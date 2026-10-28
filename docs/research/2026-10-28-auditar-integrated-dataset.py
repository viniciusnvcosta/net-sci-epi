from collections import Counter
from pathlib import Path

import pandas as pd

p = Path("integrated_dataset.csv")
s = p.stat()
cols = [
    "notification.county",
    "notification.hr",
    "notification.state",
    "exam.result",
    "notification.month",
    "notification.year",
]
total = 0
filtered = 0
count = Counter()
pair = Counter()
null = Counter()
for part in pd.read_csv(
    p,
    sep="\t",
    usecols=cols,
    dtype=str,
    chunksize=200000,
    keep_default_na=True,
    low_memory=False,
):
    total += len(part)
    x = part[part["notification.state"] == "PA"]
    filtered += len(x)
    for c in cols:
        null[c] += int(x[c].isna().sum())
    count.update(
        x.groupby(
            [
                "notification.year",
                "notification.month",
                "notification.hr",
                "exam.result",
            ],
            dropna=False,
        )
        .size()
        .to_dict()
    )
    pair.update(
        x.groupby(["notification.county", "notification.hr"], dropna=False)
        .size()
        .to_dict()
    )
    if total % 2000000 == 0:
        print("processed", total, flush=True)
stat = p.stat()
assert (s.st_size, s.st_mtime_ns) == (stat.st_size, stat.st_mtime_ns)
r = pd.read_csv(
    "rl_municip_regsaud.csv", sep=";", header=None, names=["mun", "reg"], dtype=str
)
n = pd.read_csv(
    "tb_regsaud.csv",
    sep=";",
    header=None,
    names=["reg", "status", "name", "order"],
    dtype=str,
    encoding="latin1",
)
mapping = (
    r.merge(n, on="reg", validate="many_to_one").set_index("mun")["name"].to_dict()
)
valid = {str(k): v for k, v in mapping.items()}
missing = 0
mismatch = Counter()
tail = Counter()
for (municipio, hr), cnt in pair.items():
    if pd.isna(municipio) or municipio not in valid or pd.isna(hr):
        missing += cnt
    elif valid[municipio] != hr:
        mismatch[(municipio, hr, valid[municipio])] += cnt
    if municipio == "150795":
        tail[str(hr)] += cnt
old = pd.read_csv(
    "/home/vinvs/projects/net-sci-epi/data/raw/sivep/PASIVEPDailyPerHr.csv",
    dtype={"notification.year": str, "notification.month": str},
)
old["notification.month"] = old["notification.month"].str.lstrip("0")
old_counts = (
    old.groupby(
        ["notification.year", "notification.month", "notification.hr", "exam.result"]
    )
    .testperhr.sum()
    .to_dict()
)
norm = Counter()
for (year, month, hr, result), value in count.items():
    if any(pd.isna(v) for v in [year, month, hr, result]):
        continue
    norm[(year, month.lstrip("0"), hr, result)] += value
keys = set(old_counts) | set(norm)
diffs = {k: norm.get(k, 0) - old_counts.get(k, 0) for k in keys}
print("records all", total, "PA", filtered, "nulls", dict(null))
print(
    "pairs",
    len(pair),
    "missing",
    missing,
    "mismatch rows",
    sum(mismatch.values()),
    "mismatch pairs",
    len(mismatch),
    "tail aggregate",
    dict(tail),
)
print(
    "cells union",
    len(keys),
    "equal",
    sum(v == 0 for v in diffs.values()),
    "abs difference",
    sum(abs(v) for v in diffs.values()),
    "old sum",
    sum(old_counts.values()),
    "integrated included",
    sum(norm.values()),
)
for year in sorted({k[0] for k in keys}):
    d = [v for k, v in diffs.items() if k[0] == year]
    print(
        "year",
        year,
        "cells",
        len(d),
        "equal",
        sum(v == 0 for v in d),
        "abs diff",
        sum(abs(v) for v in d),
    )
