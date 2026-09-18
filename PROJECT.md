# Fahari Ledger

**Africa's Talking Telecommunications Innovation Hackathon — Mombasa, 30 September 2026**

A phone-number-based sales, credit, and tax-compliance ledger for informal Mombasa micro-traders — built entirely on USSD, SMS, and Voice. No smartphone, no app, no data bundle required.

---

## 1. The problem

Mombasa's informal traders (fish sellers, mama mbogas, tailors, market vendors) run their businesses on memory and cash. This costs them money every day in two invisible ways, and — as of 1 January 2026 — a third, much sharper way:

1. **Spoilage / overstock leaks** — perishable stock (fish, vegetables) that isn't sold in time is a pure write-off, and vendors have no real-time signal telling them to discount before it's too late.
2. **Memory-based credit ("deni") leaks** — informal credit to regular customers is tracked in the vendor's head or on paper. Disputes and forgotten debts are common and undocumented.
3. **Compliance exposure (new, urgent)** — KRA's eTIMS system now validates all declared business income/expenses against digital invoices. Since January 2026, buyers (hotels, supermarkets, canteens) can no longer claim tax deductions for purchases from suppliers without a valid eTIMS invoice — and have begun cancelling contracts with informal suppliers who can't produce one. KRA's own fix, **eTIMS Lite via USSD (`*222#`)**, exists but is new, unexplained in plain language, and includes a strict rule almost nobody knows about: a buyer can generate an invoice on a seller's behalf ("buyer-initiated invoicing"), and the seller has only **30 days** to accept or dispute it before it auto-rejects.

### Why this isn't a financial-inclusion problem in the usual sense

Kenya's formal financial inclusion is already at 84.8% (2024 FinAccess), mobile money penetration is near-universal, and digital lending is already oversaturated — Kenyan digital loan default rates have hit ~40%, with documented over-indebtedness and privacy backlash against "alternative credit scoring." **We are explicitly not building a lending product, a credit score, or a chatbot.** The real gap is information and record-keeping at the point of a ten-second interaction between a vendor and a customer — not access to money.

---

## 2. Who it's for

**Primary persona:** a Kongowea-supplied fish seller or mama mboga — cash-based, feature phone or basic smartphone, no POS app, extends informal credit to regulars, occasionally supplies a hotel/restaurant/canteen (which makes her personally exposed to the eTIMS deadline problem).

Secondary personas considered but not built for in v1: tailors, tuk-tuk/boda operators (same leak pattern — memory-based records, no real-time decision signal — but weaker current evidence base than the market-trader/eTIMS angle).

---

## 3. What it does, end to end

| Stage | Channel | Flow |
|---|---|---|
| Morning — log a purchase | USSD | `Log purchase` → item, qty, cost. Sets the day's baseline stock. |
| During the day — log a sale | USSD | `Log sale` → item, qty, price. Updates running stock + cash total. Must have zero external dependencies — this is the demo's non-negotiable core. |
| Overstock nudge | SMS (auto) | Simple time-of-day-vs-stock-remaining heuristic fires an SMS: *"You have 8kg tilapia left and it's 4pm. Discount now or risk a loss tomorrow."* No ML model — a threshold rule. |
| Log a debt | USSD | `Log debt` → customer number, item, amount. |
| Debt reminder | SMS (opt-in) | Sent to the customer only with the vendor's explicit confirmation. |
| eTIMS invoice alert | SMS + USSD | Simulated buyer-initiated invoice event: *"Nyali Hotel sent an invoice for KES 4,200. Reply 1 to accept, 2 to dispute. 29 days left."* Accepted/disputed via USSD. |
| End-of-day summary | SMS (auto) | Total sales, total outstanding debts owed to her, stock remaining, pending eTIMS deadlines. |
| Voice logging (accessibility beat) | Voice + ASR | One scripted "say what you sold" call. AT Voice `record()` → recording URL via callback → sent to Whisper or Google Speech-to-Text (`sw-KE` locale) → matched against a small fixed Kongowea item/price vocabulary (keyword/regex, not a trained model) → confirmed by SMS. Demoed once, deliberately — not the primary logging path. |

---

## 4. Why telecom is load-bearing, not decorative

