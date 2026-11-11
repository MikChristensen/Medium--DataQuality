from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from faker import Faker


class DataGenerator:
    """Generate reproducible, relational synthetic ERP data without LLM calls."""

    TARGETS = {
        "customers": 5_000,
        "vendors": 250,
        "materials": 2_000,
        "sales_order_header": 20_000,
        "sales_order_line": 65_000,
        "inventory": 6_000,
    }

    COUNTRIES = {
        "DK": {"currency": "DKK", "locale": "da_DK", "vat": "DK"},
        "SE": {"currency": "SEK", "locale": "sv_SE", "vat": "SE"},
        "NO": {"currency": "NOK", "locale": "no_NO", "vat": "NO"},
        "DE": {"currency": "EUR", "locale": "de_DE", "vat": "DE"},
        "NL": {"currency": "EUR", "locale": "nl_NL", "vat": "NL"},
    }

    MATERIAL_GROUPS = {
        "Industrial": ("KG", 8.0, 120.0),
        "Electrical": ("EA", 15.0, 500.0),
        "Packaging": ("EA", 0.5, 40.0),
        "Safety": ("EA", 2.0, 150.0),
        "Mechanical": ("EA", 10.0, 350.0),
    }

    PLANTS = ["DK01", "DK02", "DE01"]
    STORAGE = ["MAIN", "RAW", "FIN", "QA"]

    def __init__(self, db_path: str = "data/synthetic_erp_data.db", seed: int = 42):
        self.db_path = db_path
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)
        Faker.seed(seed)
        self.fakers = {code: Faker(cfg["locale"]) for code, cfg in self.COUNTRIES.items()}

        directory = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(directory, exist_ok=True)

    def generate_data(self, scenarios: Iterable[str] | None = None) -> Dict[str, int]:
        """Generate requested tables, including dependencies, and persist to SQLite."""
        requested = list(scenarios or self.TARGETS.keys())
        unknown = set(requested) - set(self.TARGETS)
        if unknown:
            raise ValueError(f"Unknown scenarios: {sorted(unknown)}")

        # Dependencies are cheap to generate and guarantee valid foreign keys.
        builders = {
            "customers": self._customers,
            "vendors": self._vendors,
            "materials": self._materials,
            "sales_order_header": self._sales_order_header,
            "sales_order_line": self._sales_order_line,
            "inventory": self._inventory,
        }

        frames: Dict[str, pd.DataFrame] = {}
        for name in self.TARGETS:
            if name in requested or self._is_dependency(name, requested):
                frames[name] = builders[name](frames)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = OFF")
            for name in requested:
                df = frames[name]
                self._validate(name, df, frames)
                df.to_sql(name, conn, if_exists="replace", index=False)
                print(f"{name}: {len(df):,} rows")
            conn.commit()

        return {name: len(frames[name]) for name in requested}

    @staticmethod
    def _is_dependency(name: str, requested: list[str]) -> bool:
        deps = {
            "materials": {"vendors"},
            "sales_order_header": {"customers"},
            "sales_order_line": {"sales_order_header", "materials", "customers", "vendors"},
            "inventory": {"materials", "vendors"},
        }
        needed = set()
        for table in requested:
            needed |= deps.get(table, set())
        return name in needed

    def _customers(self, _: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows = []
        countries = list(self.COUNTRIES)
        probs = [0.45, 0.16, 0.10, 0.20, 0.09]
        for i in range(1, self.TARGETS["customers"] + 1):
            country = self.rng.choice(countries, p=probs)
            fake = self.fakers[country]
            currency = self.COUNTRIES[country]["currency"]
            rows.append({
                "customer_id": f"CUST{i:06d}",
                "customer_name": fake.company(),
                "customer_group": self.rng.choice(["Standard", "Key Account", "Strategic"], p=[0.72, 0.22, 0.06]),
                "country_code": country,
                "city": fake.city(),
                "postal_code": fake.postcode(),
                "address": fake.street_address(),
                "vat_number": f"{country}{self.rng.integers(10_000_000, 99_999_999)}",
                "currency_code": currency,
                "payment_terms": self.rng.choice(["NET14", "NET30", "NET60"], p=[0.15, 0.65, 0.20]),
                "credit_limit": round(float(self.rng.lognormal(10.3, 0.8)), 2),
                "active": int(self.rng.random() > 0.04),
            })
        return pd.DataFrame(rows)

    def _vendors(self, _: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows = []
        countries = list(self.COUNTRIES)
        for i in range(1, self.TARGETS["vendors"] + 1):
            country = self.rng.choice(countries)
            rows.append({
                "vendor_id": f"VEND{i:06d}",
                "vendor_name": self.fakers[country].company(),
                "vendor_group": self.rng.choice(["Preferred", "Standard", "Specialist"], p=[0.25, 0.60, 0.15]),
                "country_code": country,
                "currency_code": self.COUNTRIES[country]["currency"],
                "payment_terms": self.rng.choice(["NET14", "NET30", "NET60"], p=[0.10, 0.65, 0.25]),
                "active": int(self.rng.random() > 0.03),
            })
        return pd.DataFrame(rows)

    def _materials(self, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        vendor_ids = frames["vendors"]["vendor_id"].to_numpy()
        groups = list(self.MATERIAL_GROUPS)
        nouns = ["bearing", "cable", "valve", "filter", "seal", "connector", "housing", "fastener", "film", "glove"]
        rows = []
        for i in range(1, self.TARGETS["materials"] + 1):
            group = self.rng.choice(groups, p=[0.28, 0.22, 0.16, 0.14, 0.20])
            unit, low, high = self.MATERIAL_GROUPS[group]
            rows.append({
                "material_id": f"MAT{i:06d}",
                "material_description": f"{group} {self.rng.choice(nouns)} {i:04d}",
                "material_group": group,
                "base_unit": unit,
                "standard_cost": round(float(self.rng.uniform(low, high)), 2),
                "currency_code": "EUR",
                "vendor_id": str(self.rng.choice(vendor_ids)),
                "active": int(self.rng.random() > 0.025),
            })
        return pd.DataFrame(rows)

    def _sales_order_header(self, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        customers = frames["customers"].set_index("customer_id")
        customer_ids = customers.index.to_numpy()
        start = date(2025, 10, 1)
        rows = []
        for i in range(1, self.TARGETS["sales_order_header"] + 1):
            cid = str(self.rng.choice(customer_ids))
            order_date = start + timedelta(days=int(self.rng.integers(0, 365)))
            delivery = order_date + timedelta(days=int(self.rng.integers(1, 22)))
            customer = customers.loc[cid]
            rows.append({
                "sales_order_id": f"SO{i:07d}",
                "customer_id": cid,
                "order_date": order_date.isoformat(),
                "requested_delivery_date": delivery.isoformat(),
                "currency_code": customer["currency_code"],
                "payment_terms": customer["payment_terms"],
                "order_status": self.rng.choice(["Completed", "Open", "In Progress", "Cancelled"], p=[0.72, 0.10, 0.15, 0.03]),
            })
        return pd.DataFrame(rows)

    def _sales_order_line(self, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        orders = frames["sales_order_header"]["sales_order_id"].to_numpy()
        materials = frames["materials"].set_index("material_id")
        material_ids = materials.index.to_numpy()

        # Guarantee every order gets at least one line, then distribute remaining lines.
        order_pool = list(orders)
        remaining = self.TARGETS["sales_order_line"] - len(order_pool)
        order_pool.extend(self.rng.choice(orders, size=remaining, replace=True).tolist())
        self.rng.shuffle(order_pool)

        line_counters: Dict[str, int] = {}
        rows = []
        for oid in order_pool:
            oid = str(oid)
            line_counters[oid] = line_counters.get(oid, 0) + 10
            mid = str(self.rng.choice(material_ids))
            material = materials.loc[mid]
            markup = float(self.rng.uniform(1.15, 1.75))
            rows.append({
                "sales_order_id": oid,
                "line_no": line_counters[oid],
                "material_id": mid,
                "quantity": int(max(1, round(self.rng.lognormal(1.5, 0.9)))),
                "unit": material["base_unit"],
                "unit_price": round(float(material["standard_cost"]) * markup, 2),
                "discount_pct": float(self.rng.choice([0, 2.5, 5, 10, 15], p=[0.50, 0.10, 0.22, 0.14, 0.04])),
                "plant_code": str(self.rng.choice(self.PLANTS, p=[0.55, 0.20, 0.25])),
            })
        return pd.DataFrame(rows)

    def _inventory(self, frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        materials = frames["materials"].set_index("material_id")
        material_ids = materials.index.to_numpy()
        start = date(2025, 10, 1)
        rows = []
        for i in range(self.TARGETS["inventory"]):
            mid = str(material_ids[i % len(material_ids)])
            material = materials.loc[mid]
            rows.append({
                "material_id": mid,
                "plant_code": self.PLANTS[(i // len(material_ids)) % len(self.PLANTS)],
                "storage_location": str(self.rng.choice(self.STORAGE)),
                "quantity_on_hand": int(self.rng.integers(0, 2500)),
                "unit": material["base_unit"],
                "last_movement_date": (start + timedelta(days=int(self.rng.integers(0, 365)))).isoformat(),
            })
        return pd.DataFrame(rows)

    def _validate(self, name: str, df: pd.DataFrame, frames: Dict[str, pd.DataFrame]) -> None:
        expected = self.TARGETS[name]
        if len(df) != expected:
            raise ValueError(f"{name}: expected {expected:,} rows, got {len(df):,}")
        if df.isna().any().any():
            raise ValueError(f"{name}: unexpected NULL values")

        unique_keys = {
            "customers": ["customer_id"],
            "vendors": ["vendor_id"],
            "materials": ["material_id"],
            "sales_order_header": ["sales_order_id"],
            "sales_order_line": ["sales_order_id", "line_no"],
            "inventory": ["material_id", "plant_code"],
        }
        if df.duplicated(unique_keys[name]).any():
            raise ValueError(f"{name}: duplicate key detected")

        fk_checks = {
            "materials": ("vendor_id", "vendors", "vendor_id"),
            "sales_order_header": ("customer_id", "customers", "customer_id"),
        }
        if name in fk_checks:
            col, parent, parent_col = fk_checks[name]
            if not set(df[col]).issubset(set(frames[parent][parent_col])):
                raise ValueError(f"{name}: invalid foreign key in {col}")

        if name == "sales_order_line":
            if not set(df["sales_order_id"]).issubset(set(frames["sales_order_header"]["sales_order_id"])):
                raise ValueError("sales_order_line: invalid sales_order_id")
            if not set(df["material_id"]).issubset(set(frames["materials"]["material_id"])):
                raise ValueError("sales_order_line: invalid material_id")
