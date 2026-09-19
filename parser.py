"""File reading and row cleaning/validation."""

import math
import os
from datetime import datetime

from models import Transaction

DATA_DIR = "data"
SAMPLE_PATH = os.path.join(DATA_DIR, "statement.txt")

# Each line is deliberately messy. The comment beside it names the edge case.
SAMPLE_LINES = [
    "2026-08-01,Salary,15000.00,INCOME",             # clean valid row
    "2026-08-01,Groceries,-450.50,FOOD",             # clean valid row (duplicated below)
    "2026/08/03,Fuel,-600.00,TRANSPORT",             # wrong date separator -> normalise
    " 2026-08-04 , Coffee Shop , -45.00 , FOOD ",    # whitespace everywhere -> strip
    "2026-08-05,Airtime",                            # missing fields -> reject
    "hello world",                                   # junk line -> reject
    "2026-08-06,Netflix,abc,ENTERTAINMENT",          # non-numeric amount -> reject
    "2026-08-07,Refund,-200.00,INCOME",              # negative amount tagged income -> inconsistent
    "2026-08-08,Restaurant,350.00,FOOD",             # positive amount tagged expense -> inconsistent
    "2026-08-09,Rent,-5000.00,HOUSING",              # clean valid row
    "2026-08-10,Electricity,-800.00,UTILITIES",      # clean valid row
    "2026-08-01,Groceries,-450.50,FOOD",             # exact duplicate of row 2
    "2026-08-12,Laptop,-25000.00,SHOPPING",          # large value -> outlier candidate
]


def generate_sample_file(path=SAMPLE_PATH):
    """Write a deliberately messy statement file and return its path."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)  # data/ may not exist on a fresh clone
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(SAMPLE_LINES) + "\n")
    return path


def normalise_date(text):
    """Return a date as YYYY-MM-DD, accepting '/' or '-' separators."""
    cleaned = text.strip().replace("/", "-")
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"invalid date '{text.strip()}'")


def parse_row(line):
    """Turn one raw line into a Transaction, or raise ValueError with the reason."""
    fields = [part.strip() for part in line.split(",")]
    if len(fields) < 4:
        raise ValueError("not enough fields")
    if len(fields) > 4:
        raise ValueError("too many fields")

    date_text, description, amount_text, category = fields

    date = normalise_date(date_text)

    if not description:
        raise ValueError("empty description")
    if not category:
        raise ValueError("empty category")

    try:
        amount = float(amount_text)
    except ValueError:
        raise ValueError(f"amount '{amount_text}' is not a number")
    if not math.isfinite(amount):
        raise ValueError(f"amount '{amount_text}' is not a valid number")

    return Transaction(date, description, amount, category.upper())


def load_transactions(path=SAMPLE_PATH):
    """Return (valid_transactions, rejection_reasons). Never crashes on bad data."""
    transactions = []
    rejections = []

    if not os.path.exists(path):
        return transactions, [f"file not found: {path}"]

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError as error:
        return transactions, [f"could not read file: {error}"]

    if not any(line.strip() for line in lines):
        return transactions, ["file is empty"]

    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue  # ignore blank lines
        try:
            transactions.append(parse_row(line))
        except ValueError as error:
            rejections.append(f"row {number}: {error}")

    return transactions, rejections
