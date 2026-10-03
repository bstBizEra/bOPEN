# Engine Adapters

## Atlas

Use as the primary deterministic planner. Supply explicit `--from` and `--to` sources. The wrapper captures SQL only and never calls `atlas schema apply` or `atlas migrate apply`.

## Stripe pg-schema-diff

Use as an independent PostgreSQL plan. Pin an approved release. The wrapper rejects unknown executable names and records tool version. Treat output disagreement as review-required.

## Prisma

Use only for Prisma-supported objects. Prisma may not represent PostgreSQL features such as all views, policies, triggers, grants, and extensions. Always perform native PostgreSQL review for bOPEN security controls.

## Missing tool

If a required engine is unavailable, report `UNKNOWN` or `REVIEW_REQUIRED`; never fabricate output.
