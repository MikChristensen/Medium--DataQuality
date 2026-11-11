import sqlite3
import pandas as pd


class SelectDatabase:
    def __init__(self, db_path="data/synthetic_erp_data.db"):
        self.db_path = db_path

    def _read(self, table: str) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)

    def get_customers(self):
        return self._read("customers")

    def get_vendors(self):
        return self._read("vendors")

    def get_materials(self):
        return self._read("materials")

    def get_sales_order_header(self):
        return self._read("sales_order_header")

    def get_sales_order_line(self):
        return self._read("sales_order_line")

    def get_inventory(self):
        return self._read("inventory")
