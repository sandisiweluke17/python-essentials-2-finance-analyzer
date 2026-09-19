# Personal Finance Transaction Analyzer

A menu-driven Python program that reads a messy bank-statement file, cleans and
validates every transaction, tracks a running balance, categorises spending,
flags duplicates and unusual transactions, and writes summary reports.

Built for the Melsoft Academy Python Essentials 2 challenge (2026 DS Jan Cohort)
by Sandisiwe Luke.

## How to run

Requires Python 3. There are no third-party packages.

```
python main.py     # start the menu
python tests.py    # run the self-tests
```

Start with option 1 (generate the sample file), then option 2 (load it).

## Menu options

| Option | What it does |
|--------|--------------|
| 1 | Creates a purposefully messy sample statement called `data/statement.txt` |
| 2 | Loads and validates transactions, rejecting bad rows and providing an explanation for each |
| 3 | Shows the running balance after each transaction |
| 4 | Shows income and expenses per category and flags sign/category mismatches |
| 5 | Identifies exact duplicate transactions |
| 6 | Flags statistical outliers (more than two standard deviations from the mean), with an optional threshold check |
| 7 | Writes a monthly summary to `data/report.txt` |
| 8 | Runs `tests.py` and reports pass/fail |
| 9 | Exits |

## Project structure

```
main.py        menu (wires everything together)
models.py      Transaction class and RecurringTransaction subclass
parser.py      sample file generator and defensive loader
analytics.py   running balance generator, flagger closure, duplicates, outliers, category totals
reporting.py   monthly summary, environment/date stamp, run log
tests.py       assert-based tests for the tricky cases
data/          generated files (statement, report, log) - not committed
```

## Edge cases handled

| Broken input | What happens |
|--------------|--------------|
| Wrong date separator (`2026/08/03`) | Normalised to `2026-08-03` |
| Missing fields or too few commas | Row rejected with a reason, loading continues |
| Junk line (`hello world`) | Row rejected, no crash |
| Non-numeric amount (`abc`) | Row rejected with a clear reason |
| Exact duplicate line | Loaded, and found by option 5 |
| Positive amount tagged as an expense (or the reverse) | Flagged as inconsistent in options 4 and 7 |
| Empty or missing file | Reported with a clear message |
| Extra whitespace | Stripped during cleaning |

## Design notes

- `load_transactions(path)` returns two things: the valid `Transaction` objects
  and a list of rejection reasons such as `row 5: not enough fields`.
- Each row is validated inside its own try/except, so one bad row never stops
  the load.
- Categories are upper-cased so `food` and `FOOD` group together.
- `running_balance` is a generator, and `make_flagger` is a closure that
  remembers its threshold.
- Every run action is written to `data/analyzer.log`, an append-only log.

## Testing

`python tests.py` runs assertions covering valid rows, date normalisation,
rejected rows, whitespace, empty and missing files, the running balance,
the flagger, duplicates, outliers, category totals, and sign mismatches.
It prints `All tests passed` when everything works.