# BOPEN-PARTY-001 — bOPEN Party, Person, Organization, Legal Entity & Business Relationship Model v1.0

**Document ID:** `BOPEN-PARTY-001`  
**Version:** `1.0`  
**Status:** Draft — no implementation authority  
**Issued:** 2026-07-12  
**Owner:** Data Authority  
**Classification:** Internal engineering governance  

## Principle

A `User` can authenticate. A `Party` participates in a business relationship. A party can exist without a user account and may later link to one.

## Candidate model

```text
Party
├── Person
└── Organization
    └── Legal Entity metadata where applicable

Party Role
├── Customer
├── Supplier
├── Employee
├── Contractor
├── Farmer
├── Driver
├── Property Owner
├── Insured / Claimant
├── Investor
└── Government / Partner
```

Party roles are contextual and time-bound. They do not grant platform authorization automatically.
