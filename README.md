# Fahari Ledger

USSD/SMS/Voice sales, credit ("deni"), and eTIMS compliance ledger for informal
Mombasa micro-traders. Built for the Africa's Talking Telecommunications
Innovation Hackathon, Mombasa, 30 September 2026.

See `PROJECT.md` for the full problem statement, scope, and demo script.
See `docs/architecture.md` for the end-to-end flow and `docs/ussd-menu-tree.md`
for the exact USSD screens.

## Quick start

1. Copy `.env.example` to `.env` and fill in your Africa's Talking
   credentials.
2. Start everything:

   ```bash
   docker compose up --build
   ```

3. Create the tables and seed the deterministic demo scenario:

   ```bash
   docker compose exec app python -m scripts.seed_demo_data
   ```

   The demo vendor is `+254700000000`. The seeded state is:

   - 30kg tilapia purchased for KES 12,000
   - 13kg sold for KES 7,800
   - 17kg remaining
   - KES 2,000 outstanding debt
   - KES 4,200 pending invoice from Nyali Hotel Supplies

   The seed is database-only and does not send SMS. To rebuild the scenario:

   ```bash
   docker compose exec app python -m scripts.seed_demo_data --reset
   ```

## Africa's Talking integration

Africa's Talking Voice callbacks require a publicly reachable web endpoint and
the Voice API expects your application to return XML instructions for the call.
For local development, expose port 8000 through an HTTPS tunnel and set
`PUBLIC_BASE_URL` to the resulting URL.

Configure your AT app with:

- USSD callback: `https://<public-host>/ussd`
- Voice callback: `https://<public-host>/voice`
- SMS delivery reports (optional): `https://<public-host>/sms/status`

**Important:** Africa's Talking currently states that its Voice Sandbox is not
operational. For actual Voice testing, request a **Voice Test Number** from
the AT dashboard rather than relying on the sandbox simulator.

The voice flow is:

1. AT POSTs the incoming call to `/voice`.
2. Fahari returns XML that speaks a prompt and starts a `<Record>` action.
3. AT posts the recording callback to `/voice/recording`.
4. Fahari sends the recording to the configured ASR provider.
5. The controlled parser extracts item, quantity, and price.
6. The sale is persisted with `source="voice"`.
7. Fahari sends an SMS confirmation.
8. Fahari returns XML confirming the sale to the caller.

Africa's Talking documents `.wav` and `.mp3` as supported recording formats.

Set `ASR_PROVIDER=whisper` (OpenAI) or `ASR_PROVIDER=google` (Google Cloud
Speech-to-Text, `sw-KE` locale) in `.env` — both are implemented in
`app/voice/asr_client.py`. A transcription failure with either provider falls
back gracefully to a "please use USSD instead" response; it never corrupts
ledger data.

## Health and readiness

- `GET /health` — liveness only. Returns `{"status": "ok"}` once the process
  is up; does not touch the database.
- `GET /ready` — readiness. Runs `SELECT 1` against the configured database
  and returns 503 if it can't. Use this one for deploy/tunnel health checks
  and pre-demo verification, not `/health`.

Delivery-report callbacks received at `/sms/status` are logged (via the
standard `logging` module, under `fahari.*` loggers — set `LOG_LEVEL` in
`.env` to control verbosity) and always return `200 OK`; the product does not
depend on them to function.

## Rehearsal helper

To fire the simulated eTIMS buyer-initiated invoice event on demand during a
demo (rather than waiting on a timer):

```bash
docker compose exec app python -m scripts.trigger_etims_event --phone +254700000000
```

This helper sends an SMS through the configured Africa's Talking sender.

## Running tests

```bash
docker compose exec app pytest
```

## Repo layout

See `docs/architecture.md` for the module map and why `ussd/`, `sms/`,
`voice/`, and `etims_sim/` are kept isolated from each other.
