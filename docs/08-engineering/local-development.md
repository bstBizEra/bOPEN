# Local Development

Local development uses synthetic data and non-production credentials. Research clones remain separate. Environment setup must be reproducible from scripts and documented versions.

## Initial build posture

During Phase 0, "build" means repository bootstrap execution, validation, research, requirements, architecture and contract drafting. Production platform kernel code remains blocked until the BOPEN-RES-001 G7 release gate and applicable normative artifacts are approved.

Local bGitea is used for local git collaboration, work-package branches and bootstrap review. The local bGitea service is `http://localhost:3030/`; do not store credentials in the repository. GitHub is used only for the stable version after validation, review and evidence are complete.

Before starting a work-package branch:

1. Confirm the work package and governing artifact.
2. Run `python tools/validate_repository.py`.
3. Create a short-lived branch using the Phase 0 branch pattern.
4. Keep source, evidence and traceability updates in the same change.
5. Run repository validation again before pushing to bGitea.
