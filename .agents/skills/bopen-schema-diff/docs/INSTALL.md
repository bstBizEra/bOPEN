# Installation

## Repository scope

Copy the package into the agent skill directory supported by the target runtime. For Codex, current official documentation supports repository and user skill locations; follow the installed runtime version's documented path.

```text
<repository>/.agents/skills/bopen-schema-diff/
```

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Optional deterministic engines must be installed separately and pinned by the repository toolchain. Verify:

```bash
atlas version
pg-schema-diff --version
```

Do not place database credentials in this directory.
