# Detailed Operating Procedure

## Intake record

Create an intake record with:

```yaml
task: design | research | review | adr | gap-analysis | implementation-control | conformance-review
objective: ...
controlling_artifacts: []
scope:
  platform_areas: []
  products: []
  modules: []
  tenant_context: not-applicable | synthetic | authorized
constraints: {}
assumptions: []
required_outputs: []
```

## Analysis sequence

1. Normalize terminology against the glossary.
2. Map the request to the canonical execution chain.
3. Identify source-of-truth owners and trust boundaries.
4. Extract existing requirements and contradictions.
5. Research current primary sources only where needed.
6. Generate at least one credible alternative for material decisions.
7. Apply tenancy, authorization, data, operations, and supply-chain controls.
8. Define work packages and evidence.
9. Run the architecture checker and address blocking findings.
10. Issue a bounded disposition.

## Minimal diagrams

Use text diagrams where they improve precision. Every arrow should have a meaning: request, ownership, data flow, event, dependency, or authority. Label trust boundaries and asynchronous transitions.

## Assumption handling

Proceed with a documented assumption when it is reversible and low risk. Mark it as a blocking question when it could change tenant isolation, authorization, data ownership, legal responsibility, production topology, or release safety.

## Review conduct

Review the architecture, not the author's status. Findings must cite a control and observable evidence. Avoid style-only findings unless style obscures a material contract.
