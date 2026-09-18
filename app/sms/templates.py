def overstock_nudge(item: str, remaining_qty: float, unit: str = "kg") -> str:
    return f"You have {remaining_qty:.1f}{unit} {item} left and it's late in the day. Discount now or risk a loss tomorrow."


def debt_reminder(vendor_name: str, amount: float, item: str | None) -> str:
    item_part = f" for {item}" if item else ""
    return f"You owe {vendor_name} KES {amount:.0f}{item_part}, logged today via Fahari Ledger."


def etims_invoice_alert(buyer_name: str, amount: float, days_left: int) -> str:
    return (
        f"{buyer_name} sent an invoice for KES {amount:.0f}. "
        f"Reply 1 to accept, 2 to dispute. {days_left} days left before it auto-rejects "
        f"and you may lose this buyer."
    )


def end_of_day_summary(total_sales: float, total_owed: float, sale_count: int, pending_invoices: int) -> str:
    msg = (
        f"Fahari Ledger — end of day: KES {total_sales:.0f} sold across {sale_count} sales, "
        f"KES {total_owed:.0f} owed to you."
    )
    if pending_invoices:
        msg += f" {pending_invoices} invoice(s) awaiting your response."
    return msg
