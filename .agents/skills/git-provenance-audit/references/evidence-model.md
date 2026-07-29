# Evidence model

Use this audit directory shape:

```text
audit-output/
  audit.json
  findings.json
  raw/
    commands.json
  audit-manifest.json
```

`audit.json` binds the baseline, observation, limitations and collector result.
`findings.json` is an array of schema-conforming independent claims. Raw files
preserve sanitized collector facts. `audit-manifest.json` hashes every package
member except itself and records a deterministic checksum root.

Each finding includes a stable ID, control, independent claim, verdict,
mandatory flag, exact evidence references, basis, limitations, non-mutating
remediation, and separate authorization status.

Do not edit raw evidence to improve a result. If redaction is necessary, retain
the redaction rule and hash the redacted artifact actually delivered.
