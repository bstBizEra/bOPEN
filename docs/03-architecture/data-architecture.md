# Data Architecture

Each aggregate has an owner. Cross-context reads use contracts or approved read models. Tenant-owned rows require isolation enforcement. Audit and usage stores are append-oriented. Sensitive identity credentials belong to dedicated identity infrastructure.
