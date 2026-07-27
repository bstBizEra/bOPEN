# Research and Evidence Policy

## Source hierarchy

1. approved bOPEN artifacts and repository contracts;
2. official standards, specifications, laws, and vendor documentation;
3. primary research papers and official project repositories;
4. reputable secondary analysis for context only;
5. community discussion for hypotheses, never as sole authority for a material control.

## Freshness

Use current web research when a fact can change, including specifications, software behavior, security guidance, product capability, pricing, support status, or regulation. Record the retrieval date and version. A recently uploaded copy of an old document is not fresh evidence.

## Clean-room rule

External systems may inform capability findings and tradeoffs. Do not copy their proprietary or incompatible implementation into bOPEN.

```text
UPSTREAM OBSERVATION
  -> CAPABILITY FINDING
  -> ARCHITECTURE INFERENCE
  -> bOPEN REQUIREMENT
  -> OWNED CONTRACT
  -> CLEAN IMPLEMENTATION
```

Maintain a license register for any code, schema, template, or asset considered for reuse.

## Evidence classes

- `normative`: approved requirement, contract, policy, or standard;
- `implementation`: code, schema, migration, configuration, or deployed state;
- `verification`: test result, scan, trace, or review result;
- `operational`: metrics, logs, backup/restore result, incident evidence;
- `attestation`: signature, provenance, SBOM, approval, or independent verdict;
- `informative`: research context that does not control the design.

## Citation discipline

- Cite claims that depend on a source.
- Keep facts, interpretations, and recommendations distinct.
- Avoid long verbatim copying; summarize accurately.
- Record uncertainty and conflicting sources.
- Do not invent a source, version, test result, signature, or approval.

## Evidence integrity

Evidence should include artifact/revision, environment, date/time, command or procedure, result, verifier, correlation identifier, and hash where practical. Evidence produced by the same actor that implemented the control may be useful but does not replace independent verification where separation of duties is required.
