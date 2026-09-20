# Fahari Ledger — Build Status & Roadmap

**Repository:** `Markkaruga254/fahari-ledger`  
**Canonical branch:** `main`  
**Hackathon:** Africa's Talking Telecommunications Innovation Hackathon — Mombasa, 30 September 2026  
**Last updated:** 20 September 2026

This document is the engineering reference for **what Fahari Ledger currently has, what has been tested, what is intentionally simulated, and what we build next**.

---

## 1. Current product thesis

Fahari Ledger helps underserved small businesses turn everyday business events into a persistent, actionable record using the phone they already have.

The primary demo persona remains a **Kongowea fish seller / mama mboga** using a feature phone or basic smartphone.

The underlying ledger is deliberately generic:

- Purchase
- Sale
- Debt
- Expense
- Order
- Invoice
- Payment

The business can change; the underlying event-ledger model does not.

### Core channels

| Channel | Role |
|---|---|
| **USSD** | Primary transaction entry and ledger queries |
| **SMS** | Notifications, confirmations and summaries |
| **Voice** | Accessibility / alternative transaction-entry channel |
| **Africa's Talking** | Telecom infrastructure connecting the product to real users |

---

## 2. What is already built

### A. Core ledger

The business logic has been separated from telecom adapters so the ledger can be tested independently.

Implemented:

- Create purchases
- Create sales
- Create debts
- Create invoices
- Calculate remaining stock
- Generate end-of-day summaries
- Track items purchased and sold
- Track outstanding amounts
- Invoice lifecycle:
  - pending
  - accepted
  - disputed
  - auto-rejected after deadline
- Protection against negative stock

The core ledger is the foundation. External services should not be required for the business rules to work.

---

### B. USSD

The USSD flow is implemented as an explicit session/state machine.

Implemented flows:

1. Log purchase
2. Log sale
3. Log debt
4. Check today's activity
5. View invoices
6. Accept invoice
7. Dispute invoice
8. Invalid-input handling
9. Session termination

Validation includes:

- Positive numeric quantities/amounts
- Required item names
- Required customer numbers
- Invoice existence/state validation
- Expired-invoice handling
- Session phone-number tracking

The USSD flow is intended to remain the **primary demo path**.

---

### C. SMS

SMS functionality has been separated behind a notification/service layer.

Implemented notification types:

- Overstock alert
- Debt reminder
- Invoice alert
- End-of-day summary
- Voice transaction confirmation

The notification layer calls the SMS adapter rather than embedding telecom delivery logic throughout the application.

This gives us one place to integrate and test Africa's Talking SMS delivery.

---

### D. Overstock intelligence

The current overstock system deliberately uses a deterministic heuristic rather than ML.

It considers:

- Quantity purchased
- Quantity remaining
- Time of day
- Item

Alerts are deduplicated by:

`(vendor, item, day)`

This is intentionally simple and explainable.

**Important:** this is a business-rule signal, not an AI/ML model.

---

### E. Simulated eTIMS workflow

The repository contains a simulated buyer-initiated invoice event.

Implemented:

1. Generate invoice event
2. Notify vendor through SMS
3. Vendor opens the USSD invoice flow
4. Vendor accepts or disputes
5. Deadline is enforced
6. Expired invoices cannot be accepted

The demo uses:

- Buyer: **Nyali Hotel Supplies**
- Amount: **KES 4,200**
- A realistic remaining-deadline scenario

**Current limitation:** this is a simulation. Fahari Ledger is **not connected to KRA's live eTIMS system**.

We should never present the simulation as a live KRA integration.

---

### F. Voice logging

A complete first-pass Voice pipeline has been built.

Current flow:

`AT Voice call → Record → recording callback → ASR → deterministic parser → ledger → SMS confirmation → spoken confirmation`

Implemented:

