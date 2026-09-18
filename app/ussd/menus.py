"""
USSD menu tree for the competition demo.

Design principle: keep the core actions short and predictable. The business
event is committed before the session ends; telecom notifications remain
outside the core ledger path.
"""
from app.db.session import SessionLocal
from app.services import ledger
from app.ussd.session import get_session, clear_session


def handle(session_id: str, phone_number: str, text: str) -> tuple[str, bool]:
    session = get_session(session_id)
    parts = text.split("*") if text else []
    last_input = parts[-1] if parts else ""
    state = session["state"]

    db = SessionLocal()
    try:
        if text == "":
            session["state"] = "MAIN_MENU"
            return _main_menu(), False

        if state == "MAIN_MENU":
            return _route_main_menu(session, last_input)

        if state.startswith("PURCHASE_"):
            return _purchase_flow(db, session, phone_number, last_input)

        if state.startswith("SALE_"):
            return _sale_flow(db, session, phone_number, last_input)

        if state.startswith("DEBT_"):
            return _debt_flow(db, session, phone_number, last_input)

        if state == "INVOICES_MENU":
            return _invoices_menu(db, session, phone_number, last_input)

        session["state"] = "MAIN_MENU"
        return _main_menu(), False
    finally:
        db.close()
        if session["state"] == "END":
            clear_session(session_id)


def _main_menu() -> str:
    return (
        "CON Fahari Ledger\n"
        "1. Log purchase\n"
        "2. Log sale\n"
        "3. Log debt\n"
        "4. Check today\n"
        "5. Invoices"
    )


def _route_main_menu(session, choice: str) -> tuple[str, bool]:
    if choice == "1":
        session["state"] = "PURCHASE_ITEM"
        return "CON Enter item (e.g. tomato)", False
    if choice == "2":
        session["state"] = "SALE_ITEM"
        return "CON Enter item (e.g. tomato)", False
    if choice == "3":
        session["state"] = "DEBT_CUSTOMER"
        return "CON Enter customer phone number", False
    if choice == "4":
        db = SessionLocal()
        try:
            vendor = ledger.get_or_create_vendor(db, session.get("phone_number", ""))
            summary = ledger.today_summary(db, vendor.id)
            session["state"] = "END"
            remaining = ", ".join(
                f"{item}: {qty:g}kg"
                for item, qty in summary["items_remaining"].items()
                if qty > 0
            ) or "none"
            return (
                f"END Today: KES {summary['total_sales']:.0f} sold, "
                f"KES {summary['total_owed_to_vendor']:.0f} owed, "
                f"stock {remaining}."
            ), True
        finally:
            db.close()
    if choice == "5":
        session["state"] = "INVOICES_MENU"
        return _render_invoices_menu(session.get("phone_number", "")), False

    session["state"] = "END"
    return "END Invalid choice. Please dial again.", True


def _purchase_flow(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]

    if session["state"] == "PURCHASE_ITEM":
        item = value.strip().lower()
        if not item:
            return "CON Enter a valid item", False
        data["item"] = item
        session["state"] = "PURCHASE_QTY"
        return "CON Enter quantity in kg (e.g. 10)", False

    if session["state"] == "PURCHASE_QTY":
        quantity = _positive_float(value)
        if quantity is None:
            return "CON Enter a quantity greater than 0", False
        data["quantity"] = quantity
        session["state"] = "PURCHASE_COST"
        return "CON Enter total cost in KES (e.g. 500)", False

    if session["state"] == "PURCHASE_COST":
        cost = _positive_float(value)
        if cost is None:
            return "CON Enter a cost greater than 0", False
        data["cost"] = cost
        ledger.log_purchase(db, phone_number, data["item"], data["quantity"], data["cost"])
        session["state"] = "END"
        return f"END Logged: bought {data['quantity']:g}kg {data['item']} for KES {data['cost']:.0f}.", True

    session["state"] = "END"
    return "END Something went wrong. Please dial again.", True


