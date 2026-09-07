# Public-release hygiene review

**Read-only review, 2026-09-07 UTC. No files were published, staged for public release,
deleted from user storage or removed from Git history. No credentials were printed.**

## Scope and result

`python scripts/public_release_audit.py` scanned proposed public working files plus
unique blobs reachable from the **13 commits** available through local refs/reflogs.
The initial scan covered **156 working files and 242 unique historical blobs**; the
final scan covered **167 working files**, with the same 13 commits / 242 historical blobs.

The scan found **zero exact copies of the configured private secrets** and **zero
provider-key/JWT/private-key/credential-URL-shaped matches** in that scope. This is not
a guarantee of secret-free history: heuristic detection can miss secrets, synthetic
fixtures may look sensitive, and remote/unreachable history was not fetched.
Email/password-literal heuristics additionally flag content for human review; no matched
values are printed. Git author names/emails must be reviewed privately by the owner.

## Filename / issue-type findings

| Files | Issue type and action |
| --- | --- |
| `.emergent/cron/*`, `.emergent/emergent.yml`, `.emergent/system_deps.txt`, `.emergent/scripts/browser_check_timings.jsonl`, `.emergent/markers/*` | Already tracked internal platform/automation artifacts. Do not automatically include in a public portfolio export; preserve the working platform files privately. |
| `test_reports/iteration_1.json` through `iteration_9.json` | Already tracked internal test reports. May contain account IDs, fixture identities, responses and transcript excerpts. Exclude from the public artifact set and review available history; publish the sanitised `docs/VALIDATION.md` instead. |
| `memory/SPEC.md`, `memory/SECURITY.md` | Already tracked internal engineering context. Historical statements may be stale and include operational details. Public architecture/status documents are the reviewed replacement. |
| `backend/tests/conftest.py`, `backend/tests/test_hardening_security.py` | Final content heuristics flagged password literals used by synthetic test accounts (three scope-level findings across working tree/history). Values are intentionally not reproduced here. Review fixtures and ensure they cannot access real user data. No non-fixture email-address match was found by the added heuristic. |
| `backend/.env`, `frontend/.env`, `memory/test_credentials.md` | Private runtime configuration/credentials. Ignore-rule checks passed; keep configured files private. |
| `checkpoints/`, including code bundles and BSON database backups | Sensitive recoverable checkpoints created for this work. Ignored and never selected for publication. Do not upload, publish or automatically delete them. |
| `frontend/dist/`, `node_modules/`, browser output, caches and new raw test reports | Unnecessary generated/private artifacts; excluded by ignore rules. Actual reviewed screenshots under `docs/images/` are the intentional exception. |

**Already tracked files remain tracked.** `.gitignore` protects future additions but
does not remove an index entry, earlier commit or an already published copy. This pass
did not run index removal, history rewriting, repository creation or push operations.

## Proposed public file set

- `README.md`, `PORTFOLIO_CHECKLIST.md`, `.gitignore`.
- Reviewed `docs/` and the three labelled fictional-demo screenshots.
- Application source in `backend/` and `frontend/`, manifests/lockfiles, and safe
  `.env.example` files—**not** actual `.env`, caches or build outputs.
- Reviewed source tests and helper scripts. Keep private browser fixtures, logs and
  automation-session material out; legacy live-provider tests must be clearly labelled.
- Do not blindly publish every currently tracked file or the full working directory.

## Required if any real secret is discovered before publication

1. Stop publication. Identify the affected provider/account privately; do not paste the
   secret into an issue, chat, screenshot or audit report.
2. Rotate/revoke the credential and update private runtime configuration. For exposed
   session tokens, revoke the affected sessions; a signing-key exposure requires broader
   session invalidation. Do not claim `.gitignore` fixed the leak.
3. With explicit owner approval and a recoverable backup, remove the secret from every
   relevant commit/ref/artifact using a separately reviewed cleanup workflow. Consider
   existing clones, caches, release assets and remotes if previously published.
4. Re-scan the exact intended public history/export before authorizing publication.

No configured-secret match was found in this local scan, so no automatic key rotation
or history rewrite was performed. Provider-side rotation decisions remain with the owner.

## Remaining publication decisions

- Owner approval of a clean export versus a separately cleaned history; existing
  deployment/submission and private backups must remain intact.
- Project licensing/ownership and dependency/font redistribution/provider voice rights.
  No arbitrary project licence was added and no ownership details were invented.
- Independent final secret/PII review and clean installation outside Emergent.
- Verification of the desired live-domain version and any manual audio/demo recording.