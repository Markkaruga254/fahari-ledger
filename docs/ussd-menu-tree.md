# USSD Menu Tree

Implemented in `app/ussd/menus.py`. This file is a placeholder for the full
screen-by-screen spec (every state, every input, every edge case) — fill in
before building any further on top of the USSD flow, and keep this in sync
with the code as the menu evolves.

## Current states (from the code)

- `MAIN_MENU` -> 1 Log purchase / 2 Log sale / 3 Log debt / 4 Check today / 5 Invoices
- `PURCHASE_ITEM` -> `PURCHASE_QTY` -> `PURCHASE_COST` -> END
- `SALE_ITEM` -> `SALE_QTY` -> `SALE_PRICE` -> END
- `DEBT_CUSTOMER` -> `DEBT_ITEM` -> `DEBT_AMOUNT` -> `DEBT_NOTIFY` -> END
- `INVOICES_MENU` -> select invoice -> accept/dispute -> END

TODO: expand each state with exact prompt text, input validation rules, and
error/edge-case screens (invalid input, no pending invoices, session
timeout).
