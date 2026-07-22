# GitHub Copilot adapter for bOPEN

Follow `AGENTS.md`. The canonical shared-skill catalog is
`docs/registers/skill-registry.json`; routing lives in
`.agents/SKILL-ROUTING.md`. Installation does not activate a skill or grant
authority. Validate discovery with
`python tools/validate_skill_registry.py --check-discovery copilot` and do not
invoke inactive candidates.
