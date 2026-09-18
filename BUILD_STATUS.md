# Fahari Ledger — Build Status & Roadmap

**Repository:** `Markkaruga254/fahari-ledger`  
**Canonical branch:** `main`  
**Hackathon:** Africa's Talking Telecommunications Innovation Hackathon — Mombasa, 30 September 2026  
**Last updated:** 18 September 2026

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
30 passed in 2.43s
```

No warnings were reported.

### Tested areas

- Core ledger operations
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

### Next session

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
**Automated tests:** ✅ 30 passing  
**AT Voice Test Number:** ✅ Received — two-week testing window

### Next

**Real AT Voice E2E:** 🔥 NOW  
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
