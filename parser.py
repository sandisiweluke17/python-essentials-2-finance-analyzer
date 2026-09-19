"""File reading and row cleaning/validation."""

import os

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
