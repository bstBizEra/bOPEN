# Control Checklist

- [ ] Dependency direction is explicit and acyclic where practical.
- [ ] No product Module writes another Module's tables directly.
- [ ] Shared utilities contain no hidden domain policy.
- [ ] Provider adapters sit behind owned interfaces.
- [ ] Service extraction requires operational evidence.
