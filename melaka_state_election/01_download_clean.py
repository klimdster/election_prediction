"""Step 1: download electiondata.my files (optional refresh) and check seat cleaning.

Usage: python 01_download_clean.py [--refresh]
Without --refresh, the committed CSV snapshots in data/raw are used and only the
missing files (the 2.3 MB boundary GeoJSON) are downloaded.
"""
import sys
import urllib.request
from common import RAW, SOURCES, load_ballots, load_stats

refresh = "--refresh" in sys.argv
for fname, url in SOURCES.items():
    dest = RAW / fname
    if refresh or not dest.exists():
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, dest)

b, s = load_ballots(), load_stats()
# Cleaning checks
assert b.seat.str.match(r"^N\.\d{2} ").all() and s.seat.str.match(r"^N\.\d{2} ").all()
modern = b[b.date >= "2004"]  # 28-seat map since the 2003 redelineation
assert sorted(modern.n.unique()) == list(range(1, 29))
renamed = modern.groupby("n").seat_name.unique()
renamed = renamed[renamed.apply(len) > 1]
print("Seats renamed since 2004 (treated as continuous):")
for n, names in renamed.items():
    print(f"  N{n}: {' -> '.join(names)}")
pre = s[s.date < "2004"].groupby("election").n.max()
print("Pre-2004 seat counts (different map, excluded):", dict(pre))
se16 = b[b.election == "SE-16"]
print(f"SE-16: {se16.seat.nunique()} seats, {len(se16)} candidates, "
      f"{int(s[s.election == 'SE-16'].voters_total.sum()):,} voters")
