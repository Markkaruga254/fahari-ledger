# Architecture

## Flow

| Stage | Channel | Flow |
|---|---|---|
| Morning — log a purchase | USSD | `Log purchase` -> item, qty, cost. Sets the day's baseline stock. |
| During the day — log a sale | USSD | `Log sale` -> item, qty, price. Updates running stock + cash total. |
| Overstock nudge | SMS (auto) | Threshold rule (`app/services/overstock.py`), no ML model. |
| Log a debt | USSD | `Log debt` -> customer number, item, amount. |
| Debt reminder | SMS (opt-in) | Sent to the customer only with vendor confirmation. |
| eTIMS invoice alert | SMS + USSD | Simulated buyer-initiated invoice (`app/etims_sim/`). Accept/dispute via USSD. |
| End-of-day summary | SMS (auto) | Sales, debts owed, pending invoices. |
| Voice logging | Voice + ASR | One scripted demo path — `app/voice/`. Kept isolated from the USSD core. |

## Why the modules are isolated

`app/ussd/`, `app/sms/`, `app/voice/`, and `app/etims_sim/` do not import from
each other — they only share `app/services/` (pure DB logic, no network
calls) and `app/db/`. This means the Voice/ASR path — the one part of the
system with a live third-party network dependency — can fail without taking
the USSD core down, since it doesn't share in-memory state with it.

## Data flow for the demo's key differentiator

```
scripts/trigger_etims_event.py  (rehearsal control)
        |
        v
app/etims_sim/event_generator.py
        |
        +--> app/services/ledger.create_invoice()   (DB write)
        +--> app/sms/sender.send_sms()               (AT SMS API)
                |
                v
        vendor replies via USSD (1=accept, 2=dispute)
                |
                v
        app/ussd/menus.py -> ledger.respond_to_invoice()
```
