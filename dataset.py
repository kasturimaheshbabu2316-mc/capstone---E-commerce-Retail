"""
dataset.py - Deterministic Synthetic Order Dataset Generator
Track: E-Commerce & Retail (Nykaa)
Task 1: Seeded dataset generator with invariant validation.
"""

from typing import List, Dict, Any, Optional
import os
import random

# Controlled Vocabularies
CATEGORIES = [
    "Apparel",
    "Electronics",
    "Home",
    "Footwear",
    "Beauty",
]

ORDER_STATUSES = [
    "Placed",
    "Shipped",
    "Delivered",
    "Returned",
    "Refunded",
]

# Realistic retail price bands in INR for Nykaa catalog
RETAIL_PRICE_BOUNDS: Dict[str, tuple] = {
    "Beauty": (299.0, 4999.0),          # Lipsticks, luxury serums, perfumes
    "Apparel": (799.0, 6999.0),         # Kurtas, dresses, activewear
    "Footwear": (899.0, 8499.0),        # Flats, heels, lifestyle sneakers
    "Home": (499.0, 5499.0),            # Aromatherapy, scented candles, organisers
    "Electronics": (1499.0, 18999.0),   # Hair straighteners, multi-stylers, epilators
}


class OrderRecord:
    """Represents a single immutable Nykaa e-commerce order record."""

    def __init__(
        self,
        record_id: str,
        category: str,
        status: str,
        order_value_inr: float,
        days_since_created: int,
        delayed_shipment: bool,
    ):
        self.record_id = record_id
        self.category = category
        self.status = status
        self.order_value_inr = round(float(order_value_inr), 2)
        self.days_since_created = int(days_since_created)
        self.delayed_shipment = bool(delayed_shipment)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "category": self.category,
            "status": self.status,
            "order_value_inr": self.order_value_inr,
            "days_since_created": self.days_since_created,
            "delayed_shipment": self.delayed_shipment,
        }

    def __repr__(self) -> str:
        delay_flag = "DELAYED" if self.delayed_shipment else "ON_TIME"
        return (
            f"OrderRecord({self.record_id}, {self.category}, {self.status}, "
            f"₹{self.order_value_inr:,.2f}, {self.days_since_created}d, {delay_flag})"
        )


def generate_orders(
    seed: int = 42,
    total_records: int = 45,
    target_delay_prob: float = 0.20,
) -> List[Dict[str, Any]]:
    """
    Deterministically generates synthetic orders meeting all Nykaa capstone invariants:
    - Invariant 1: Total records >= 40.
    - Invariant 2: Every category has >= 3 records.
    - Invariant 3: Every status has >= 1 record.
    - Invariant 4: Delayed shipment proportion strictly in [0.10, 0.30] (10% to 30%).
    - Invariant 5: Order values stay within retail bands (INR 299 to INR 18,999).
    """
    if total_records < 40:
        raise ValueError("Total records must be >= 40 according to specification.")

    rng = random.Random(seed)
    records: List[Dict[str, Any]] = []
    rec_counter = 1001

    # Guarantee baseline coverage: all 5 categories >= 3 records, all 5 statuses >= 1 record
    for cat_idx, category in enumerate(CATEGORIES):
        min_bound, max_bound = RETAIL_PRICE_BOUNDS[category]
        for repeat_idx in range(3):
            status = ORDER_STATUSES[(cat_idx * 3 + repeat_idx) % len(ORDER_STATUSES)]
            order_val = rng.uniform(min_bound, max_bound)
            days = rng.randint(0, 30)
            is_delayed = rng.random() < target_delay_prob

            rec = OrderRecord(
                record_id=f"NYK-{rec_counter}",
                category=category,
                status=status,
                order_value_inr=order_val,
                days_since_created=days,
                delayed_shipment=is_delayed,
            )
            records.append(rec.to_dict())
            rec_counter += 1

    # Fill remaining records up to total_records
    remaining = total_records - len(records)
    for _ in range(remaining):
        category = rng.choice(CATEGORIES)
        status = rng.choice(ORDER_STATUSES)
        min_bound, max_bound = RETAIL_PRICE_BOUNDS[category]
        order_val = rng.uniform(min_bound, max_bound)
        days = rng.randint(0, 30)
        is_delayed = rng.random() < target_delay_prob

        rec = OrderRecord(
            record_id=f"NYK-{rec_counter}",
            category=category,
            status=status,
            order_value_inr=order_val,
            days_since_created=days,
            delayed_shipment=is_delayed,
        )
        records.append(rec.to_dict())
        rec_counter += 1

    # Check delayed_shipment proportion invariant [0.10, 0.30]
    delay_count = sum(1 for r in records if r["delayed_shipment"])
    delay_rate = delay_count / len(records)

    if not (0.10 <= delay_rate <= 0.30):
        # Deterministically step target probability to converge within bounds
        adjusted_target = min(max(0.15, target_delay_prob), 0.25)
        return generate_orders(
            seed=seed + 1,
            total_records=total_records,
            target_delay_prob=adjusted_target,
        )

    # Invariant Verification Assertions
    assert len(records) >= 40, f"Total records {len(records)} < 40"
    for cat in CATEGORIES:
        count = sum(1 for r in records if r["category"] == cat)
        assert count >= 3, f"Invariant violated: category '{cat}' has only {count} records."

    for st in ORDER_STATUSES:
        count = sum(1 for r in records if r["status"] == st)
        assert count >= 1, f"Invariant violated: status '{st}' has only {count} records."

    assert 0.10 <= delay_rate <= 0.30, (
        f"Invariant violated: delay rate {delay_rate:.2%} outside [10%, 30%]."
    )

    return records


