"""Self-tests for the Finance Transaction Analyzer.

Run with:  python tests.py
Every check is an assert with a helpful message. The first failure stops the run.
"""

import os
import tempfile
import types

import analytics
import parser
from models import RecurringTransaction, Transaction


def make(amount, date="2026-08-01", description="Item", category="FOOD"):
    """Build a Transaction quickly for tests."""
    return Transaction(date, description, amount, category)


def write_file(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def is_rejected(line):
    """True if parse_row refuses the line with a ValueError."""
    try:
        parser.parse_row(line)
    except ValueError:
        return True
    return False


# ---------------------------------------------------------------- models.py
t = make(-450.50, description="Groceries")
assert t.is_income() is False, "is_income() should be False for a negative amount"
assert make(15000.0, category="INCOME").is_income() is True, "is_income() should be True for a positive amount"
assert make(0.0).is_income() is False, "is_income() should be False for a zero amount"
assert t.formatted() == "2026-08-01 Groceries -450.50 FOOD", "formatted() output wrong"
assert "Groceries" in str(t), "__str__ should include the description"

before = Transaction.count
make(10.0)
make(20.0)
assert Transaction.count == before + 2, "Transaction.count should go up by 1 per transaction"

r = RecurringTransaction("2026-08-01", "Rent", -5000.0, "HOUSING", "monthly")
assert isinstance(r, Transaction), "RecurringTransaction should inherit from Transaction"
assert r.interval == "monthly", "RecurringTransaction should store its interval"
assert "recurring" in str(r), "RecurringTransaction.__str__ should be overridden"

# --------------------------------------------------- parser.py: single rows
row = parser.parse_row("2026-08-01,Groceries,-450.50,food")
assert row.date == "2026-08-01", "valid row: wrong date"
assert row.amount == -450.50 and isinstance(row.amount, float), "valid row: amount should be a float"
assert row.category == "FOOD", "valid row: category should be upper-cased"
assert row.description == "Groceries", "valid row: wrong description"

slash = parser.parse_row("2026/08/03,Fuel,-600.00,TRANSPORT")
assert slash.date == "2026-08-03", "wrong date separator should be normalised, not rejected"

messy = parser.parse_row(" 2026-08-04 , Coffee Shop , -45.00 , FOOD ")
assert messy.date == "2026-08-04", "whitespace should be stripped from the date"
assert messy.description == "Coffee Shop", "whitespace should be stripped from the description"
assert messy.amount == -45.0, "whitespace should be stripped from the amount"
assert messy.category == "FOOD", "whitespace should be stripped from the category"

assert is_rejected("hello world"), "junk line should be rejected"
assert is_rejected("2026-08-05,Airtime"), "row with missing fields should be rejected"
assert is_rejected("2026-08-06,Netflix,abc,ENTERTAINMENT"), "non-numeric amount should be rejected"
assert is_rejected("2026-08-06,Netflix,,ENTERTAINMENT"), "empty amount should be rejected"
assert is_rejected("2026-08-06,Netflix,nan,ENTERTAINMENT"), "'nan' amount should be rejected"
assert is_rejected("2026-13-45,Bad date,10,FOOD"), "impossible date should be rejected"
assert is_rejected("2026-08-01,Too,many,fields,here"), "row with too many fields should be rejected"

# ---------------------------------------------- parser.py: whole-file loading
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "statement.txt")

    write_file(path, ["2026-08-01,Salary,15000.00,INCOME"])
    valid, rejected = parser.load_transactions(path)
    assert len(valid) == 1 and len(rejected) == 0, "clean file: 1 valid, 0 rejected expected"

    write_file(path, [
        "2026-08-01,Salary,15000.00,INCOME",
        "hello world",
        "2026-08-05,Airtime",
        "2026-08-06,Netflix,abc,ENTERTAINMENT",
        "2026-08-09,Rent,-5000.00,HOUSING",
    ])
    valid, rejected = parser.load_transactions(path)
    assert len(valid) == 2, "only the 2 good rows should load"
    assert len(rejected) == 3, "rejection count should go up for each bad row"
    assert all(v.description not in ("Airtime", "Netflix") for v in valid), "bad rows must not appear in the valid list"
    assert valid[-1].description == "Rent", "a bad row must not stop later rows loading"
    assert rejected[0].startswith("row 2"), "rejection should name the row number"
    assert "abc" in rejected[2], "rejection should give a clear reason for the bad amount"

    write_file(path, [])
    valid, rejected = parser.load_transactions(path)
    assert valid == [] and rejected == ["file is empty"], "empty file should be reported gracefully"

    write_file(path, ["   ", ""])
    valid, rejected = parser.load_transactions(path)
    assert valid == [] and rejected == ["file is empty"], "whitespace-only file should count as empty"

    missing = os.path.join(folder, "does_not_exist.txt")
    valid, rejected = parser.load_transactions(missing)
    assert valid == [] and "not found" in rejected[0], "missing file should be reported gracefully"

    sample = os.path.join(folder, "nested", "statement.txt")
    parser.generate_sample_file(sample)
    assert os.path.exists(sample), "generate_sample_file should create the file (and its folder)"
    with open(sample, encoding="utf-8") as f:
        assert len(f.read().splitlines()) >= 12, "sample file needs at least 12 rows"
    valid, rejected = parser.load_transactions(sample)
    assert len(valid) == 10, "sample file should give 10 valid transactions"
    assert len(rejected) == 3, "sample file should give 3 rejections"
    assert rejected[0].startswith("row 5") and rejected[2].startswith("row 7"), "sample rejections should name rows 5, 6 and 7"
    assert len(analytics.find_duplicates(valid)) == 1, "sample file should contain one planted duplicate"

