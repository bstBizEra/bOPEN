# Supply-chain records

- `sbom.spdx.json`: initial SPDX package/dependency SBOM.
- `provenance.intoto.jsonl`: unsigned in-toto/SLSA-shaped candidate build statement.
- `release-manifest.json`: candidate file inventory and source-tree digest.
- `SHA256SUMS`: closed-world package checksums.

Candidate admission refreshes these records before registry digest binding. The
package validator rejects version, inventory, tree-digest and provenance drift.
They support review but are not proof of authenticity until produced and signed
by an approved build identity.
