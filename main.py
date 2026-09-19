"""Menu for the Finance Transaction Analyzer."""

import os
import subprocess
import sys

import analytics
import parser
import reporting

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MENU = """
===== FINANCE TRANSACTION ANALYZER =====
1. Generate a messy sample statement file
2. Load & validate transactions (reject bad rows)
3. Show running balance (ledger)
4. Category breakdown (income vs expense by tag)
5. Detect duplicate transactions
6. Flag unusual transactions (statistical outliers)
7. Monthly summary report -> file
8. Run self-tests (tests.py)
9. Exit
"""

state = {"transactions": [], "rejections": [], "loaded": False}


def require_loaded(allow_empty=False):
    """Check that option 2 has been run (and found something to work with)."""
    if not state["loaded"]:
        print("No transactions loaded yet. Choose option 2 first.")
        return False
    if not state["transactions"] and not allow_empty:
        print("There are no valid transactions to work with.")
        return False
    return True


def option_generate():
    path = parser.generate_sample_file()
    print(f"Messy sample statement written to {path}")
    reporting.log_run("generated sample file")


def option_load():
    raw = input(f"File to load [{parser.SAMPLE_PATH}]: ").strip().strip('"')
    path = raw or parser.SAMPLE_PATH
    transactions, rejections = parser.load_transactions(path)
    state["transactions"] = transactions
    state["rejections"] = rejections
    state["loaded"] = True
    print(f"Loaded {len(transactions)} valid transaction(s).")
    print(f"Rejected {len(rejections)} problem(s):")
    for reason in rejections:
        print(f"  - {reason}")
    reporting.log_run(f"loaded {path}: {len(transactions)} valid, {len(rejections)} rejected")


def option_ledger():
    if not require_loaded():
        return
    balances = analytics.running_balance(state["transactions"])
    print(f"{'Date':<12}{'Description':<22}{'Amount':>12}{'Balance':>14}")
    for t, balance in zip(state["transactions"], balances):
        print(f"{t.date:<12}{t.description:<22}{t.amount:>12,.2f}{balance:>14,.2f}")
    reporting.log_run("showed ledger")


def option_categories():
    if not require_loaded():
        return
    print(f"{'Category':<16}{'Income':>14}{'Expenses':>14}{'Net':>14}")
    for category, v in sorted(analytics.category_totals(state["transactions"]).items()):
        print(f"{category:<16}{v['income']:>14,.2f}{v['expense']:>14,.2f}{v['net']:>14,.2f}")
    inconsistent = analytics.find_inconsistent(state["transactions"])
    if inconsistent:
        print("\nInconsistent (sign does not match category):")
        for t in inconsistent:
            print(f"  - {t.formatted()}")
    reporting.log_run("showed category breakdown")


def option_duplicates():
    if not require_loaded():
        return
    duplicates = analytics.find_duplicates(state["transactions"])
    if not duplicates:
        print("No duplicate transactions found.")
    else:
        print(f"Found {len(duplicates)} duplicate(s):")
        for t in duplicates:
            print(f"  - {t.formatted()}")
    reporting.log_run(f"duplicate check: {len(duplicates)} found")


def option_outliers():
    if not require_loaded():
        return
    outliers = analytics.find_outliers(state["transactions"])
    if not outliers:
        print("No statistical outliers found.")
    else:
        print(f"Found {len(outliers)} outlier(s) (more than 2 standard deviations from the mean):")
        for t in outliers:
            print(f"  - {t.formatted()}")
    raw = input("Optional: amount threshold to flag large transactions (Enter to skip): ").strip()
    if raw:
        try:
            flag = analytics.make_flagger(float(raw))
        except ValueError:
            print("That is not a number, skipping the threshold check.")
        else:
            flagged = [t for t in state["transactions"] if flag(t)]
            print(f"{len(flagged)} transaction(s) above {raw}:")
            for t in flagged:
                print(f"  - {t.formatted()}")
    reporting.log_run(f"outlier check: {len(outliers)} found")


def option_report():
    if not require_loaded(allow_empty=True):
        return
    reporting.monthly_summary(state["transactions"], state["rejections"])
    print(f"Monthly summary written to {reporting.REPORT_PATH}")
    reporting.log_run("wrote monthly summary")


def option_tests():
    try:
        result = subprocess.run(
            [sys.executable, "tests.py"],
            capture_output=True, text=True, cwd=BASE_DIR,
        )
    except OSError as error:
        print(f"Could not run tests: {error}")
        return
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    print("RESULT: PASS" if result.returncode == 0 else "RESULT: FAIL")
    reporting.log_run("ran self-tests: " + ("pass" if result.returncode == 0 else "fail"))


ACTIONS = {
    "1": option_generate,
    "2": option_load,
    "3": option_ledger,
    "4": option_categories,
    "5": option_duplicates,
    "6": option_outliers,
    "7": option_report,
    "8": option_tests,
}


def main():
    os.chdir(BASE_DIR)  # so data/ paths work wherever the program is started from
    while True:
        print(MENU)
        try:
            choice = input("Choose an option (1-9): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "9":
            print("Goodbye!")
            break

        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice. Please enter a number from 1 to 9.")
            continue

        try:
            action()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
        except Exception as error:  # the menu must never crash
            print(f"Something went wrong: {error}")


if __name__ == "__main__":
    main()