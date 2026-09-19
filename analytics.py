"""Ledger generator, closures, duplicates, outliers."""

import statistics


def running_balance(transactions, start=0.0):
    """Generator: yield the balance after each transaction, in order."""
    balance = start
    for t in transactions:
        balance += t.amount
        yield balance


def make_flagger(threshold):
    """Closure: return a function that flags amounts beyond the remembered threshold."""
    def flag(transaction):
        return abs(transaction.amount) > threshold
    return flag


def _signature(t):
    return (t.date, t.description, t.amount, t.category)


def find_duplicates(transactions):
    """Return every repeat of an exact duplicate (the first copy is not included)."""
    seen = set()
    duplicates = []
    for t in transactions:
        sig = _signature(t)
        if sig in seen:
            duplicates.append(t)
        else:
            seen.add(sig)
    return duplicates


def find_outliers(transactions):
    """Return transactions more than 2 standard deviations from the mean amount."""
    if len(transactions) < 2:
        return []
    amounts = [t.amount for t in transactions]
    mean = statistics.mean(amounts)
    spread = statistics.stdev(amounts)
    if spread == 0:
        return []
    return [t for t in transactions if abs(t.amount - mean) > 2 * spread]


def category_totals(transactions):
    """Return {category: {'income': x, 'expense': y, 'net': z}}."""
    totals = {}
    for t in transactions:
        entry = totals.setdefault(t.category, {"income": 0.0, "expense": 0.0, "net": 0.0})
        if t.amount > 0:
            entry["income"] += t.amount
        else:
            entry["expense"] += t.amount
        entry["net"] += t.amount
    return totals


def find_inconsistent(transactions):
    """Return transactions whose sign disagrees with their category.

    INCOME with a negative amount, or any other category with a positive amount.
    """
    flagged = []
    for t in transactions:
        if t.category == "INCOME" and t.amount < 0:
            flagged.append(t)
        elif t.category != "INCOME" and t.amount > 0:
            flagged.append(t)
    return flagged
