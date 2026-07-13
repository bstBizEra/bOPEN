# Clone Bootstrap

## Windows PowerShell

```powershell
./scripts/bootstrap-boxyhq-study.ps1 `
  -WorkspaceRoot C:\laragon\www\bopen-research\ENGIN-R0-<run-id> `
  -OperatorId ENGIN-R0-<run-id>
```

## Linux (not exercised by R0)

Linux requires Bash 4+, `sha256sum`, and a separately approved absolute external root. The workflow is disabled when `BOPEN_RESEARCH_APPROVED_ROOT` is absent.

```bash
export BOPEN_RESEARCH_APPROVED_ROOT="$HOME/bopen-research"
./scripts/bootstrap-boxyhq-study.sh "$HOME/bopen-research/REV-R0-<run-id>" "REV-R0-<run-id>"
```

## Verification

The script shall:

1. clone `boxyhq/saas-starter-kit` into an isolated upstream directory;
2. fetch the pinned commit;
3. checkout detached HEAD at `abc9b686823cbfb4973c79bc36fea37a3244be6c`;
4. preserve upstream license files;
5. write a clone metadata record;
6. calculate key checksums;
7. refuse to continue when the checked-out SHA differs.

Dependency installation and runtime startup must be separately logged because external services may require test credentials.

## Baseline execution

```powershell
./scripts/run-boxyhq-baseline.ps1 `
  -Target C:\laragon\www\bopen-research\ENGIN-R0-<run-id>\01-boxyhq\upstream `
  -EvidenceRoot C:\laragon\www\bopen-research\ENGIN-R0-<run-id>\evidence `
  -OperatorId ENGIN-R0-<run-id>
```

`DEC-0009` requires physical clones and raw logs to remain outside the bOPEN Git worktree. The R0 baseline pins npm 10.9.2 because npm 11 rejects the approved upstream lockfile; this compatibility condition must be re-evaluated when the upstream pin changes.

Finalize and verify each external evidence store with `finalize-research-evidence.ps1`. The finalizer writes a normalized secret-scan receipt and a BOM-free file/hash manifest, then verifies the complete evidence file set.