- `POST /voice`
- `POST /voice/recording`
- Public callback URL configuration through `PUBLIC_BASE_URL`
- XML voice responses
- Recording callback handling
- Whisper ASR integration path
- Controlled item vocabulary
- Basic English and Swahili number parsing
- Sale persistence with `source="voice"`
- SMS confirmation
- Spoken confirmation
- Graceful fallback when transcription/parsing fails
- XML escaping
- Tests for voice responses and media type

The parser currently uses a controlled vocabulary / deterministic matching approach rather than a trained NLU model.

---

## 3. Africa's Talking integration status

### Current telecom access

**Africa's Talking has now provided Fahari Ledger with a Voice Test Number for a two-week testing window.**

This changes the immediate plan: Voice is no longer waiting on approval. We can now perform real phone-based Voice integration testing.

**Testing window:** two weeks from the date the test number was issued.

The exact number should **not** be committed to this public repository or documentation. Store it securely in the local/environment configuration used for testing.

### What is already verified

Before receiving the real test number, we verified through local/public testing:

- `/voice` returns HTTP 200
- Voice response is valid XML
- Public callback URL is generated correctly
- Public `/voice/recording` endpoint is reachable
- Failure in the ASR path produces a graceful user-facing fallback

### What the test number now lets us verify

We can now test the complete real-world Voice path:

`phone call → AT Voice → Fahari callback → recording → ASR → parser → ledger → SMS → spoken confirmation`

This should become an immediate integration milestone rather than a future item.

### Remaining telecom integration

- Africa's Talking **USSD integration**
- Africa's Talking **SMS integration**
- Real Voice end-to-end testing using the supplied test number
- Failure/retry behaviour across all telecom channels

---

## 4. Test status

The current automated test suite has been run inside Docker with:

```bash
docker compose exec app pytest -q
```

Latest verified result:

```
31 passed in 2.13s
```

The full suite passed cleanly inside the Docker runtime. Host-side pytest initially exposed an environment mismatch because Kali is using Python 3.13 while the repository pins `psycopg2-binary==2.9.9`; the application runtime remains Python 3.12.14 in Docker. No dependency changes were made.

### Tested areas

- Core ledger operations
- Vendor phone normalization (whitespace variants resolve to the same vendor)
- Docker application rebuild from the current repository state
- FastAPI health endpoint
- End-to-end USSD purchase smoke test against the rebuilt container
- Stock calculations
- End-of-day summaries
- Debt tracking
- Invoice lifecycle
- Expired invoice rejection
- USSD session flows
- USSD validation
- USSD invoice actions
- Overstock scheduler behaviour
- Overstock deduplication
- Debt SMS orchestration
- Notification adapter behaviour
- eTIMS simulation flow
- Voice parser
- Voice routing
- Voice confirmation
- Public callback URL behaviour
- XML response handling

### Important distinction

Automated tests prove that our application logic behaves as expected.

They do **not** replace real telecom integration testing.

The next test layer is now:

1. **Real Voice call**
2. **Real USSD session**
3. **Real SMS delivery**
4. **Full cross-channel scenario**

---

## 5. Deterministic demo data

The repository includes a repeatable demo seed.

Demo vendor:

- Phone: `+254700000000`

Demo customer:

- Phone: `+254711111111`

Demo buyer:

- Nyali Hotel Supplies

Scenario:

| Event | Data |
|---|---|
| Purchase | 30kg tilapia — KES 12,000 |
| Sale 1 | 8kg tilapia — KES 4,800 |
| Sale 2 | 5kg tilapia — KES 3,000 |
| Remaining stock | 17kg |
| Debt | KES 2,000 |
| Invoice | KES 4,200 |
| Invoice deadline | 29 days remaining in seeded scenario |

The seed is database-only and does not send external SMS.

This keeps demos repeatable and prevents accidental telecom messages during local setup.

---

## 6. Architecture snapshot

Current high-level structure:

