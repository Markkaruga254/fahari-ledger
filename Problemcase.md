The problem, in one sentence

Mombasa's informal traders (fish sellers, mama mbogas, tailors) run entirely on memory and cash, which costs them money every day through spoiled stock and forgotten debts — and as of January 2026, it's starting to cost them their biggest customers too, because KRA now requires digital tax invoices (via USSD) that most of them don't know exist and can't produce.

Who it's for

A single persona, held consistently through the whole demo: a Kongowea-supplied fish seller or mama mboga, cash-based, feature phone or basic smartphone, no POS app, no formal bookkeeping, occasionally sells on credit to regulars, occasionally supplies a hotel/restaurant/canteen (which makes her personally exposed to the eTIMS deadline problem).

What it does, end to end

Stage 1 — Morning: log what you bought.
She dials the USSD code after her Kongowea supply run. A short menu: "1. Log purchase 2. Log sale 3. Log debt 4. Check today 5. Invoices." She picks "Log purchase," enters item, quantity, cost — three quick numeric/menu taps, no typing. This gives the system a baseline: what she's carrying today and what it cost her.

Stage 2 — During the day: log a sale in the ten seconds she has between customers.
Same USSD menu, "Log sale" — item, quantity, price. Every entry updates a running total: cash in, stock remaining. This is the reliable backbone of the whole system and it must never fail on stage, so it has zero external dependencies — just USSD session state and a database write.

Stage 3 — The overstock nudge (the "why does this matter" moment).
As stock-remaining crosses a threshold relative to how the day is progressing (a simple time-of-day-vs-stock-sold heuristic, not real ML), an SMS fires automatically: "You have 8kg tilapia left and it's 4pm. Discount now or risk a loss tomorrow." This is the single clearest "this saved me real money today" story you can tell a judge — it converts an information gap into a same-day decision.

Stage 4 — Logging a debt, and the customer-side reminder.
"Log debt" — customer's phone number, item, amount. With her explicit confirmation, an SMS goes to the customer: "You owe [vendor name] KES 200 for sukuma, logged [date]." This kills the "who owes me what" leak and gives her something more durable than memory if there's ever a dispute.

Stage 5 — The eTIMS moment (your differentiator).
A simulated event: a buyer (e.g. "Nyali Hotel Supplies") sends a buyer-initiated invoice through the eTIMS rail. Your system intercepts/represents this and sends her an SMS: "Nyali Hotel sent an invoice for KES 4,200. Reply 1 to accept, 2 to dispute. 29 days left before it auto-rejects and you may lose this buyer." She responds via USSD. This is the one thing almost no other team at the hackathon will have researched, and it's the moment your 15-second cold open ("her biggest buyer can legally drop her tomorrow and she doesn't know it") pays off live.

Stage 6 — Closing up: the end-of-day SMS.
Automatically sent, no action needed from her: total sales, total outstanding debts owed to her, stock remaining, and — if applicable — any pending eTIMS invoice deadlines. This is the "she now knows things she never knew before" payoff shot.

Stage 7 — Voice, as one deliberate accessibility beat, not the backbone.
One scripted call demonstrating "say what you sold" — she speaks a sale instead of dialing it in, AT's Voice API records it, your backend runs it through an ASR (Whisper or Google STT with the sw-KE locale), a small keyword/price-list matcher extracts item/quantity/price, and it's confirmed by SMS. This shows accessibility ambition without risking your core demo on a live third-party ASR call.

What's explicitly out of scope, and why
No credit scoring, no lending. The research showed this space is already saturated and reputationally toxic in Kenya (40% default rates, privacy backlash) — building it would read as naive to any judge who's followed the fintech news.
No AI chatbot as the interface. USSD/SMS is the interface; ML shows up only as a pretrained ASR call and a simple heuristic, never as the main mechanism.
No real eTIMS integration. You'll simulate the buyer-initiated invoice event rather than hooking into KRA's actual system — that's an honest, statable scoping decision, not a hidden shortcut, and you should say so explicitly if asked.
Why telecom is load-bearing, not decorative
USSD is the entire data-entry and query interface — no smartphone, no data cost, works on the cheapest phone in Kenya.
SMS is the entire notification and confirmation layer — overstock nudges, debt reminders, eTIMS deadlines, end-of-day summaries.
Voice is the accessibility layer for the one moment you want to show ambition beyond the core.
Africa's Talking APIs aren't sending a confirmation text at the end of some other product — they are the product.
