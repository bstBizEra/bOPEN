CREATE TABLE projects (
  id uuid PRIMARY KEY,
  code text NOT NULL UNIQUE,
  name text NOT NULL
);
