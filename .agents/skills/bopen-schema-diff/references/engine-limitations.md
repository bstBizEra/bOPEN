# Known Limitations

- Static SQL analysis is conservative and cannot prove runtime data compatibility.
- Regex-based local analysis does not replace a PostgreSQL parser or live catalog inspection.
- Atlas and pg-schema-diff may support different object sets and dependency ordering.
- Prisma only compares features represented by Prisma.
- Rename intent cannot always be inferred from final schema states.
- Lock duration depends on table size, workload, PostgreSQL version, data distribution, and transaction context.
- RLS correctness requires policy semantics, role topology, application session setup, and negative tests.
- This package does not execute or benchmark production migrations.
