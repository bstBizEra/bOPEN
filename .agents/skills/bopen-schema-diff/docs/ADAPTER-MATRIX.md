# Adapter Matrix

| Adapter | P0 status | Authority | Strength | Limitation |
|---|---|---|---|---|
| Static SQL analyzer | Included | Advisory | Fast bOPEN rules | Conservative regex analysis |
| Atlas | Optional primary | Deterministic plan | Broad schema workflow | Version/feature/licensing differences |
| Stripe pg-schema-diff | Optional second opinion | Deterministic plan | PostgreSQL-focused downtime awareness | CLI and object coverage may change |
| Prisma migrate diff | Optional source adapter | ORM-supported plan | Prisma integration | Unsupported PostgreSQL features invisible |
| Alembic | Deferred | ORM candidate | SQLAlchemy integration | Autogenerate requires review |
| Liquibase | Deferred | Cross-database candidate | Broad database support | Not needed for PostgreSQL P0 |