- **USSD** — the entire data-entry and query interface. Works on the cheapest phone in Kenya, no data cost.
- **SMS** — the entire notification/confirmation layer: overstock nudges, debt reminders, eTIMS deadlines, end-of-day summaries.
- **Voice** — the accessibility layer for one deliberate "beyond the core" moment.

Africa's Talking APIs aren't a confirmation text bolted onto some other product — they *are* the product.

---

## 5. Explicit scope decisions

**In scope (v1):**
- USSD session flow: log purchase, log sale, log debt, check today, invoices menu
- SMS: overstock nudge, debt reminder (opt-in), eTIMS alert, end-of-day summary
- Simulated eTIMS buyer-initiated invoice event + accept/dispute via USSD
- One scripted Voice + ASR logging demo

**Out of scope (and why):**
- **No credit scoring or lending** — the Kenyan digital-credit space is already saturated and reputationally damaged (documented over-indebtedness, privacy violations); building this would read as naive to an informed judge.
- **No AI chatbot as the primary interface** — USSD/SMS *is* the interface. ML appears only as a pretrained ASR call for the Voice beat and a simple threshold heuristic for the overstock nudge, never as the core mechanism.
- **No real KRA/eTIMS integration** — the buyer-initiated invoice event is simulated, not hooked into KRA's live system. This is an honest scoping decision to be stated plainly if asked, not a hidden shortcut.

---

## 6. Demo script (~3 minutes)

1. **(0:00–0:15) Cold open.** "As of this year, if a fish seller in Mombasa can't produce a digital invoice, her biggest buyer can legally stop buying from her tomorrow. Almost none of them know this."
2. **(0:15–1:15) Live USSD session.** Log a sale, log a debt, trigger the overstock nudge live.
3. **(1:15–2:00) The eTIMS moment.** SMS alert arrives, accepted via USSD.
4. **(2:00–2:30) End-of-day SMS summary** appears.
5. **(2:30–3:00) Close on scale.** "This is one phone number. It works on the cheapest feature phone in Kenya. It's the same USSD rail KRA already uses for `*222#`, and it's the same rail 70+ million SIMs in this country are already on."

---

## 7. Build plan (solo, ~10–12 days)

- **Days 1–3:** AT Sandbox USSD session flow (log purchase/sale/debt, check balance) — the non-negotiable core, must be rock-solid before anything else.
- **Days 4–6:** SMS layer (overstock nudge, debt reminder, end-of-day summary).
- **Days 7–8:** Simulated eTIMS invoice event + accept/dispute flow.
- **Days 9–10:** Voice + ASR logging pipeline (half a day build, half a day rehearsal + fallback handling) and seed realistic demo data (real Kongowea prices).
- **Remaining days:** Rehearse the 3-minute script until automatic; buffer for sandbox flakiness — the most common way solo hackathon demos fail live.

---

## 8. Key evidence backing this direction

- Kenya's formal financial inclusion: 84.8% (2024 FinAccess Household Survey, CBK/KNBS/FSD Kenya).
- Mobile money daily usage: 52.6% of Kenyans, up from 23.6% in 2021 (CBK, 2024 FinAccess).
- Digital loan default rates as high as ~40%, with documented over-indebtedness and privacy-invasive "alternative credit scoring" practices (CHI '26 paper *Risk, Data, Alignment: Making Credit Scoring Work in Kenya*; Muma & Kanjama Advocates).
- eTIMS: effective 1 January 2026, KRA validates all declared income/expenses against eTIMS records; non-eTIMS invoices are no longer deductible (KRA public notice, Nov 2025; Alphacap, HelaBora).
- eTIMS Lite USSD solution (`*222#`) built specifically for non-VAT-registered, informal-sector taxpayers (KRA press release).
- Buyer-initiated ("reverse") invoicing: seller has 30 days to accept/reject via USSD before auto-rejection (KRA Buyer Initiated Invoicing guide).
- Existing SME tools (Duka Manager, Kopo Kopo, Veira, Delytt) all assume a smartphone and app-based daily use — none target feature-phone-first, USSD-native record-keeping.
- Kongowea market context: one of East Africa's largest wholesale/retail produce markets, thousands of traders, documented price volatility and per-unit cash trading (The Star; Nation; DukaSale; Huduma Global).

---

*Maintained by Mark — Technical University of Mombasa. Built for the Africa's Talking Telecommunications Innovation Hackathon, WesterWelle Startup Haus, Mombasa, 30 September 2026.*
