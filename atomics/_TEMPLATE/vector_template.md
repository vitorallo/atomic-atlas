---
atlas_technique: AML.T0000          # Replace with actual ATLAS technique ID
display_name: Technique Name        # Human-readable name from ATLAS
interaction_vector: direct_chat     # Replace with the target vector (see SPEC.md for enum)
guid: 00000000-0000-4000-8000-000000000000  # Generate a fresh UUID4: python3 -c "import uuid; print(uuid.uuid4())"
runs: 5
target_requires:
  - capability: direct_chat         # List capabilities the target must expose
---

# [Technique Name] via [Vector Name]

## Why this matters
One or two sentences. Write for a CISO who has 30 seconds. What is the real-world impact if this attack succeeds?

## Prerequisites
- What the attacker needs (access level, position, capabilities)
- What the target must expose (tool, RAG, MCP server, etc.)

## Attack strategy
Describe the attack concept. Reference the PyRIT orchestrator (PromptSendingOrchestrator or RedTeamingOrchestrator). Reference the payload seed file if one exists.

Payload seed: `payloads/your_payload_file.md` (or `.json`)

## Interaction
1. Setup step (if any)
2. User → agent: "Trigger message here."
3. Observe: what to watch for

## Success criteria
Plain prose: what does a successful test look like? This text is used by the LLM judge. Be concrete — name the tool call, the data, or the behavior that indicates success.

## ATLAS mitigations
- MXXX: Mitigation name
- MXXX: Mitigation name

## Cleanup
- Remove any state created in setup
- Stop any mock servers or listeners
