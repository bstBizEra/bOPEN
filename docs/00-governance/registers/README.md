# PG-GOV-REG-001 - Program governance registers

**Document ID:** `PG-GOV-REG-001`

**Version:** `0.1.0`

**Status:** Draft

**Owner:** Engineering Authority

**Issue date:** 2026-07-21

**Governing artifacts:** `BOPEN-BOOT-001`, draft `BOPEN-GOAL-001`

**Dependent work package:** `GOV-P0-01`

These JSON registers are the draft machine-readable control surface for Program G0. Each register uses a matching draft schema under `contracts/governance/` and the shared envelope `$schema`, `register_id`, `version`, `status`, `owner_authority`, `updated_at`, and `entries`.

The registers are draft inputs only. Empty agent, module, and skill registers do not prove operational readiness. `NOT_READY` schedule entries do not pass a phase gate. No entry authorizes production implementation, approves Program Goal v0.2, certifies a module, promotes a skill, or approves a technology decision.

Run `python tools/validate_program_controls.py` for structural, reference, expiry, self-review, certification, schedule-cycle, phase-namespace, and concurrent-scope validation.
