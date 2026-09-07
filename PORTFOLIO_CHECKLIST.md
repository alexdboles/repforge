# RepForge public portfolio preparation checklist

**Preparation only.** No repository creation, push, publication, deployment change,
contest-entry change, user-data deletion or Git-history rewrite is authorised/performed.
“Complete” below means the preparation deliverable exists and was checked—not that
publication is safe without the owner's final decisions.

## A. Portfolio README and screenshots — COMPLETE (preparation checked)

- [x] RepForge README replaces outdated skeleton claims and identifies Emergent's role.
- [x] Local setup/configuration/check commands distinguish executed checks from clean-install limitations.
- [x] Actual landing, simulation and coaching screenshots exist in `docs/images/`, contain fictional/demo data and are visually reviewed.
- [x] Live link is `https://www.therepforge.app/`; preview validation and production-version difference are explicit.

## B. Short demonstration guide — COMPLETE (preparation checked)

- [x] `docs/DEMO_GUIDE.md` describes the actual demo → coaching → targeted retry path.
- [x] Roughly two-minute narration, honest timing caveat and exact manual recording/privacy steps are included.
- [x] No video or screenshot has been fabricated.

## C. Architecture and verification — COMPLETE (preparation checked)

- [x] `docs/ARCHITECTURE.md` describes implemented auth/workspaces, lifecycle, grading, AI/voice and data boundaries with Mermaid.
- [x] `docs/VALIDATION.md` records actual results, failures/rechecks and manual limitations without claiming a complete legacy suite pass.
- [x] Transcript evidence, recoverable failures and bounded—not exact-dollar—provider budgets are explained.

## D. Public-release hygiene and honest status — COMPLETE (preparation checked; manual publication review remains)

- [x] `.gitignore` and safe backend/frontend `.env.example` files checked; existing private configuration retained.
- [x] Proposed public files and available local Git refs/reflogs scanned read-only; filename/issue-type findings recorded without secret values.
- [x] `docs/PROJECT_STATUS.md` separates implemented/verified scope, limitations, estimates and future work.
- [x] Existing tracked internal files/history risks and licence/ownership decisions are explicitly flagged; no automatic deletion or rewrite.

Artifact verification: `python scripts/check_portfolio_docs.py` passed all 12 required
file/image checks and local links. Three 1280×720 JPEGs passed integrity checks, had no
EXIF metadata and were visually reviewed for visible secrets/private information.
Small-text readability and viewport cropping are noted in the image provenance;
captions retain fictional-demo context. This is content review, not a security certification.

Final read-only scan: 167 working files, 13 available commits / 242 historical blobs,
zero configured-secret or provider-key/JWT-shaped matches. Two test-source filenames
were flagged for fixture-password review; tracked internal artifacts remain a manual
publication decision. See [audit details](docs/PUBLIC_RELEASE_AUDIT.md).

## Owner's manual pre-publication checklist

- [ ] Inspect screenshots, narration and the exact files/history selected for release; exclude private runtime data, reports, backups and platform artifacts.
- [ ] Resolve already tracked internal material in a separately reviewed public-export/history workflow. `.gitignore` does not erase prior commits.
- [ ] Run independent secret/history scanning. If a real secret is found, rotate/revoke it first, then clean all relevant history with explicit approval.
- [ ] Decide the project licence and confirm ownership, dependency/font redistribution and provider/voice rights. No licence was guessed here.
- [ ] Verify the intended production version separately; this pass did not deploy preview changes.
- [ ] Make and listen to the actual demo recording, if wanted; complete manual audio/accessibility/privacy checks.
- [ ] Verify a clean install and re-run the documented checks on the final export. Only then explicitly authorize publication from Emergent.