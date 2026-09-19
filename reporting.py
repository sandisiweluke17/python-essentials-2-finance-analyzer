"""Summary report and environment/date stamp."""

import os
import platform
from datetime import datetime

import analytics

DATA_DIR = "data"
REPORT_PATH = os.path.join(DATA_DIR, "report.txt")
LOG_PATH = os.path.join(DATA_DIR, "analyzer.log")


def _ensure_folder(path):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)  # data/ may not exist on a fresh clone


def environment_stamp():
    """One line with the date/time, operating system, Python version and folder."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"Generated: {now} | OS: {platform.system()} {platform.release()} "
        f"| Python: {platform.python_version()} | Folder: {os.getcwd()}"
    )


def monthly_summary(transactions, rejections=None, path=REPORT_PATH):
    """Write the summary report to `path` and return the report text."""
    rejections = rejections or []

    months = {}
    for t in transactions:
        month = t.date[:7]  # YYYY-MM
        entry = months.setdefault(month, {"income": 0.0, "expense": 0.0})
        if t.amount > 0:
            entry["income"] += t.amount
        else:
            entry["expense"] += t.amount

    duplicates = analytics.find_duplicates(transactions)
    outliers = analytics.find_outliers(transactions)
    inconsistent = analytics.find_inconsistent(transactions)

    lines = ["FINANCE TRANSACTION ANALYZER - MONTHLY SUMMARY", environment_stamp(), ""]

    lines.append("MONTHLY TOTALS")
    if not months:
        lines.append("  (no valid transactions)")
    for month in sorted(months):
        income = months[month]["income"]
        expense = months[month]["expense"]
        lines.append(
            f"  {month}: income {income:,.2f} | expenses {expense:,.2f} | net {income + expense:,.2f}"
        )

    lines += ["", "CATEGORY BREAKDOWN"]
    for category, v in sorted(analytics.category_totals(transactions).items()):
        lines.append(
            f"  {category:<15} income {v['income']:>12,.2f}  "
            f"expenses {v['expense']:>12,.2f}  net {v['net']:>12,.2f}"
        )

    lines += ["", "DATA QUALITY"]
    lines.append(f"  Valid transactions: {len(transactions)}")
    lines.append(f"  Rejected rows: {len(rejections)}")
    for reason in rejections:
        lines.append(f"    - {reason}")
    lines.append(f"  Duplicates: {len(duplicates)}")
    for t in duplicates:
        lines.append(f"    - {t.formatted()}")
    lines.append(f"  Outliers: {len(outliers)}")
    for t in outliers:
        lines.append(f"    - {t.formatted()}")
    lines.append(f"  Inconsistent (sign vs category): {len(inconsistent)}")
    for t in inconsistent:
        lines.append(f"    - {t.formatted()}")

    text = "\n".join(lines) + "\n"

    _ensure_folder(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def log_run(message, path=LOG_PATH):
    """Append one timestamped line to the run log (never overwrites)."""
    _ensure_folder(path)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{stamp} | {message}\n")