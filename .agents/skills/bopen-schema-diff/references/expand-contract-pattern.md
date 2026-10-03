# Expand-and-Contract Pattern

1. Add compatible schema elements.
2. Deploy application code capable of reading old and new representations.
3. Backfill deterministically and verify counts/hashes.
4. Switch writes to the new representation.
5. Observe and verify.
6. Remove old schema only in a later, separately approved change.

A direct rename, type replacement, or drop may be acceptable only when coordinated downtime or complete consumer compatibility is proven.
