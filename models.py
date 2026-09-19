"""Transaction class and subclasses. No file or menu logic lives here."""


class Transaction:
    """A single bank-statement transaction."""

    count = 0  # class variable: how many transactions have been created

    def __init__(self, date, description, amount, category):
        self.date = date
        self.description = description
        self.amount = amount
        self.category = category
        Transaction.count += 1

    def __str__(self):
        return f"{self.date} | {self.description} | {self.amount:.2f} | {self.category}"

    def is_income(self):
        """True for a positive amount, False otherwise."""
        return self.amount > 0

    def formatted(self):
        """Signed, formatted line e.g. '2026-08-01 Groceries -450.50 FOOD'."""
        return f"{self.date} {self.description} {self.amount:+.2f} {self.category.upper()}"


class RecurringTransaction(Transaction):
    """A transaction that repeats on an interval (e.g. monthly rent)."""

    def __init__(self, date, description, amount, category, interval="monthly"):
        super().__init__(date, description, amount, category)
        self.interval = interval

    def __str__(self):
        return f"{super().__str__()} (recurring: {self.interval})"
