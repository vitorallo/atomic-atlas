"""Human-in-the-loop (HITL) wrapper for atomic-atlas targets.

When `--hitl` is set on `atomic-atlas exec` or `atomic-atlas runbook exec`,
every outbound `send_prompt_async` call is gated. The operator sees the
target description, the interaction vector, and the message body about to
be sent, and confirms `y` (forward) / `s` (show full body) / `n` (skip
this turn — counted as a failure) / `a` (abort the run).

The wrapper sits at the target level so it works equally for
`PromptSendingAttack` (one outbound per run) and `RedTeamingAttack`
(many outbound across mutated turns). Every actual outbound message
stops at the gate.
"""

from __future__ import annotations

from typing import Any

from .targets.base import AtomicAtlasTarget


class HITLAbortError(BaseException):
    """Raised when the operator chooses to abort a run from the HITL prompt.

    The runner catches this and returns a partial RunResult; the runbook
    runner catches it and marks remaining steps as skipped. cleanup() still
    runs in both cases.

    Inherits from BaseException so PyRIT's internal ``except Exception``
    blocks don't swallow the abort and re-prompt the operator on retry.
    """


_TRUNCATE = 400  # default body truncation for the HITL preview


def _format_body(text: str, full: bool = False) -> str:
    if full or len(text) <= _TRUNCATE:
        return text
    return text[:_TRUNCATE] + f"\n... (truncated; {len(text) - _TRUNCATE} more chars)"


class HITLTargetWrapper(AtomicAtlasTarget):
    """Wraps any AtomicAtlasTarget; gates send_prompt_async on operator confirmation.

    The wrapper inherits AtomicAtlasTarget for type compatibility but does
    NOT inherit the inner target's PyRIT plumbing — it forwards setup(),
    cleanup(), and send_prompt_async() to the inner target. The HITL gate
    sits inside send_prompt_async.
    """

    def __init__(self, inner: AtomicAtlasTarget, *, click_module=None) -> None:
        # Don't call AtomicAtlasTarget.__init__ — we don't need a fresh
        # PromptTarget; we delegate to the inner target's PyRIT identity.
        # We do hold the same atomic + profile refs so type checks pass.
        self.atomic = inner.atomic
        self.profile = inner.profile
        self._adapter_config = inner._adapter_config
        self._inner = inner
        # click is the prompt UI; injected for testability.
        if click_module is None:
            import click as _click
            click_module = _click
        self._click = click_module

    async def setup(self) -> None:
        return await self._inner.setup()

    async def cleanup(self) -> None:
        return await self._inner.cleanup()

    # PyRIT introspects targets via get_identifier; forward to the inner.
    def get_identifier(self):  # pragma: no cover — passthrough
        return self._inner.get_identifier()

    async def send_prompt_async(self, *, message):
        request_piece = message.message_pieces[0]
        body = request_piece.converted_value or request_piece.original_value or ""

        target_label = type(self._inner).__name__
        vector = self._adapter_config.get("type") or self.atomic.interaction_vector

        click = self._click
        click.echo("")
        click.echo("=" * 70)
        click.echo(f"HITL gate: about to send via {target_label} ({self.atomic.interaction_vector})")
        click.echo(f"Target adapter mode: {vector}")
        click.echo(f"Atomic: {self.atomic.atlas_technique} / {self.atomic.interaction_vector}")
        click.echo("-" * 70)
        click.echo("Message body:")
        click.echo(_format_body(str(body), full=False))
        click.echo("=" * 70)

        while True:
            choice = click.prompt(
                "Send? [y]es  [s]how full body  [n]o (skip this send)  [a]bort run",
                default="n",
                show_default=True,
            ).strip().lower()
            if choice in ("y", "yes"):
                return await self._inner.send_prompt_async(message=message)
            if choice in ("s", "show"):
                click.echo("")
                click.echo(_format_body(str(body), full=True))
                click.echo("")
                continue
            if choice in ("n", "no"):
                # Synthesize a non-success response so the orchestrator records
                # this turn as a skip / failure without crashing.
                from pyrit.models import construct_response_from_request
                return [construct_response_from_request(
                    request=request_piece,
                    response_text_pieces=["[HITL skip — operator declined this send]"],
                    error="processing",
                )]
            if choice in ("a", "abort", "q", "quit"):
                raise HITLAbortError("Operator aborted the run from the HITL gate.")
            click.echo(f"Unrecognized response: {choice!r}. Try y / s / n / a.")