```text
                    ┌────────────────────┐
                    │   Africa's Talking │
                    └─────────┬──────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
              USSD           SMS          Voice
                │             │             │
                ▼             ▼             ▼
          ┌────────────────────────────────────┐
          │          Application Layer         │
          │                                    │
          │  USSD router / SMS scheduler /     │
          │  Voice router / eTIMS simulator    │
          └──────────────────┬─────────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Notification Layer  │
                  │ + Business Services │
                  └──────────┬──────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Core Ledger   │
                    │                 │
                    │ Purchase        │
                    │ Sale            │
                    │ Debt            │
                    │ Invoice         │
                    │ Stock/Summary   │
                    └────────┬────────┘
                             │
                             ▼
                       PostgreSQL
```

The important architectural rule is:

> **Telecom adapters should connect to the business system; telecom delivery should not contain the business rules.**

---

## 7. What is NOT built yet

The core application build has now reached a stable local integration checkpoint. The remaining work is primarily real telecom integration and demo hardening, rather than core ledger construction.

These are intentional next-stage items, not failures.

### Priority 1 — Real Africa's Talking Voice test

**NEW: Test number received.**

Build and verify:

- Configure the supplied Voice Test Number
- Point the Voice callback to the public application
- Make real calls
- Record transactions
- Verify recording callbacks
- Verify transcription
- Verify parsing
- Verify database writes
- Verify SMS confirmation
- Verify spoken confirmation
- Test ASR failure fallback

**Acceptance condition:** one complete real call-to-ledger transaction works end-to-end.

---

### Priority 2 — Real Africa's Talking USSD

Build and verify:

- AT USSD callback
- Session lifecycle
- Real phone-number identification
- Real menu interaction
- Production-like callback behaviour
- Error/failure handling

**Acceptance condition:** a real test phone can complete the core USSD flow against the running application.

---

### Priority 3 — Real Africa's Talking SMS

Connect the existing notification layer to the AT SMS API.

Verify:

- Overstock SMS
- Debt reminder
- Invoice alert
- End-of-day summary
- Voice confirmation

**Acceptance condition:** at least one real test number receives each required message type without breaking the core ledger.

---

### Priority 4 — Cross-channel integration

Once individual channels work, run the entire scenario as one system:

```text
USSD purchase
     ↓
USSD sale
     ↓
Ledger / stock update
     ↓
Automated SMS alert
     ↓
USSD debt entry
     ↓
SMS debt reminder
     ↓
Simulated invoice event
     ↓
SMS invoice alert
     ↓
USSD accept/dispute
     ↓
EOD SMS
     ↓
Voice transaction
     ↓
Ledger confirmation
```

This is the point where we prove that Fahari is a **telecommunications product**, rather than three disconnected demos.

---

### Priority 5 — Demo hardening

After telecom integration works, stop adding unnecessary features.

Focus on:

- deterministic seed/reset
- clean demo environment
- obvious logs
- failure fallbacks
- timeout handling
- duplicate-event handling
- realistic demo data
- clear error messages
- repeatable setup instructions
- safe handling of telecom credentials
- protecting test numbers from accidental spam

The goal is not maximum feature count.

The goal is **a reliable 3-minute demonstration**.

---

### Priority 6 — Demo rehearsal

The final demo should prove one coherent story:

```text
Purchase
   ↓
Sale
   ↓
Stock visibility
   ↓
Overstock SMS
   ↓
Customer debt
   ↓
Buyer invoice event
   ↓
USSD accept/dispute
   ↓
End-of-day summary
   ↓
Voice accessibility moment
```

The demo should make it obvious that USSD, SMS and Voice are not decorative integrations.

They are the actual interface.

---

## 8. Current demo scenario

The main rehearsal scenario should remain a fish seller supplied by Kongowea.

### Morning

The seller buys:

**30kg tilapia for KES 12,000**

She records the purchase through USSD.

### During the day

She records:

**8kg sold for KES 4,800**

Then:

**5kg sold for KES 3,000**

The ledger now shows:

**17kg remaining**

### Afternoon

The overstock rule identifies the remaining stock as a potential loss and sends an SMS action prompt.

### Credit sale

The seller records:

**KES 2,000 owed by a regular customer**

