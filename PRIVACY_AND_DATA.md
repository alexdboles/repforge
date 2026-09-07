# RepForge — privacy, transparency and data controls

## Scope and product status
This is an implementation inventory, not a legal-compliance certification. Privacy,
Terms and Data pages are public (`/privacy`, `/terms`, `/data`), linked from the
landing/footer and Profile. Existing design, AI model selection, managed Google
authentication and the microphone/playback lifecycle are preserved. Google’s live
managed handoff remains blocked by the previously confirmed upstream issue; no
claim of verified live Google login is made. There is no checkout, subscription,
paid plan, billing portal or advertising-cookie integration in this tree.

## Data flow and ownership
1. Browser speech recognition receives microphone audio. Depending on the browser,
   its speech service can process audio remotely. RepForge receives transcript text;
   it does not upload or persist microphone recordings.
2. FastAPI sends conversation text, scenario/product context and relevant prior
   conversation memory to OpenAI if `OPENAI_API_KEY` is configured; otherwise to
   Anthropic through the Emergent integration. Keys stay server-side. No new
   providers, models or integrations were added for this feature.
3. ElevenLabs receives AI prospect text to synthesise speech. Replies may repeat
   user-provided facts. Generated prospect audio is cached in Mongo for one day
   (TTL cleanup is asynchronous), not saved as a user microphone recording.
4. Google/Emergent provide identity details for optional sign-in. RepForge stores
   identity bindings and temporary nonce-bound proof/recovery records, not Gmail,
   Drive or Calendar content. Provider session tokens are not saved.
5. Authenticated users own their training records. Verified workspace managers see
   performance/assignments. Platform owners see minimal pseudonymous usage events.
   Authorised infrastructure operators can access stored data; no E2E encryption,
   independent security audit, measured ROI or compliance certification is claimed.

## Active-database inventory
| Collection | Contents / export / erasure |
|---|---|
| users | Profile, email where present, password hash, progress, auth epoch. Export strips secrets; erasure hard-deletes the record, invalidating cookie and bearer sessions |
| simulations | Transcript, frozen transcript, evaluation, coaching, scenario/product snapshots, prior memory, retries, score and XP. Included in JSON and hard-deleted |
| sales_profiles, custom_scenarios | User-authored business details and generated scenarios; included and removed by owner |
| assignments | Own assigned practice included/deleted; another user's assignment remains with deleted assigner ID replaced by `Deleted account` |
| memberships, workspaces | Own memberships/owned metadata exported. Own memberships deleted. Empty owned workspace deleted; shared workspace preserved without the departing owner's ID. Other members are never deleted or promoted |
| evidence_events | SHA-256 actor ID, simulation ID, event/date and coarse context; included and removed for this actor/session |
| feedback | Optional scorecard rating keyed by simulation ID; included and removed with that simulation |
| oauth_identities, oauth_recoveries, oauth_flows, oauth_codes | Own identity/recovery/flow metadata included without credentials/proofs. Linked flow/code records and bindings are removed on account erasure |
| invitations | Invitations addressed to the user exported with other actors removed. Invites created by/addressed to/accepted by a deleted account removed |
| audio_cache | Binary generated speech, not in JSON. New entries record owner ID; deletion also reconstructs legacy cache hashes from owned saved prospect turns and microphone-check sample text |
| rate_limits, leases | Operational counters and temporary request locks; not exported. User-keyed counters removed on account erasure; generic IP/provider budgets expire normally |
| provider_checks | Shared voice-availability metadata, no personal conversation; not exported/deleted |

No account list or workspace roster is exported. Secrets, password hashes, OAuth
proofs, replay keys, internal operation markers and session tokens are excluded
recursively. Export is JSON data, not a database backup or binary audio download.
It includes all matched own rows, without the history UI's pagination limit.

## API contracts (all on api_router under `/api`)
| Method / path | Result |
|---|---|
| GET `/data/summary` | Current user's record counts, guest flag, retention disclosure |
| GET `/data/export` | `DataExport`: schema_version, exported_at (UTC), user_id, data, exclusions. Attachment header + `Cache-Control: no-store` |
| DELETE `/data/sessions/{id}?confirm=DELETE` | Own call and recursively linked full retries/moment drills deleted. Foreign or missing IDs return 404 |
| DELETE `/data/account?confirm=DELETE` | Registered caller’s active-database records permanently deleted; cookie cleared |
| DELETE `/data/guest?confirm=DELETE` | Only the authenticated current guest erased; cookie cleared. Registered account gets 403 |

Confirmation is required in the UI and server; missing/wrong confirmation gets 422.
No target user ID/email accepted for account export/deletion. Existing origin guard
protects cookie-authenticated changes. Pending/error controls prevent accidental
double submits; a failure is never displayed as successful erasure. UI uses the
typed API helpers and TanStack Query. No provider call is needed for export/deletion.