def _sale_flow(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]

    if session["state"] == "SALE_ITEM":
        item = value.strip().lower()
        if not item:
            return "CON Enter a valid item", False
        data["item"] = item
        session["state"] = "SALE_QTY"
        return "CON Enter quantity in kg (e.g. 2)", False

    if session["state"] == "SALE_QTY":
        quantity = _positive_float(value)
        if quantity is None:
            return "CON Enter a quantity greater than 0", False
        data["quantity"] = quantity
        session["state"] = "SALE_PRICE"
        return "CON Enter total price in KES (e.g. 200)", False

    if session["state"] == "SALE_PRICE":
        price = _positive_float(value)
        if price is None:
            return "CON Enter a price greater than 0", False
        data["price"] = price
        ledger.log_sale(db, phone_number, data["item"], data["quantity"], data["price"])
        session["state"] = "END"
        return f"END Logged: sold {data['quantity']:g}kg {data['item']} for KES {data['price']:.0f}.", True

    session["state"] = "END"
    return "END Something went wrong. Please dial again.", True


def _debt_flow(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]

    if session["state"] == "DEBT_CUSTOMER":
        customer = value.strip()
        if not customer:
            return "CON Enter customer phone number", False
        data["customer_phone"] = customer
        session["state"] = "DEBT_ITEM"
        return "CON Enter item (or 0 to skip)", False

    if session["state"] == "DEBT_ITEM":
        data["item"] = None if value.strip() == "0" else value.strip()
        session["state"] = "DEBT_AMOUNT"
        return "CON Enter amount owed in KES", False

    if session["state"] == "DEBT_AMOUNT":
        amount = _positive_float(value)
        if amount is None:
            return "CON Enter an amount greater than 0", False
        data["amount"] = amount
        session["state"] = "DEBT_NOTIFY"
        return "CON Notify customer by SMS? 1. Yes 2. No", False

    if session["state"] == "DEBT_NOTIFY":
        if value not in {"1", "2"}:
            return "CON Choose 1 for Yes or 2 for No", False
        notify = value == "1"
        ledger.log_debt(
            db,
            phone_number,
            data["customer_phone"],
            data.get("item"),
            data["amount"],
            notify,
        )
        session["state"] = "END"
        return f"END Logged: KES {data['amount']:.0f} owed by {data['customer_phone']}.", True

    session["state"] = "END"
    return "END Something went wrong. Please dial again.", True


def _render_invoices_menu(phone_number: str) -> str:
    db = SessionLocal()
    try:
        vendor = ledger.get_or_create_vendor(db, phone_number)
        pending = ledger.pending_invoices(db, vendor.id)
        if not pending:
            return "END No pending invoices."

        lines = ["CON Pending invoices:"]
        for inv in pending[:3]:
            days_left = max((inv.deadline - __import__("datetime").datetime.utcnow()).days, 0)
            lines.append(f"{inv.id}. {inv.buyer_name} KES {inv.amount:.0f} ({days_left}d left)")
        lines.append("Enter invoice number")
        return "\n".join(lines)
    finally:
        db.close()


def _invoices_menu(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]

    if "invoice_id" not in data:
        try:
            invoice_id = int(value)
        except ValueError:
            return "CON Enter a valid invoice number", False
        data["invoice_id"] = invoice_id
        return "CON 1. Accept 2. Dispute", False

    if value not in {"1", "2"}:
        return "CON Choose 1 for Accept or 2 for Dispute", False

    try:
        invoice = ledger.respond_to_invoice(db, data["invoice_id"], value == "1")
    except ValueError as exc:
        session["state"] = "END"
        return f"END {exc}", True

    session["state"] = "END"
    verdict = "accepted" if invoice.status.value == "accepted" else "disputed"
    return f"END Invoice {verdict}.", True


def _positive_float(value: str) -> float | None:
    try:
        number = float(value.strip())
    except (ValueError, AttributeError):
        return None
    return number if number > 0 else None
