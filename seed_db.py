import shutil
import sqlite3
import tempfile
from datetime import date

FINAL_PATH = "data/company.db"

PLAN_PRICE = {"Starter": 49.0, "Growth": 199.0, "Enterprise": 499.0}
REFERENCE_DATE = date(2024, 6, 1)  # the "as of" snapshot date for this dataset

# (id, name, plan, signup_date, status, churn_date)
CUSTOMERS = [
    (1, "Acme Retail", "Growth", "2023-01-15", "active", None),
    (2, "Blue Harbor Goods", "Starter", "2023-02-10", "churned", "2024-03-01"),
    (3, "Cedar & Co", "Enterprise", "2022-11-05", "active", None),
    (4, "Daily Grind Coffee", "Starter", "2023-05-20", "churned", "2024-01-15"),
    (5, "Evergreen Supply", "Growth", "2023-03-12", "active", None),
    (6, "Fresh Fields Market", "Growth", "2022-09-01", "churned", "2024-02-20"),
    (7, "Golden Gate Apparel", "Enterprise", "2021-12-01", "active", None),
    (8, "Harbor Lane Books", "Starter", "2023-07-08", "active", None),
    (9, "Ironwood Furniture", "Growth", "2022-06-15", "churned", "2023-12-10"),
    (10, "Juniper Kids", "Starter", "2023-09-01", "active", None),
    (11, "Kite & Key Toys", "Growth", "2023-04-18", "churned", "2024-03-15"),
    (12, "Lantern Home Goods", "Enterprise", "2022-02-01", "active", None),
    (13, "Maple Street Bakery", "Starter", "2023-10-05", "active", None),
    (14, "Nomad Outdoor", "Growth", "2023-01-30", "churned", "2024-02-05"),
    (15, "Oakwood Pet Supply", "Starter", "2023-06-12", "active", None),
]


def add_months(d: date, n: int) -> date:
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def month_range(start: date, end: date):
    months = []
    current = date(start.year, start.month, 1)
    end_month = date(end.year, end.month, 1)
    while current <= end_month:
        months.append(current)
        current = add_months(current, 1)
    return months


def build_orders():
    """One monthly billing row per customer from signup until churn (or the reference date)."""
    orders = []
    order_id = 1
    for cust_id, _name, plan, signup_str, status, churn_str in CUSTOMERS:
        signup = date.fromisoformat(signup_str)
        if status == "churned":
            churn = date.fromisoformat(churn_str)
            last_billed = add_months(date(churn.year, churn.month, 1), -1)
        else:
            last_billed = REFERENCE_DATE
        for month in month_range(signup, last_billed):
            orders.append((order_id, cust_id, month.isoformat(), PLAN_PRICE[plan]))
            order_id += 1
    return orders


def main():
    # Build in a local temp dir first, then copy into place: sqlite's file
    # locking can fail when the working directory is a network/UNC mount
    # (e.g. a WSL path accessed from Windows), but a plain file copy is safe.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = f"{tmp_dir}/company.db"
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS customers;

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                plan TEXT NOT NULL CHECK(plan IN ('Starter','Growth','Enterprise')),
                signup_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('active','churned')),
                churn_date TEXT
            );

            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                order_date TEXT NOT NULL,
                amount REAL NOT NULL
            );
            """
        )
        cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", CUSTOMERS)
        cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", build_orders())
        conn.commit()

        n_customers = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        n_orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        n_churned = cur.execute("SELECT COUNT(*) FROM customers WHERE status='churned'").fetchone()[0]
        conn.close()

        shutil.copyfile(tmp_path, FINAL_PATH)

    print(f"Created {FINAL_PATH}: {n_customers} customers ({n_churned} churned), {n_orders} orders.")


if __name__ == "__main__":
    main()
