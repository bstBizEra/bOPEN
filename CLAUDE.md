# Claude Code adapter for bOPEN

Read `AGENTS.md` first. Discover shared skills only through
`docs/registers/skill-registry.json`, then apply `.agents/SKILL-ROUTING.md`.
An installed skill is not active or authorized. Run
`python tools/validate_skill_registry.py --check-discovery claude` before use
and stop on an inactive, drifted, unknown, or explicit-only skill that was not
named by the user.
