# Control Checklist

- [ ] Trusted server logic establishes context.
- [ ] Database context is transaction-local and safely cleared.
- [ ] Consumers revalidate because events are not authority tokens.
- [ ] Support access requires an explicit expiring grant and reason.
- [ ] Negative tests cover APIs jobs caches and events.
