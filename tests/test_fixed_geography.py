"""Tests for the fixed-series geography candidate."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from headd_l0.graph_io import PA_HEALTH_REGIONS_2013


@pytest.fixture
def geography_inputs():
    codes = [f"15{i:04d}" for i in range(1, 144)] + ["150795"]
    regions = list(PA_HEALTH_REGIONS_2013)
    assigned = [str(regions[i % 13]) for i in range(143)] + ["15004"]
    relation = pd.DataFrame({"municipality": codes, "region": assigned})
    municipality = gpd.GeoDataFrame(
        {"code_muni6": [int(c) for c in codes], "abbrev_state": "PA"},
        geometry=[box(i, 0, i + 1, 1) for i in range(144)],
        crs="EPSG:4674",
    )
    names = pd.DataFrame(
        [(str(k), "ATIVO", v, "1") for k, v in PA_HEALTH_REGIONS_2013.items()],
        columns=["region", "status", "name", "level"],
    )
    return municipality, relation, names


def test_crosswalk_selects_pa_and_aggregate(geography_inputs):
    from headd_l0.fixed_geography import join_municipalities, select_pa_crosswalk

    municipalities, relation, names = geography_inputs
    relation = pd.concat(
        [
            relation,
            pd.DataFrame(
                {
                    "municipality": ["150000", "110001", "0"],
                    "region": ["15000", "11001", "0"],
                }
            ),
        ],
        ignore_index=True,
    )
    selected = select_pa_crosswalk(relation)
    assert len(selected) == 144
    result = join_municipalities(municipalities, selected, names)
    assert len(result) == 144
    assert result.loc[result.code_muni6 == 150795, "name"].item() == "LAGO DE TUCURUI"
    municipalities["code_muni6"] = municipalities.code_muni6.astype(str)
    assert len(join_municipalities(municipalities, selected, names)) == 144


@pytest.mark.parametrize(
    "failure",
    ["missing", "duplicate", "fraction", "external", "region", "name", "tailandia"],
)
def test_crosswalk_rejects_bad_input(geography_inputs, failure):
    from headd_l0.fixed_geography import join_municipalities

    municipalities, relation, names = geography_inputs
    if failure == "missing":
        relation = relation.iloc[:-1]
    elif failure == "duplicate":
        relation = pd.concat([relation, relation.iloc[[0]]], ignore_index=True)
    elif failure == "fraction":
        municipalities["code_muni6"] = municipalities.code_muni6.astype(float)
        municipalities.loc[0, "code_muni6"] = 150001.5
    elif failure == "external":
        relation.loc[0, "municipality"] = "110001"
    elif failure == "region":
        relation.loc[0, "region"] = "15999"
    elif failure == "name":
        names.loc[0, "name"] = "OUTRA"
    else:
        relation.loc[143, "region"] = "15011"
    with pytest.raises(ValueError):
        join_municipalities(municipalities, relation, names)