The seller explicitly chooses whether a reminder should be sent.

### Hotel order / invoice

A simulated buyer-initiated invoice arrives:

**Nyali Hotel Supplies — KES 4,200**

The seller receives an SMS and uses USSD to accept or dispute it.

### End of day

The seller receives a compact SMS summary containing:

- sales
- outstanding debt
- remaining stock
- pending invoice status

### Accessibility beat

The seller calls the Voice Test Number and says what she sold.

The system:

- records the speech
- transcribes it
- extracts the transaction
- writes it to the ledger
- confirms it by SMS and voice

---

## 9. Engineering rules going forward

### Rule 1 — Keep the ledger independent

Business logic should remain testable without Africa's Talking, Whisper, KRA or any other external API.

### Rule 2 — Telecom is load-bearing

Every telecom channel must have a meaningful product role.

- USSD → entry/query
- SMS → notification/confirmation
- Voice → accessibility

### Rule 3 — No fake integrations

If something is simulated, label it as simulated.

Especially:

- KRA/eTIMS
- telecom delivery
- ASR providers

### Rule 4 — Prefer deterministic systems during the hackathon

Do not introduce ML where a transparent rule works better.

The current product does not need:

- a chatbot
- credit scoring
- predictive lending
- unnecessary recommendation models

### Rule 5 — Test before adding features

The sequence is:

`build → test → integrate → test → rehearse`

Not:

`build → build → build → discover everything is broken`

### Rule 6 — One coherent story beats feature count

A judge should be able to understand Fahari from one transaction.

---

## 10. Immediate execution order

### Next session — 20 September 2026

**Start from the telecom integration layer. Do not reopen the completed core ledger/USSD work unless a new integration test exposes a regression.**

**1. Voice Test Number — use the two-week window**
- configure the number
- make the first real call
- capture callback behaviour
- test one simple transaction
- verify ledger write
- verify confirmation
- document any AT-specific behaviour

**2. Africa's Talking USSD**
- connect callback
- test session
- test real phone flow

**3. Africa's Talking SMS**
- connect sender
- test notification delivery

**4. Run the full integrated scenario**
- purchase
- sale
- stock
- SMS
- debt
- invoice
- USSD response
- EOD summary
- Voice

**5. Freeze core architecture**
- avoid unnecessary refactors

**6. Rehearse**
- clean database
- seed
- run
- demonstrate
- reset
- repeat

---

## 11. Definition of "hackathon ready"

Fahari Ledger is ready for the final demo when all of the following are true:

- [ ] Core ledger tests pass
- [ ] USSD works through Africa's Talking
- [ ] SMS delivery works through Africa's Talking
- [ ] Overstock notification works
- [ ] Debt reminder works
- [ ] Invoice notification works
- [ ] Invoice accept/dispute works
- [ ] End-of-day summary works
- [ ] Voice Test Number completes a real end-to-end transaction
- [ ] Voice fallback works when ASR fails
- [ ] Demo seed is deterministic
- [ ] Demo can be reset quickly
- [ ] No external API failure can destroy the entire demo
- [ ] eTIMS simulation is clearly labelled
- [ ] The 3-minute story is rehearsed
- [ ] The team can explain exactly why USSD + SMS + Voice are necessary

---

## 12. Status at this checkpoint

### Built

**Core ledger:** ✅  
**USSD application flow:** ✅  
**SMS orchestration:** ✅  
**Overstock heuristic:** ✅  
**Debt workflow:** ✅  
**eTIMS simulation:** ✅  
**Voice pipeline:** ✅  
**Public callback setup:** ✅  
**Deterministic demo seed:** ✅  
**Automated tests:** ✅ 44 passing (31 core + 13 added in operational hardening)
**Docker runtime:** ✅ Python 3.12.14
**Docker rebuild + health smoke test:** ✅
**USSD end-to-end purchase smoke test:** ✅
**Vendor phone whitespace normalization:** ✅
**SMS delivery-report callback (`/sms/status`):** ✅
**SMS send retry/backoff:** ✅
**Structured logging (`fahari.*`, `LOG_LEVEL`):** ✅
**Google Cloud Speech-to-Text ASR path:** ✅ (alongside existing Whisper path)
**Readiness check (`/ready`, DB connectivity):** ✅
**Local working tree / origin:** ✅ pushed and confirmed on `main` at commit `59e7294`  
**AT Voice Test Number:** ✅ Received — two-week testing window