# ------------------------------------------------------------- analytics.py
amounts = [make(100.0), make(-30.0), make(-20.5)]
gen = analytics.running_balance(amounts)
assert isinstance(gen, types.GeneratorType), "running_balance should be a generator"
assert list(gen) == [100.0, 70.0, 49.5], "running_balance wrong sequence"
assert list(analytics.running_balance(amounts, start=50.0)) == [150.0, 120.0, 99.5], "running_balance ignores the start value"
assert list(analytics.running_balance([])) == [], "running_balance of an empty list should yield nothing"

flag = analytics.make_flagger(1000)
assert flag(make(5000.0)) is True, "make_flagger(1000) should flag 5000"
assert flag(make(-5000.0)) is True, "make_flagger should flag large negative amounts too"
assert flag(make(50.0)) is False, "make_flagger(1000) should NOT flag 50"
assert analytics.make_flagger(10)(make(50.0)) is True, "each flagger should remember its own threshold"

a = make(-450.50, description="Groceries")
b = make(-600.0, description="Fuel", date="2026-08-03")
c = make(-450.50, description="Groceries")
dupes = analytics.find_duplicates([a, b, c])
assert len(dupes) == 1 and dupes[0] is c, "planted duplicate should be found"
assert analytics.find_duplicates([a, b]) == [], "clean list should have no duplicates"
assert analytics.find_duplicates([]) == [], "empty list should have no duplicates"

spread = [make(100.0)] * 10 + [make(10000.0, description="Huge")]
found = analytics.find_outliers(spread)
assert len(found) == 1 and found[0].description == "Huge", "extreme amount should be flagged as an outlier"
calm = [make(v) for v in (100.0, 110.0, 90.0, 105.0, 95.0)]
assert analytics.find_outliers(calm) == [], "a calm list should have no outliers"
assert analytics.find_outliers([make(5.0)]) == [], "a single transaction cannot have outliers"

totals = analytics.category_totals([
    make(1000.0, category="INCOME"),
    make(-200.0, category="FOOD"),
    make(-50.0, category="FOOD"),
    make(30.0, category="FOOD"),
])
assert totals["INCOME"]["income"] == 1000.0, "INCOME income total wrong"
assert totals["FOOD"]["expense"] == -250.0, "FOOD expense total wrong"
assert totals["FOOD"]["income"] == 30.0, "FOOD income total wrong"
assert totals["FOOD"]["net"] == -220.0, "FOOD net total wrong"

mismatched = analytics.find_inconsistent([
    make(-200.0, description="Refund", category="INCOME"),
    make(350.0, description="Restaurant", category="FOOD"),
    make(-45.0, description="Coffee", category="FOOD"),
    make(500.0, description="Bonus", category="INCOME"),
])
assert [m.description for m in mismatched] == ["Refund", "Restaurant"], "sign/category mismatches wrong"

print("All tests passed")