Session erasure also clears the owner's AI speech cache, feedback, usage events,
assignment completion references and derived earlier-call memory. Remaining calls
stay available. Deleted XP is subtracted; badges recalculate from remaining calls,
and streak/date reset. Account erasure does not delete the user's Google account.

## Concurrency and failure semantics
Normal authenticated API requests register a bounded activity marker on the user
document; concurrent voice/text requests still coexist. Erasure obtains an atomic
exclusive account gate only if no request is active, otherwise returns a retryable
409. A stale activity marker expires logically after five minutes. Reward recovery,
account login completion and assignment writes also participate. New requests do
not write into an account under erasure. Google email/flow locks protect linking.
Operation cleanup never upserts a deleted user.

Standalone Mongo here does not provide a multi-collection transaction. Dependants
are deleted before the user. On an ordinary failure the exclusive flag is released
and the caller can retry; the server does not report success for partial erasure.
An abrupt process crash can leave `users.privacy_lock` requiring authorised operator
recovery: first confirm no erasure worker is alive, remove only that stale lock, then
rerun the same authorised erasure. Do not advertise fault-proof atomic deletion.

## Browser cleanup
On server-confirmed account/guest erasure the browser removes RepForge/VocalPitch
localStorage/sessionStorage keys, clears the query cache, signals other tabs and
hard-navigates to a deletion receipt on the landing page. It does not wipe unrelated
site storage. Other devices' stored tokens are invalid because their user no longer
exists. Signing out alone does not delete any practice data. If a guest loses its
session, an ID alone is not sufficient to export/delete it through the public API.

## Retention and maintenance
- Profile/training records, including guests: until explicit deletion. No automatic
  guest purge is scheduled; do not imply closing a tab deletes a guest.
- Google flows 10 minutes, codes one day, recoveries three days; invitations two
  days; generated speech one day. TTL cleanup can lag expiry.
- Legacy unowned audio not reconstructible from saved turns (e.g. fixed admin QA
  samples) remains subject to its original one-day TTL; no other user's cache is
  bulk-deleted as a shortcut. Such fixed samples contain no customer speech.
- `backend/scripts/cleanup_privacy_data.py --guest-id UUID` is a private dry-run.
  After independently verifying authorisation, append `--confirm DELETE` to use
  the same hard-deletion service. It refuses registered accounts and has no bulk
  guest wipe. `--expired-temporary` previews already-expired temporary rows; the
  same explicit confirmation executes removal. Neither mode was run on real users.
- Platform request/security logs and private historical operator backups are
  separate from Mongo controls. This feature does not rewrite backups, erase
  provider records, or recall downloads. No verified backup purge schedule or
  provider zero-retention setting exists; those limits are visible in the UI.

## AI distress handling
`backend/lib/llm.py` now gives a safety exception precedence over buyer character,
difficulty and short-response rules. For genuine distress it asks the model to stop
sales roleplay, respond warmly, disclose AI/non-crisis limitations and offer leaving
the practice. Possible self-harm/imminent danger calls for local emergency/crisis
support and a trusted person, without guessing a country, inventing a number,
diagnosing, shaming, harmful detail or pretending to summon help. Ordinary sales
idioms/negation are not automatically crises. Evaluator instructions exclude these
disclosures from scoring, quotation evidence and retry drills. If no sales evidence
exists, no invented categories/score should be produced.

This is prompt-level handling, not guaranteed detection, live monitoring, an automatic
software hang-up or a medical service. End Call/leave controls remain user-operated.
The voice loop is unchanged. Safety responses may be persisted like other transcript
turns; users can delete the session. Provider safety behaviour requires ongoing review.

## Sources and remaining launch prerequisites
Public references: [OpenAI API data](https://developers.openai.com/api/docs/guides/your-data),
[Anthropic retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data),
[ElevenLabs privacy](https://elevenlabs.io/privacy-policy),
[Google privacy](https://policies.google.com/privacy).
Account-specific retention/opt-outs are not established by reading a public policy.
Operator legal identity, verified privacy contact, jurisdiction-specific review,
backup expiry process and managed-auth upstream recovery remain launch prerequisites,
not fabricated policies or features. This task does not deploy the app.

## Verification
The privacy smoke checks use disposable internal fixtures and real local Mongo
plus curl through the public preview. Browser checks cover visible confirmation,
JSON download and permanent erasure. No destructive checks target existing users.
Result: all 17 public curl requests (including expected negative cases), real Mongo
postconditions, `yarn typecheck`, and the 12.2-second public browser journey passed.
The browser created a real demo, downloaded its transcript JSON, cancelled/confirmed
session deletion, verified empty History, erased the guest and verified cleared state.
Desktop/mobile captures passed without console errors or failed requests. Fixtures
were disposable; no existing users were deleted. Safety verification checked prompt
priority and evaluator/hint instructions, not live crisis-response quality. Physical
microphone/audio and upstream Google login were not re-certified in this privacy pass.
See `memory/SPEC.md` for the script/result locations and continuing limitations.