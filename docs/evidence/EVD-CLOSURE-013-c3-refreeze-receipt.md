# EVD-CLOSURE-013 - Durable checker receipt: C3 closure-manifest re-freeze (permitted_effects correction)

**Version:** 0.1
**Status:** Durable independent-review receipt (maker-persisted verbatim per issued PG-P0-INTERP-002 section 7).
**Class:** Independent BST-Codex-Motor exact-SHA verification (independent of the maker).
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker; did not author the receipt content).
**Runtime pointer (non-anchor):** review task b931vyas0.

## Checker receipt (verbatim)

```yaml
subject_commit: 27e70fa82e5ae5573658dbb0ca10f622fe232f56
subject_tree: 7dd29f0ee93f3e3c5960be272814557a60ffba3e
parent: b84f22d05f6029327b316b8a76f7a9efc61ea132
manifest_sha256_old: 9e67cd0b76817f1ca84c2badfb1236676beaa42aa64e9d5dbdbf117929518677
manifest_sha256_new: 7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a
mandate_payload_sha256: 0f34a306ad63bb3457c1fdda3d3c9185bd99636314dc3008f2dc6ebc9acaf92c
predecessor_sha256: e80f7b9390d86a7627d6d14bd683296f2314189d145791971fb8aeb2a8d9f1cf
successor_sha256: 1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863
pae_sha256: bd5113a6edf87e03d8a80d60da41f430afbe8c7fe0e6a1e59c8352c221863d41
checker_id: BST-Codex-Motor
checker_role: independent_checker
checker_independent: true
maker: Claude Opus 4.8
checker_authored_commits: 0
tools: Python 3.13; tools/verify_phase_transition.py; Git
commands: VERIFY-P0-01 round-trip; full validation chain; both manifest checks; unittest discovery
test_result: PASS; 189 tests; OK
test_digest: 21c5ac335fae96750e345701edae021a8291db94d55cc888f24646c30be88ac8
verdict: ACCEPT_EXACT_SHA
timestamp: 2026-07-27T09:07:08+07:00
operator_signature: not performed; checker evidence only
```

## Findings (summarized)

Verdict **ACCEPT_EXACT_SHA**. The re-freeze added `tests/governance/test_program_control_validation.py`
to the closure manifest's `permitted_effects` (correcting the omission found by EVD-CLOSURE-012). The
**four signing digests are unchanged** (mandate `0f34a306`, predecessor `e80f7b93`, successor `1f8d183e`,
PAE `bd5113a6`) and `mandate_payload_b64` is byte-identical to its value at `b84f22d0` -> **the operator's
C4 signature subject and signing command (PAE `bd5113a6`) are unaffected.** Only the manifest's own
sha256 changed, `9e67cd0b -> 7417cc6a`; the real C6 mandate record must name `7417cc6a` per INTERP-002
v0.4 §5. Round-trip through VERIFY-P0-01 = VERIFIED / VERIFIED_EXACT. Both document-manifest checks +
full validation chain + 189/189 tests PASS; strict UTF-8 (0x97=0, CRLF=0); protected diff zero;
SCHEDULE-REGISTER byte-identical; state still PG-P0 ACTIVE / PG-P1 NOT_READY / no signature. No finding.

## Status effect

None. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized. The closure subject the operator
signs at C4 is unchanged.