# Seeded production dataset instance
ORDERS: List[Dict[str, Any]] = generate_orders(seed=42, total_records=45)

# Fast O(1) indexed dictionary by record_id
ORDERS_BY_ID: Dict[str, Dict[str, Any]] = {r["record_id"]: r for r in ORDERS}


def get_all_orders() -> List[Dict[str, Any]]:
    """Returns the immutable list of all seeded orders."""
    return list(ORDERS)


def get_order_by_id(record_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """O(1) transactional lookup for order records by ID."""
    if not record_id:
        return None
    return ORDERS_BY_ID.get(str(record_id).strip().upper())


def compute_escalation_score(order: Dict[str, Any]) -> float:
    """
    Computes parametric escalation score S_esc in [0.0, 1.0]:
    S_esc = w1 * delayed_shipment + w2 * (days_since_created / 30)
    w1 = 0.60 (delay impact factor)
    w2 = 0.40 (aging factor)
    Clamped strictly within [0.0, 1.0] to satisfy EC-07.
    """
    if not isinstance(order, dict):
        return 0.0
    w1 = 0.60
    w2 = 0.40
    delay_factor = 1.0 if order.get("delayed_shipment", False) else 0.0
    try:
        raw_days = float(order.get("days_since_created", 0))
    except (ValueError, TypeError):
        raw_days = 0.0
    aging_factor = min(max(raw_days / 30.0, 0.0), 1.0)
    return round(w1 * delay_factor + w2 * aging_factor, 4)


def check_order_status(record_id: Optional[str]) -> Dict[str, Any]:
    """
    O(1) transactional lookup for Nykaa orders with continuous escalation scoring.
    Escalation threshold: S_esc >= 0.65
    Implements EC-06 (safe lookup without uncaught exceptions on unseeded IDs).
    """
    if not record_id:
        normalized_id = ""
    else:
        normalized_id = str(record_id).strip().upper()

    order = ORDERS_BY_ID.get(normalized_id)

    if not order:
        return {
            "found": False,
            "record_id": normalized_id,
            "error": f"Order ID '{normalized_id}' not found in Nykaa order registry.",
            "escalation_score": 0.0,
            "escalation_triggered": False,
        }

    s_esc = compute_escalation_score(order)
    is_escalated = s_esc >= 0.65

    return {
        "found": True,
        "record_id": order["record_id"],
        "category": order["category"],
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "days_since_created": order["days_since_created"],
        "delayed_shipment": order["delayed_shipment"],
        "escalation_score": s_esc,
        "escalation_triggered": is_escalated,
    }


def generate_task_01_verification() -> str:
    """Produces the formatted validation transcript for Task 1."""
    total = len(ORDERS)
    delay_count = sum(1 for r in ORDERS if r["delayed_shipment"])
    delay_pct = (delay_count / total) * 100

    lines = [
        "================================================================================",
        "TASK 1 VERIFICATION: SEEDED SYNTHETIC ORDER DATASET (NYKAA TRACK)",
        "================================================================================",
        f"Seed: 42",
        f"Total Records Generated: {total} (Requirement: >= 40) -> PASS",
        f"Delayed Shipments Count: {delay_count}/{total} ({delay_pct:.2f}%) (Requirement: 10% - 30%) -> PASS",
        "",
        "--- CATEGORY DISTRIBUTION (Requirement: >= 3 per category) ---",
    ]

    for cat in CATEGORIES:
        count = sum(1 for r in ORDERS if r["category"] == cat)
        price_range = [r["order_value_inr"] for r in ORDERS if r["category"] == cat]
        min_p, max_p = min(price_range), max(price_range)
        lines.append(f"  - {cat:<12}: {count:>2} orders | Range: ₹{min_p:,.2f} to ₹{max_p:,.2f} -> PASS")

    lines.append("")
    lines.append("--- STATUS DISTRIBUTION (Requirement: >= 1 per status) ---")
    for st in ORDER_STATUSES:
        count = sum(1 for r in ORDERS if r["status"] == st)
        lines.append(f"  - {st:<12}: {count:>2} orders -> PASS")

    lines.append("")
    lines.append("--- ESCALATION ENGINE SAMPLING (Threshold: S_esc >= 0.65) ---")
    for sample_id in ["NYK-1001", "NYK-1002", "NYK-1003", "NYK-1015", "NYK-1025"]:
        res = check_order_status(sample_id)
        lines.append(
            f"  {res['record_id']}: Status={res['status']}, Days={res['days_since_created']}, "
            f"Delayed={res['delayed_shipment']} -> S_esc={res['escalation_score']:.4f} "
            f"[Escalated={res['escalation_triggered']}]"
        )

    lines.append("================================================================================")
    lines.append("ALL TASK 1 INVARIANTS DETERMINISTICALLY VERIFIED AND SATISFIED.")
    lines.append("================================================================================")
    return "\n".join(lines)


if __name__ == "__main__":
    transcript = generate_task_01_verification()
    print(transcript)

    # Save verification transcript
    os.makedirs("transcripts", exist_ok=True)
    with open(os.path.join("transcripts", "task_01_dataset.txt"), "w", encoding="utf-8") as f:
        f.write(transcript + "\n")
    print("\nVerification transcript written to transcripts/task_01_dataset.txt")
