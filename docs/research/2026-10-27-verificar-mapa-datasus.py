import struct
import sys
import zipfile

import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

member = sys.argv[1] if len(sys.argv) > 1 else "br_regsaud.MAP"
if member not in {"br_regsaud.MAP", "br_regsaude.MAP"}:
    raise ValueError("Expected br_regsaud.MAP or br_regsaude.MAP")
print("map", member)
b = zipfile.ZipFile("/tmp/headd-castro-20261027/br_mapas_2013.zip").read(member)
pos = 18
regions = {}
while pos < len(b):
    pos += 1
    lg = b[pos]
    pos += 1
    code = b[pos : pos + 10][:lg].decode("cp1252")
    pos += 10
    ln = b[pos]
    pos += 1
    name = b[pos : pos + 25][:ln].decode("cp1252")
    pos += 25 + 8
    n = struct.unpack_from("<h", b, pos)[0]
    pos += 2
    assert n >= 0 and pos + 8 * n <= len(b)
    coords = list(struct.iter_unpack("<ff", b[pos : pos + 8 * n]))
    pos += 8 * n
    if not code.startswith("15"):
        continue
    rings = []
    start = 0
    for j in range(1, n):
        if (
            abs(coords[j][0] - coords[start][0]) < 1e-6
            and abs(coords[j][1] - coords[start][1]) < 1e-6
            and j - start >= 2
        ):
            rings.append(coords[start : j + 1])
            start = j + 1
    if start < n and n - start >= 3:
        rings.append(coords[start:] + [coords[start]])
    regions.setdefault(code, []).extend(make_valid(Polygon(ring)) for ring in rings)
assert pos == len(b)
mun = gpd.read_file("zip:///tmp/headd-castro-20261027/pa_municipios_2013.zip")
p4 = gpd.read_parquet(
    "/home/vinvs/projects/net-sci-epi/.worktrees/_archive/2026-10-23/second-execution/data/processed/graph/healthregions_2013.parquet"
)
p4 = p4[p4.abbrev_state == "PA"]
mp = {str(int(r.code_muni)): str(int(r.code_health_region)) for r in p4.itertuples()}
unique = 0
miss = []
different = []
for r in mun.itertuples():
    p = r.geometry.representative_point()
    found = [c for c, gs in regions.items() if any(g.covers(p) for g in gs)]
    if len(found) != 1:
        miss.append((r.CD_GEOCMU, found))
        continue
    unique += 1
    if found[0] != mp[r.CD_GEOCMU]:
        different.append((r.CD_GEOCMU, found[0], mp[r.CD_GEOCMU]))
print(
    "regions",
    len(regions),
    "unique",
    unique,
    "missing_or_ambiguous",
    miss,
    "different_vs_P4",
    different,
)

tail = mun.loc[mun.CD_GEOCMU == "1507953"].geometry.iloc[0]
tail_projected = gpd.GeoSeries([tail], crs=4674).to_crs(5880).iloc[0]
for region_code in ("15004", "15011"):
    region = unary_union(regions[region_code])
    projected = gpd.GeoSeries([region], crs=4674).to_crs(5880).iloc[0]
    print(
        region_code,
        "overlap_share",
        tail_projected.intersection(projected).area / tail_projected.area,
    )
