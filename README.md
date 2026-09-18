# Fahari Ledger

USSD/SMS/Voice sales, credit ("deni"), and eTIMS compliance ledger for informal
Mombasa micro-traders. Built for the Africa's Talking Telecommunications
Innovation Hackathon, Mombasa, 30 September 2026.

See `PROJECT.md` for the full problem statement, scope, and demo script.
See `docs/architecture.md` for the end-to-end flow and `docs/ussd-menu-tree.md`
for the exact USSD screens.

## Quick start

1. Copy `.env.example` to `.env` and fill in your Africa's Talking sandbox
   credentials (username `sandbox` + API key from your AT dashboard).
2. Start everything:

   ```bash
   docker compose up --build
   ```

3. Create the tables (first run only):

   ```bash
   docker compose exec app python -m scripts.seed_demo_data
   ```

4. Expose your local server to Africa's Talking with ngrok (or similar) and
   set the callback URLs in your AT sandbox app:
   - USSD callback: `https://<ngrok-url>/ussd`
   - SMS delivery reports (optional): `https://<ngrok-url>/sms/status`
   - Voice callback: `https://<ngrok-url>/voice`

5. Dial your sandbox USSD code from the AT simulator to walk the menu tree.

## Rehearsal helper

To fire the simulated eTIMS buyer-initiated invoice event on demand during a
demo (rather than waiting on a timer):

```bash
docker compose exec app python -m scripts.trigger_etims_event --phone +254700000000
```

## Running tests

```bash
docker compose exec app pytest
```

## Repo layout

See `docs/architecture.md` for the module map and why `ussd/`, `sms/`,
`voice/`, and `etims_sim/` are kept isolated from each other.
