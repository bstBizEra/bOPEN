# Pre-publication credential scan — every blob reachable from `HEAD`, 2026-08-10

**Status:** **SCAN RESULT — advisory.** Not an authorization to publish. Merge, release and any
outward publication remain outside agent authority (`AGENTS.md` §20.3).
**Ran at:** `561333a`, branch `claude/BOPEN-P35-001-runtime-realization`
**Tool:** [`tools/scan_history_for_credentials.py`](../../tools/scan_history_for_credentials.py) — read-only, reproducible
**Run by:** Claude (agent, Motor role). **Not independently verified.**

---

## 1. Why this exists

`https://github.com/bstBizEra/bOPEN` and this working tree are **two disjoint histories**:

```text
git merge-base 9a80f9d HEAD          ->  (empty)
commits of HEAD already on GitHub    ->  0
commits of HEAD never on GitHub      ->  342
```

Nothing from this lineage has ever left the machine. **A first push publishes 342 commits at once**,
and publication is not reliably reversible — content can be cached or indexed after deletion. So the
history was scanned before, not after, the question of whether to push is decided.

## 2. Coverage

```text
objects reachable from HEAD  : 3,266
blobs                        : 1,267
total blob bytes             : 28,821,466
blobs scanned                : 1,267
blobs skipped (binary/large) : 0
```

**Every blob was read.** The tool prints these counts and aborts on zero blobs, because a first
attempt at this scan reported "0 blobs" from a broken reader — `git rev-list --objects` emits
`<sha> <path>` and the consumer took the whole line as an object name. A clean result from a broken
scanner looks exactly like a clean result.

## 3. Result — no live credential found

Ten credential **shapes** were searched, not keywords, so that a repository which discusses secrets
in prose does not bury real findings. **Eight matched nothing at all:**

| Pattern | Matches |
| :--- | ---: |
| `aws_access_key_id` (`AKIA…`/`ASIA…`) | **0** |
| `github_token` (`ghp_`, `github_pat_`, …) | **0** |
| `slack_token` (`xox…`) | **0** |
| `google_api_key` (`AIza…`) | **0** |
| `openai_key` (`sk-…`) | **0** |
| `stripe_key` (`sk_live_`, `rk_live_`) | **0** |
| `jwt_like` (`eyJ….eyJ….…`) | **0** |
| `assigned_secret` (`password=`/`api_key=` with a non-placeholder value) | **0** |
| `private_key_block` | 3 — **all placeholder**, §4 |
| `url_with_password` | 122 — **all placeholder but one**, §5 |

## 4. `private_key_block` — a commented placeholder

All three occurrences are the same line in successive versions of `.env.example`, and it is
**commented out with an elided body**:

```text
# BOPEN_CONTEXT_TOKEN_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

The surrounding comment is the opposite of a leak — it names the value as *"the highest-value secret
in the system"*, points at `tools/generate_token_key.py` for development, and requires an external
secret manager in production (`BOPEN-IDP-001` §12.4).

## 5. `url_with_password` — 122 matches, 121 of them placeholders

`CHANGE_ME`, `<password>`, `<pw>`, `{password}`, `{DEFAULT_ROLE}` across `.env.example`, `db.py`,
`db_bootstrap.py`, `provision_dedicated_db.py` and the isolation tests. One ballot record contains
`http://user:pass@127.0.0.1:8765`, which is a **probe vector**, not a credential.

**One is a literal pair, and it is reported rather than waved through:**

```text
.env.example:27   DATABASE_URL=postgresql://bopen:bopen@localhost:5432/bopen_dev
```

Assessment: **low risk, and worth fixing anyway.** It is a weak local development default in an
example file, on `localhost`, and the file's own comment says *"Retained for compatibility with
pre-P35 examples. Prefer `BOPEN_DATABASE_URL` above; nothing in the kernel reads `DATABASE_URL`."*
It is still a credential pair a reader could copy into a real environment, and `CHANGE_ME` is the
convention used by every other entry in the same file.

## 6. `.env` itself was never committed

```text
.gitignore:13:.env
files matching .env* ever added in history:  .env.example
```

Only the example file has ever entered the history. No real environment file exists in any commit.

## 7. What this scan does NOT establish

Named because a security result that overstates itself is worse than none:

1. **It is pattern-based.** A credential in a shape not listed in §3 — a bare high-entropy string, a
   base64 blob, an internal token format — would not be found. This is not entropy analysis.
2. **It covers `HEAD` only.** Objects reachable from other local branches, from the **six other
   worktrees** (`git worktree list`, one of them marked `prunable`), or from dangling reflog entries
   were **not** scanned. If a different branch is ever published, it must be scanned separately.
3. **It says nothing about what publication would disclose beyond credentials.** The history contains
   six artifacts awaiting disposition and one **open, reproducible security defect** —
   `P35-04R-15`, where `/v1/../admin` reaches the kernel as `/admin` because the `/v1` prefix does
   not confine the proxy, still live at `ebb4dcc` and awaiting `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`.
   Publishing a working probe for an unfixed defect is a disclosure decision, and it is the
   operator's, not a scanner's.
4. **It was run by the maker of most of this history and has not been independently verified.** EBIV
   §8: a maker's own passing check carries no verdict weight.

## 8. Recommended before any first push

1. Change `.env.example:27` to `CHANGE_ME`, matching every other entry in the file.
2. Decide `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`, or decide deliberately to publish with the defect
   open and recorded.
3. Have an independent agent re-run `tools/scan_history_for_credentials.py` and confirm §2's counts.
4. Choose the repository lineage — the two histories share no ancestor, so pushing is not a
   fast-forward of anything and the choice among branch / replace `main` / separate repository is a
   decision about what `bstBizEra/bOPEN` *is*.

Recorded advisory-only. Confers no publication, merge, release or production authority.
