import numpy as np
import pandas as pd


class DataCorruptor:

    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)
        self.error_log = []

    def _sample_indices(self, df, fraction):
        n = max(1, int(len(df) * fraction))
        return self.rng.choice(
            df.index.to_numpy(),
            size=n,
            replace=False
        )

    def missing_values(
        self,
        df,
        column,
        fraction=0.01
    ):
        idx = self._sample_indices(df, fraction)

        for i in idx:
            self.error_log.append({
                "table": None,
                "row_index": int(i),
                "column": column,
                "error_type": "missing_value",
                "original_value": df.at[i, column],
                "corrupted_value": None
            })

        df.loc[idx, column] = None

        return df

    def duplicate_records(
        self,
        df,
        fraction=0.005
    ):
        """
        Duplicate a fraction of randomly selected rows.

        The duplicated rows are added to the DataFrame and
        recorded in the ground-truth error log.
        """

        idx = self._sample_indices(df, fraction)

        duplicates = df.loc[idx].copy()

        for i in idx:
            self.error_log.append({
                "row_index": int(i),
                "column": None,
                "error_type": "duplicate_record",
                "original_value": None,
                "corrupted_value": "duplicated"
            })

        df_corrupt = pd.concat(
            [df, duplicates],
            ignore_index=True
        )

        return df_corrupt

    def invalid_range(
        self,
        df,
        column,
        fraction=0.005,
        invalid_value=-10
    ):
        """
        Replace values in a numeric column with a deliberately
        invalid value.

        Example:
            quantity = -10
            standard_cost = -100
        """

        idx = self._sample_indices(df, fraction)

        for i in idx:
            self.error_log.append({
                "row_index": int(i),
                "column": column,
                "error_type": "invalid_range",
                "original_value": df.at[i, column],
                "corrupted_value": invalid_value
            })

        df.loc[idx, column] = invalid_value

        return df

    def extreme_values(
        self,
        df,
        column,
        fraction=0.005,
        multiplier=1000
    ):
        """
        Create statistically extreme values while keeping
        them technically valid.

        Example:
            quantity:      5 -> 5000
            standard_cost: 125.50 -> 125500.00
        """

        idx = self._sample_indices(df, fraction)

        for i in idx:
            original_value = df.at[i, column]
            corrupted_value = original_value * multiplier

            self.error_log.append({
                "row_index": int(i),
                "column": column,
                "error_type": "extreme_value",
                "original_value": original_value,
                "corrupted_value": corrupted_value
            })

            df.at[i, column] = corrupted_value

        return df

    def duplicate_entities(
        self,
        df,
        id_column="customer_id",
        name_column="customer_name",
        fraction=0.01
    ):
        """
        Create duplicate business entities with different
        primary keys and slightly different names.
        """

        idx = self._sample_indices(df, fraction)

        duplicates = df.loc[idx].copy()

        existing_ids = set(df[id_column].astype(str))
        next_id = 1

        for i in idx:
            original_id = df.at[i, id_column]
            original_name = str(df.at[i, name_column])

            # Generate a unique synthetic customer ID
            while f"DUP{next_id:06d}" in existing_ids:
                next_id += 1

            new_id = f"DUP{next_id:06d}"
            existing_ids.add(new_id)
            next_id += 1

            # Introduce a variation in the customer name
            new_name = f"{original_name} Group"

            duplicates.at[i, id_column] = new_id
            duplicates.at[i, name_column] = new_name

            self.error_log.append({
                "row_index": int(i),
                "column": name_column,
                "error_type": "duplicate_entity",
                "original_value": original_name,
                "corrupted_value": new_name,
                "original_id": original_id,
                "duplicate_id": new_id
            })

        return pd.concat(
            [df, duplicates],
            ignore_index=True
        )

    def functional_dependency_violation(
        self,
        df,
        id_column,
        value_column,
        fraction=0.005
    ):
        """
        Create conflicting records with the same ID
        but different attribute values.
        """

        idx = self._sample_indices(df, fraction)

        duplicates = df.loc[idx].copy()

        for i in idx:
            original = df.at[i, value_column]
            corrupted = f"CONFLICT_{original}"

            duplicates.at[i, value_column] = corrupted

            self.error_log.append({
                "row_index": int(i),
                "column": value_column,
                "error_type": "functional_dependency_violation",
                "original_value": original,
                "corrupted_value": corrupted,
                "record_id": df.at[i, id_column]
            })

        return pd.concat(
            [df, duplicates],
            ignore_index=True
        )