### Next

**Push the `.env` config-crash fix (below) to `main`:** 🔥 IMMEDIATE — not yet on origin  
**Real AT Voice E2E:** 🔥 NEXT PHASE  
**AT USSD integration:** 🔜  
**AT SMS integration:** 🔜  
**Cross-channel E2E testing:** 🔜  
**Demo hardening:** 🔜  
**Final rehearsal:** 🔜

---

## 13. Reference documents

- `PROJECT.md` — product thesis, scope, problem framing and demo concept.
- `BUILD_STATUS.md` — this document; engineering status, verified work and next actions.
- `.env.example` — integration configuration reference.
- `README.md` — repository setup and operational instructions.

---

## 14. Change log

### 18 September 2026 — Core build milestone

Completed:

- strengthened ledger/business logic
- hardened USSD state machine
- added automated USSD tests
- added SMS notification orchestration
- added overstock scheduling and deduplication
- added debt reminders
- added simulated eTIMS lifecycle
- added deterministic demo seed
- completed first-pass Voice + ASR pipeline
- added public callback URL handling
- hardened XML responses
- documented Africa's Talking Voice integration
- verified the Docker test suite: **30 passed**
- merged the core build into `main`

### 18 September 2026 — Telecom testing unlocked

- Africa's Talking provided a **Voice Test Number**
- Testing window: **two weeks**
- Real Voice integration testing is now the immediate priority
- The previous "awaiting approval" status is superseded

**Next milestone:** use the Voice Test Number for a real call-to-ledger transaction, then connect and verify USSD and SMS.


### 19 September 2026 — Core validation and repair checkpoint

Completed and verified:

- Corrected the application database configuration to point at the Docker PostgreSQL service.
- Rebuilt the application container from the current repository state.
- Verified Docker runtime is Python 3.12.14.
- Ran the complete automated suite: **31 passed in 2.13s**.
- Investigated host-side pytest failures and confirmed they were caused by the host Python 3.13 environment attempting to build the pinned `psycopg2-binary==2.9.9`; the repository dependency set was left unchanged because the Docker runtime is healthy.
- Added vendor phone whitespace normalization so values such as `  +254700000010  ` resolve to the same vendor.
- Added and passed a regression test for vendor phone normalization.
- Validated USSD purchase flow state-by-state against the rebuilt application: main menu → purchase → item → quantity → total cost → successful ledger write.
- Verified `/health` returns `{"status":"ok"}`.
- Verified Docker app and PostgreSQL containers are running after rebuild.
- Confirmed local `main` and `origin/main` are synchronized at commit `1e927cb`.
- Identified the remaining Africa's Talking SMS authentication failure as an external provider-credential/configuration issue; it does not prevent the core ledger transaction from being persisted.

### 20 September 2026 — Operational hardening

Completed and verified (all local, no Docker/Postgres — full suite run
against SQLite via `pytest`, no external network calls):

- Implemented the `/sms/status` Africa's Talking delivery-report callback
  (`app/sms/router.py`), previously documented in the README but not wired
  into `app/main.py`. Logs only; always returns `200 OK` so AT never retries
  it into a spam loop.
- Added retry-with-backoff to `app/sms/sender.py`: up to 3 attempts with a
  short linear backoff before an SMS send is logged and swallowed as an
  error, so one transient AT network blip no longer costs a notification
  outright.
- Replaced `print()` calls in the SMS and Voice/ASR adapters with structured
  `logging` (`fahari.*` loggers, configurable via `LOG_LEVEL`).
