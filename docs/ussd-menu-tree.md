# USSD Menu Tree

Implemented in `app/ussd/menus.py`. This file mirrors the code — if you change
a prompt or a validation rule in `menus.py`, update the matching section here.

Session state is in-memory (`app/ussd/session.py`, single process). A session
is cleared as soon as a state returns `END`, so a retried/late callback can
never double-commit a transaction.

## States

- `MAIN_MENU` -> 1 Log purchase / 2 Log sale / 3 Log debt / 4 Check today / 5 Invoices
- `PURCHASE_ITEM` -> `PURCHASE_QTY` -> `PURCHASE_COST` -> END
- `SALE_ITEM` -> `SALE_QTY` -> `SALE_PRICE` -> END
- `DEBT_CUSTOMER` -> `DEBT_ITEM` -> `DEBT_AMOUNT` -> `DEBT_NOTIFY` -> END
- `INVOICES_MENU` -> select invoice -> accept/dispute -> END

## Screens and validation

| State | Prompt | Validation (invalid input re-prompts, never commits) |
|---|---|---|
| `MAIN_MENU` | `CON Fahari Ledger\n1. Log purchase\n2. Log sale\n3. Log debt\n4. Check today\n5. Invoices` | Anything but 1–5 → `END Invalid choice. Please dial again.` |
| `PURCHASE_ITEM` / `SALE_ITEM` | `CON Enter item (e.g. tomato)` | Non-empty after strip; stored lowercased. |
| `PURCHASE_QTY` / `SALE_QTY` | `CON Enter quantity in kg (...)` | Finite number > 0 (`inf`/`nan`/0/negative rejected). |
| `PURCHASE_COST` / `SALE_PRICE` | `CON Enter total cost/price in KES (...)` | Finite number > 0. Ledger layer re-validates. |
| `DEBT_CUSTOMER` | `CON Enter customer phone number` | Must look like a phone number (9–15 digits); Kenyan `07...` / `254...` / spaced / dashed forms are normalized to E.164 (`+254...`) before storage. |
| `DEBT_ITEM` | `CON Enter item (or 0 to skip)` | `0` → no item recorded. |
| `DEBT_AMOUNT` | `CON Enter amount owed in KES` | Finite number > 0. |
| `DEBT_NOTIFY` | `CON Notify customer by SMS? 1. Yes 2. No` | Only 1/2; SMS goes out only on explicit `1`. |
| `4. Check today` | `END Today: KES {sales} sold, KES {owed} owed, stock {...}.` | `owed` = **all** unsettled debts (any date), not just today's. |
| `5. Invoices` | `CON Pending invoices:` + up to 3 lines `{id}. {buyer} KES {amount} ({days}d left)` + `Enter invoice number`, or `END No pending invoices.` | Selection must be an invoice **owned by the calling vendor**; another vendor's id is re-prompted. Then `CON 1. Accept 2. Dispute` → `END Invoice accepted/disputed.` Expired or already-handled invoices end with the reason. |

## Edge cases covered by tests (`tests/test_ussd_flow.py`, `tests/test_hardening.py`)

- Invalid menu choice, negative/zero/`inf` quantities and amounts.
- Invalid customer number (nothing persisted until a valid one is given).
- Invoice id belonging to a different vendor (cannot accept/dispute it).
- Empty invoice list (session ends cleanly, repeatable).
- `serviceCode` missing from the callback (accepted, defaults to `""`).
