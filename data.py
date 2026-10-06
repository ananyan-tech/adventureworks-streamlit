"""Snowflake access layer for the AdventureWorks Streamlit application."""

from __future__ import annotations

import os
import re
from typing import Final

import pandas as pd
import streamlit as st

DEFAULT_DATABASE: Final[str] = "ADVENTURE_WORKS_PROD"
DEFAULT_SCHEMA: Final[str] = "MARTS"
TABLES: Final[dict[str, str]] = {
    "executive": "MART_STREAMLIT__EXECUTIVE_KPIS",
    "monthly": "MART_STREAMLIT__MONTHLY_PERFORMANCE",
    "products": "MART_STREAMLIT__PRODUCT_PERFORMANCE",
    "customers": "MART_STREAMLIT__CUSTOMER_INSIGHTS",
    "employees": "MART_STREAMLIT__EMPLOYEE_PURCHASING",
}
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _secret(name: str, default: str) -> str:
    env_value = os.getenv(name.upper())
    if env_value:
        return env_value
    try:
        return str(st.secrets.get(name, st.secrets.get(name.lower(), default)))
    except Exception:
        return default


def database_name() -> str:
    return _secret("SNOWFLAKE_DATABASE", DEFAULT_DATABASE)


def schema_name() -> str:
    return _secret("SNOWFLAKE_SCHEMA", DEFAULT_SCHEMA)


def _qualified_name(table: str) -> str:
    database = database_name()
    schema = schema_name()
    for identifier in (database, schema, table):
        if not _IDENTIFIER.fullmatch(identifier):
            raise ValueError(f"Unsafe Snowflake identifier: {identifier!r}")
    return f'"{database.upper()}"."{schema.upper()}"."{table.upper()}"'


def _run_query(query: str) -> pd.DataFrame:
    """Use the active Snowpark session in Snowflake, or st.connection locally."""
    try:
        from snowflake.snowpark.context import get_active_session

        session = get_active_session()
        frame = session.sql(query).to_pandas()
    except Exception:
        connection = st.connection("snowflake")
        frame = connection.query(query, ttl=600)

    frame = frame.copy()
    frame.columns = [str(column).lower() for column in frame.columns]
    return frame


@st.cache_data(ttl=600, show_spinner=False)
def load_dataset(dataset: str) -> pd.DataFrame:
    if dataset not in TABLES:
        raise KeyError(f"Unknown application dataset: {dataset}")
    return _run_query(f"select * from {_qualified_name(TABLES[dataset])}")


def load_all() -> dict[str, pd.DataFrame]:
    return {name: load_dataset(name) for name in TABLES}
