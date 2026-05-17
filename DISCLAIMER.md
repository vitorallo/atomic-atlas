# Disclaimer & Acceptable Use

atomic-atlas is an **offensive security testing tool**. It executes adversarial
attacks (prompt injection, jailbreaks, credential extraction, RAG/tool/MCP
poisoning, agent-to-agent attacks) against AI agents. It is **dual-use**: built
for defenders, equally capable of harm if misused.

## Authorized use only

Use atomic-atlas **only** against systems you own or for which you hold
explicit, written authorization to test. Running these atomics against systems
you are not authorized to test is unethical and, in most jurisdictions,
illegal (e.g. computer-misuse / unauthorized-access statutes).

Intended use: authorized red-team engagements, security research, defensive
coverage verification, education, and CTF/lab environments.

The runner enforces an explicit `--authorized` flag on every `exec` invocation.
That flag is **your attestation that you have authorization** — it is not a
grant of permission and does not make unauthorized testing lawful.

## No responsibility for misuse

The software is provided "as is", without warranty of any kind, as stated in
[`LICENSE`](LICENSE) (MIT). To the maximum extent permitted by law, the authors
and contributors:

- accept **no responsibility or liability** for any use or misuse of this
  software, or for any damage, loss, or legal consequence arising from it; and
- make **no warranty** that use of this software is lawful in your jurisdiction
  or against any particular target.

**You** — the operator — are solely responsible for obtaining authorization,
for complying with all applicable laws and contracts, and for any consequences
of running this software.

## Catalog content

Atomic test definitions describe attack *techniques and shapes* for the purpose
of testing and hardening AI systems. They are published for defensive and
research value. Contributors must not submit live credentials, real target
data, or material whose distribution is itself unlawful.

By using atomic-atlas you acknowledge and accept the above.
