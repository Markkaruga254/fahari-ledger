"""
Fire the simulated eTIMS buyer-initiated invoice event on command, so it can
be triggered live during the demo rather than waiting on a timer:

    python -m scripts.trigger_etims_event --phone +254700000000 \
        --buyer "Nyali Hotel Supplies" --amount 4200
"""
import argparse

from app.etims_sim.event_generator import fire_invoice_event


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phone", required=True)
    parser.add_argument("--buyer", default="Nyali Hotel Supplies")
    parser.add_argument("--amount", type=float, default=4200)
    parser.add_argument("--deadline-days", type=int, default=29)
    args = parser.parse_args()

    invoice = fire_invoice_event(args.phone, args.buyer, args.amount, args.deadline_days)
    print(f"Fired invoice #{invoice.id}: {args.buyer} KES {args.amount} for {args.phone}")


if __name__ == "__main__":
    main()
