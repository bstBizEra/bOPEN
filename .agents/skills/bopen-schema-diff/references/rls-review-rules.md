# RLS Review Rules

Block or independently review:

- `DISABLE ROW LEVEL SECURITY`;
- `NO FORCE ROW LEVEL SECURITY` on protected tables;
- policy removal without replacement;
- broadening tenant predicates;
- missing `WITH CHECK` on mutating policies;
- policies using client-supplied tenant identifiers without server validation;
- roles with `BYPASSRLS`;
- ownership changes that alter RLS behavior;
- SECURITY DEFINER functions with unsafe `search_path`;
- views that bypass expected invoker permissions;
- grants to `PUBLIC` or broad application roles.

RLS is defense in depth and does not replace application authorization or validated tenant context.
