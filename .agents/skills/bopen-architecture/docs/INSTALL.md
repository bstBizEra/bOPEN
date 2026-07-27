# Installation

## Repository-scoped

Copy the complete directory to:

```text
<repo>/.agents/skills/bopen-architecture/
```

Keep the directory name equal to the `SKILL.md` name.

## User-scoped

Copy it to:

```text
$HOME/.agents/skills/bopen-architecture/
```

## OpenAI hosted skill bundle

A compatible hosted environment may accept the release ZIP as one skill bundle. Upload exactly one top-level `bopen-architecture/` directory containing exactly one `SKILL.md`.

## Dependencies for bundled utilities

```bash
python -m pip install -r requirements.txt
```

The skill's prose instructions remain usable without Python dependencies; the dependencies are required for deterministic schemas, validation, tests, and packaging.

## Verification

```bash
python scripts/validate_package.py
python -m unittest discover -s tests -v
python scripts/run_static_evals.py
```
