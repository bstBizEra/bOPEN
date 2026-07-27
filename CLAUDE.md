# CLAUDE.md — bOPEN Claude Code Adapter

Read and obey the repository root `AGENTS.md` as the canonical operating policy.

## Claude-specific operating profile

1. Use Claude primarily for architecture, requirements, threat modeling, design review,
   cross-file reasoning, independent checking and evidence assessment.
2. Before implementation, restate the controlling requirement, architecture decision,
   allowed paths, test obligations and stop conditions.
3. Keep this file concise. Use `.claude/rules/` for scoped rules and
   `.claude/agents/` for specialist subagents.
4. Treat instructions as context, not an enforcement mechanism. High-risk command
   blocking must be implemented through approved hooks or external policy controls.
5. Do not use auto-memory as a source of normative truth. Promote verified learning into
   version-controlled governance, ADRs, runbooks or approved skills.
6. Do not self-approve changes made in the same session.
7. Produce a structured handoff using `docs/02-agents/HANDOFF-CONTRACT.md`.
8. Discover shared procedures from `.agents/skills/` and verify their entries in
   `docs/registers/skill-registry.json`; do not maintain a divergent Claude-only copy.
