# Entitlement and Commercial Analysis

## Observed commercial structures

- team billing identifier and provider fields;
- subscription records;
- service and price catalog records;
- payment-management permission resource;
- Stripe integration described in upstream documentation.

## Research questions

- How is a subscription related to a team/customer?
- Does subscription state gate any team capability?
- Are plan changes versioned?
- Are quotas or seats measured?
- What happens on past due, cancellation or expiry?
- Can an admin view billing but not change product access?

## bOPEN separation

```text
Subscription = commercial agreement instance
Entitlement = right or limit granted to tenant
Feature flag = rollout/experiment control
Authorization = principal permission
Module enabled = tenant configuration
```

## Target entitlement types

- boolean;
- static value;
- seat/capacity;
- metered usage;
- time-bound grant;
- promotional/manual override.

## Initial disposition

`REJECT` direct model reuse. `ADAPT` the integration boundary and customer/subscription lifecycle as research input.
