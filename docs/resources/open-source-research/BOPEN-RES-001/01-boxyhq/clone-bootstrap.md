# Clone Bootstrap

## Windows PowerShell

```powershell
./scripts/bootstrap-boxyhq-study.ps1 -WorkspaceRoot C:\laragon\www\bopen-research
```

## Linux/macOS

```bash
./scripts/bootstrap-boxyhq-study.sh "$HOME/bopen-research"
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
