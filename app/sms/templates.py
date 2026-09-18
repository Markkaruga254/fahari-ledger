def overstock_nudge(item: str, remaining_qty: float, unit: str = "kg") -> str:
    return (
        f"Fahari alert: {remaining_qty:.1f}{unit} {item} remains late in the day. "
        "Consider discounting to reduce today's loss."
    )


def debt_reminder(vendor_name: str, amount: float, item: str | None) -> str:
    item_part = f" for {item}" if item else ""
    return f"You owe {vendor_name} KES {amount:.0f}{item_part}, logged today via Fahari Ledger."


def etims_invoice_alert(buyer_name: str, amount: float, days_left: int) -> str:
    return (
        f"Fahari: {buyer_name} sent an invoice for KES {amount:.0f}. "
        f"Use USSD to accept or dispute. {days_left} days remain."
    )


def end_of_day_summary(
    total_sales: float,
    total_owed: float,
    sale_count: int,
    pending_invoices: int,
    items_remaining: dict[str, float] | None = None,
) -> str:
    msg = (
        f"Fahari Ledger — end of day: KES {total_sales:.0f} sold across {sale_count} sales, "
        f"KES {total_owed:.0f} owed to you."
    )

    if items_remaining:
        stock = ", ".join(
            f"{item} {qty:g}kg"
            for item, qty in items_remaining.items()
            if qty > 0
        )
        if stock:
            msg += f" Stock remaining: {stock}."

    if pending_invoices:
        msg += f" {pending_invoices} invoice(s) awaiting your response."

    return msg
