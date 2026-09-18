"""
The USSD menu tree. See docs/ussd-menu-tree.md for the screen-by-screen spec
this implements. Every handler returns (response_text, end_session: bool).
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

        # Fallback — unknown state, reset
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
        return "CON Enter item name (e.g. tomato)", False
    if choice == "2":
        session["state"] = "SALE_ITEM"
        return "CON Enter item name (e.g. tomato)", False
    if choice == "3":
        session["state"] = "DEBT_CUSTOMER"
        return "CON Enter customer phone number", False
    if choice == "4":
        # handled inline, no DB session held open across the loop for this simple case
        db = SessionLocal()
        try:
            vendor = ledger.get_or_create_vendor(db, session.get("phone_number", ""))
            summary = ledger.today_summary(db, vendor.id)
            session["state"] = "END"
            return (
                f"END Today: KES {summary['total_sales']:.0f} sold, "
                f"KES {summary['total_owed_to_vendor']:.0f} owed to you, "
                f"{summary['sale_count']} sales logged."
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
        data["item"] = value.strip().lower()
        session["state"] = "PURCHASE_QTY"
        return "CON Enter quantity in kg (e.g. 10)", False
    if session["state"] == "PURCHASE_QTY":
        data["quantity"] = _to_float(value)
        session["state"] = "PURCHASE_COST"
        return "CON Enter total cost in KES (e.g. 500)", False
    if session["state"] == "PURCHASE_COST":
        data["cost"] = _to_float(value)
        ledger.log_purchase(db, phone_number, data["item"], data["quantity"], data["cost"])
        session["state"] = "END"
        return (
            f"END Logged: bought {data['quantity']}kg {data['item']} for KES {data['cost']:.0f}."
        ), True
    session["state"] = "END"
    return "END Something went wrong. Please dial again.", True


def _sale_flow(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]
    if session["state"] == "SALE_ITEM":
        data["item"] = value.strip().lower()
        session["state"] = "SALE_QTY"
        return "CON Enter quantity in kg (e.g. 2)", False
    if session["state"] == "SALE_QTY":
        data["quantity"] = _to_float(value)
        session["state"] = "SALE_PRICE"
        return "CON Enter total price in KES (e.g. 200)", False
    if session["state"] == "SALE_PRICE":
        data["price"] = _to_float(value)
        ledger.log_sale(db, phone_number, data["item"], data["quantity"], data["price"])
        session["state"] = "END"
        return (
            f"END Logged: sold {data['quantity']}kg {data['item']} for KES {data['price']:.0f}."
        ), True
    session["state"] = "END"
    return "END Something went wrong. Please dial again.", True


def _debt_flow(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]
    if session["state"] == "DEBT_CUSTOMER":
        data["customer_phone"] = value.strip()
        session["state"] = "DEBT_ITEM"
        return "CON Enter item (or 0 to skip)", False
    if session["state"] == "DEBT_ITEM":
        data["item"] = None if value.strip() == "0" else value.strip()
        session["state"] = "DEBT_AMOUNT"
        return "CON Enter amount owed in KES", False
    if session["state"] == "DEBT_AMOUNT":
        data["amount"] = _to_float(value)
        session["state"] = "DEBT_NOTIFY"
        return "CON Notify the customer by SMS? 1. Yes 2. No", False
    if session["state"] == "DEBT_NOTIFY":
        notify = value == "1"
        ledger.log_debt(db, phone_number, data["customer_phone"], data.get("item"), data["amount"], notify)
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
        lines = [f"CON Pending invoices:"]
        for inv in pending[:3]:
            days_left = max((inv.deadline - inv.created_at).days, 0)
            lines.append(f"{inv.id}. {inv.buyer_name} KES {inv.amount:.0f} ({days_left}d left)")
        lines.append("Reply with invoice number, then 1=accept 2=dispute")
        return "\n".join(lines)
    finally:
        db.close()


def _invoices_menu(db, session, phone_number, value) -> tuple[str, bool]:
    data = session["data"]
    if "invoice_id" not in data:
        try:
            data["invoice_id"] = int(value)
        except ValueError:
            session["state"] = "END"
            return "END Invalid invoice number.", True
        return "CON 1. Accept 2. Dispute", False
    accept = value == "1"
    ledger.respond_to_invoice(db, data["invoice_id"], accept)
    session["state"] = "END"
    verdict = "accepted" if accept else "disputed"
    return f"END Invoice {verdict}.", True


def _to_float(value: str) -> float:
    try:
        return float(value.strip())
    except ValueError:
        return 0.0
