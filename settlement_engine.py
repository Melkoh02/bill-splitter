from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict


@dataclass(frozen=True)
class Item:
    name: str
    cost: int
    shared_by: Tuple[str, ...]
    paid_by: str  # "tab" or a participant name (individual pay)


def parse_time(hhmm: str, base_date: datetime) -> datetime:
    t = datetime.strptime(hhmm, "%H:%M")
    return base_date.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)


def round_and_fix_total(shares: Dict[str, float], total: int, fix_person: str) -> Dict[str, int]:
    rounded = {p: int(round(v)) for p, v in shares.items()}
    diff = total - sum(rounded.values())
    rounded[fix_person] += diff
    return rounded


def add_item_reimbursements(
        reimbursements: Dict[str, Dict[str, int]],
        item: Item,
        drift_person: str,
) -> None:
    """
    Create reimbursements[debtor][creditor] += amount for individually-paid items.
    Any rounding drift is assigned to drift_person, even if not in shared_by.
    """
    assert item.paid_by != "tab"

    n = len(item.shared_by)
    per = item.cost / n
    rounded_shares = {p: int(round(per)) for p in item.shared_by}
    diff = item.cost - sum(rounded_shares.values())

    if diff != 0:
        if drift_person in rounded_shares:
            rounded_shares[drift_person] += diff
        else:
            rounded_shares[drift_person] = diff

    payer = item.paid_by
    for person, share in rounded_shares.items():
        if person == payer:
            continue
        reimbursements[person][payer] += share


def main() -> None:
    people = ["Sebas", "Melkoh", "Benja", "Dave", "Kevin", "Mathi"]
    drift_person = "Melkoh"
    payer_X = "X"  # detached payer of venue (pool + tab only)

    arrivals = {
        "Sebas": "18:15",
        "Melkoh": "18:15",
        "Benja": "19:00",
        "Dave": "19:00",
        "Kevin": "19:40",
        "Mathi": "20:30",
    }

    departures = {
        "Dave": "20:00",
        "Benja": "22:50",
        "Sebas": "23:30",
        "Melkoh": "23:30",
        "Mathi": "23:30",
        "Kevin": "23:30",
    }

    grand_total_venue = 675_000  # X paid this (venue only)
    pool_price_per_hour_per_table = 40_000
    number_of_tables = 2

    items: List[Item] = [
        # On tab (part of venue bill)
        Item("fernet", 20_000, ("Sebas", "Melkoh"), "tab"),
        Item("3 beers", 20_000, ("Melkoh",), "tab"),
        Item("pizza(tab)", 50_000, ("Dave", "Melkoh", "Benja", "Sebas"), "tab"),
        Item("picadas", 55_000, ("Dave", "Melkoh", "Benja"), "tab"),
        Item("coke(Benja)", 10_000, ("Benja",), "tab"),
        Item("coke(Melkoh)", 10_000, ("Melkoh",), "tab"),
        Item("water(Sebas)", 10_000, ("Sebas",), "tab"),
        Item("pizza(tab2)", 40_000, ("Melkoh", "Mathi", "Benja", "Kevin"), "tab"),

        # Individually paid (NOT part of venue total)
        Item("fries", 20_000, ("Dave", "Melkoh", "Benja", "Sebas"), "Dave"),
        Item("pizza(Kevin paid)", 50_000, ("Melkoh", "Mathi", "Benja", "Kevin"), "Kevin"),
    ]

    base_date = datetime(2026, 1, 30)

    # Durations
    durations_min: Dict[str, float] = {}
    for p in people:
        a = parse_time(arrivals[p], base_date)
        d = parse_time(departures[p], base_date)
        if d < a:
            d += timedelta(days=1)
        durations_min[p] = (d - a).total_seconds() / 60.0
    total_presence_min = sum(durations_min.values())

    # Pool total (earliest arrival -> latest departure)
    session_start = min(parse_time(arrivals[p], base_date) for p in people)
    session_end = max(parse_time(departures[p], base_date) for p in people)
    if session_end < session_start:
        session_end += timedelta(days=1)

    session_minutes = (session_end - session_start).total_seconds() / 60.0
    pool_total = int(round((pool_price_per_hour_per_table * number_of_tables) * (session_minutes / 60.0)))

    pool_share = {p: pool_total * (durations_min[p] / total_presence_min) for p in people}

    # Tab shares + reimbursements
    tab_share = {p: 0.0 for p in people}
    tab_items_total = 0

    reimbursements: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for it in items:
        if it.paid_by == "tab":
            tab_items_total += it.cost
            per = it.cost / len(it.shared_by)
            for p in it.shared_by:
                tab_share[p] += per
        else:
            add_item_reimbursements(reimbursements, it, drift_person=drift_person)

    # Venue base shares (pool + tab)
    venue_base = {p: pool_share[p] + tab_share[p] for p in people}
    known_venue_total = pool_total + tab_items_total

    # Unknown handling (venue only)
    venue_delta = grand_total_venue - known_venue_total
    venue_adjust = {p: 0.0 for p in people}
    if venue_delta > 0:
        venue_adjust[drift_person] += venue_delta
    elif venue_delta < 0:
        per_discount = venue_delta / len(people)
        for p in people:
            venue_adjust[p] += per_discount

    venue_share_float = {p: venue_base[p] + venue_adjust[p] for p in people}
    final_venue_share = round_and_fix_total(venue_share_float, grand_total_venue, fix_person=drift_person)

    # Fold reimbursements into the single list to X:
    # debtor->creditor A becomes:
    #   debtor pays +A to X, creditor pays -A to X
    combined_to_X = dict(final_venue_share)
    for debtor, creditors in reimbursements.items():
        for creditor, amt in creditors.items():
            if amt == 0:
                continue
            combined_to_X[debtor] += amt
            combined_to_X[creditor] -= amt

    # Final rounding drift <- drift_person is the fallback, they pay more
    combined_to_X = round_and_fix_total({p: float(v) for p, v in combined_to_X.items()},
                                        grand_total_venue, fix_person=drift_person)

    # Output
    print("== Single list ==")
    for p in people:
        print(f"{p:6s} -> {payer_X}: {combined_to_X[p]:,}")
    print(f"Sum total: {sum(combined_to_X.values()):,} (should equal {grand_total_venue:,})")


if __name__ == "__main__":
    main()
