"""Fixed-series regional geography, separate from the historical P4 graph."""

import unicodedata

import geopandas as gpd
import pandas as pd

from headd_l0.graph_io import PA_HEALTH_REGIONS_2013


def _code(value: object, width: int) -> str:
    if isinstance(value, str):
        if len(value) != width or not value.isascii() or not value.isdigit():
            raise ValueError("invalid code format")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid numeric code")
    if not pd.notna(value) or int(value) != value:
        raise ValueError("invalid numeric code")
    result = str(int(value))
    if len(result) != width:
        raise ValueError("invalid code length")
    return result


def _name(value: object) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode()
        .upper()
        .split()
    )


def select_pa_crosswalk(relation: pd.DataFrame) -> pd.DataFrame:
    """Select PA municipalities, removing the explicit state aggregate."""
    result = relation[["municipality", "region"]].copy()
    result = result[result.municipality.astype(str).str.startswith("15")].copy()
    result["municipality"] = result.municipality.map(lambda x: _code(x, 6))
    result["region"] = result.region.map(lambda x: _code(x, 5))
    aggregate = result[result.municipality == "150000"]
    if len(aggregate) != 1 or aggregate.region.iloc[0] != "15000":
        raise ValueError("invalid PA aggregate")
    return result[result.municipality != "150000"].reset_index(drop=True)


def join_municipalities(
    municipalities: gpd.GeoDataFrame, relation: pd.DataFrame, names: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Join 144 PA municipalities to their validated fixed regions."""
    m = municipalities.copy()
    r = relation[["municipality", "region"]].copy()
    if "abbrev_state" not in m or not m.abbrev_state.eq("PA").all():
        raise ValueError("municipalities must be PA")
    m["municipality"] = m.code_muni6.map(lambda x: _code(x, 6))
    r["municipality"] = r.municipality.map(lambda x: _code(x, 6))
    r["region"] = r.region.map(lambda x: _code(x, 5))
    if (
        len(m) != 144
        or len(r) != 144
        or m.municipality.duplicated().any()
        or r.municipality.duplicated().any()
        or not r.municipality.str.startswith("15").all()
        or set(m.municipality) != set(r.municipality)
    ):
        raise ValueError("municipality crosswalk is incomplete or duplicated")
    mapping = {str(k): v for k, v in PA_HEALTH_REGIONS_2013.items()}
    if (
        set(r.region) != set(mapping)
        or r.loc[r.municipality == "150795", "region"].item() != "15004"
    ):
        raise ValueError("invalid regional composition")
    n = names.copy()
    n = n[n.region.astype(str).isin(mapping)].copy()
    n["region"] = n.region.map(lambda x: _code(x, 5))
    n["name"] = n.name.map(_name)
    if (
        len(n) != 13
        or n.region.duplicated().any()
        or not n.status.eq("ATIVO").all()
        or not n.name.eq(n.region.map(mapping)).all()
    ):
        raise ValueError("invalid region names")
    joined = m.merge(r, on="municipality", validate="one_to_one")
    joined["name"] = joined.region.map(mapping)
    return joined
