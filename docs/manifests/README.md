# Versioned Document Manifest Snapshots

**Version:** 0.1
**Status:** Draft operational convention pending DEC-0012
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-02 (Proposed; not accepted)

This directory preserves candidate document manifests without replacing the canonical generated `docs/DOCUMENT-MANIFEST.json`. A snapshot excludes the canonical manifest and its own output path. It is technical evidence only and does not approve documents or resolve DEC-0012.

Reason: literal append-only instructions conflict with deterministic replacement of the canonical generated manifest. Benefit of the old phase: the canonical manifest remains unchanged and its Git history is preserved. Expected outcome: DEC-0012 selects an approved long-term convention.