- Implemented the previously-stubbed Google Cloud Speech-to-Text path in
  `app/voice/asr_client.py` (`ASR_PROVIDER=google`), `sw-KE` locale with
  `en-KE` fallback, alongside the existing Whisper path.
- Added `GET /ready` (checks DB connectivity via `SELECT 1`, returns 503 if
  unreachable) alongside the existing `GET /health` liveness check — use
  `/ready` for deploy/tunnel verification before a demo, not `/health`.
- Migrated FastAPI startup from the deprecated `@app.on_event("startup")` to
  a `lifespan` context manager (removes a deprecation warning; no behavior
  change).
- Added 13 new tests covering SMS retry/backoff, the `/sms/status` route,
  `/health` and `/ready`, and both branches of the Google ASR path (success,
  no-results, missing API key, HTTP error, MP3 vs. WAV encoding selection).
- Full suite: **44 passed** (31 previous + 13 new), run locally against
  SQLite — no regressions in existing behavior.
- Updated `README.md`, `docs/architecture.md`, and `.env.example`
  (`LOG_LEVEL`) to document all of the above.

**Not done in this pass (needs your real credentials/hardware, not code):**
real AT Voice E2E call, real AT USSD session, real AT SMS delivery, and the
cross-channel rehearsal — see the runbook for the exact sequence.

### 20 September 2026 — Pushed to `main`, config-crash bug caught and fixed

- Confirmed the operational-hardening work above is live on GitHub: commit
  `ffcf8f5` ("Add SMS status callback, retry/backoff, Google ASR, /ready
  endpoint, logging") and `59e7294` ("Remove patch file from repo, ignore
  .patch files") are both on `origin/main`. Verified by a clean re-clone of
  the repository, not just a local push confirmation.
- **Bug found on verification:** `.env.example` gained a `LOG_LEVEL` entry
  in the hardening pass, but `app/config.py`'s `Settings` class never
  declared a matching field. `pydantic-settings` rejects unknown `.env` keys
  by default, so `cp .env.example .env` — exactly what the README's own
  quick-start step 1 says to do — produced an immediate `extra_forbidden`
  crash on startup. This did not show up in the hardening pass's own test
  run because that run happened with no `.env` file present, which masked
  it.
- **Fix:** declared `log_level: str = "INFO"` on `Settings` and added
  `extra="ignore"` to `model_config` as a second line of defense against the
  same class of bug for any future `.env.example` addition that isn't
  mirrored in `app/config.py`.
- Re-verified with an actual `.env.example`-derived `.env` file (not just
  defaults) this time: **44 passed**, `Settings` loads cleanly,
  `log_level` reads back as `"INFO"`.
- **Status:** fix is ready as a patch, not yet applied/pushed to `origin`.
  This is the single next action before anything else in this document.

### Current stage

**Phase completed:** Core application build + local integration validation +
operational hardening (retries, logging, readiness check, delivery-report
callback, Google ASR).

The project has moved from feature construction into **real telecom integration and demo hardening**. The core ledger, USSD application flow, database persistence, invoice workflow, debt workflow, notifications orchestration, eTIMS simulation, and first-pass Voice pipeline are implemented and covered by automated/local validation.

### Next phase — tomorrow

1. **Real Africa's Talking Voice E2E** — configure/use the available Voice Test Number, place one real call, verify callback → recording → ASR → parser → ledger, and verify spoken/SMS confirmation.
2. **Real Africa's Talking USSD** — connect the live callback and complete the core purchase/sale flow from a real phone.
3. **Real Africa's Talking SMS** — resolve/configure provider authentication and verify real delivery of required notification types.
4. **Cross-channel E2E** — purchase → sale → stock → notification → debt → invoice → USSD response → EOD summary → Voice.
5. **Demo hardening** — clean/reset deterministic data, verify logs/fallbacks, protect credentials/test numbers, and rehearse the final 3-minute story.

**Rule for the next phase:** do not add new product features until the real telecom paths have been exercised and the existing system is repeatable end-to-end.
