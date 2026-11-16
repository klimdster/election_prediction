"""Optional step 0: rebuild the electorate ethnic mix from Wikipedia constituency pages.

Each Melaka state-constituency page carries a pie chart "Ethnic breakdown of <seat>'s
electorate as of 2026" (citing China Press). electiondata.my has no ethnic data.
Usage: python 00_fetch_ethnic_mix.py [--write]   (--write overwrites data/input/ethnic_mix_2026.json)
Note: Telok Mas only had a 2021 breakdown at the time of the original run.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from common import INPUT

NAMES = ["Kuala Linggi", "Tanjung Bidara", "Ayer Limau", "Lendu", "Taboh Naning", "Rembia", "Gadek",
         "Machap Jaya", "Durian Tunggal", "Asahan", "Sungai Udang", "Pantai Kundor", "Paya Rumput",
         "Kelebang", "Pengkalan Batu", "Ayer Keroh", "Bukit Katil", "Ayer Molek", "Kesidang",
         "Kota Laksamana", "Duyong", "Bandar Hilir", "Telok Mas", "Bemban", "Rim", "Serkam",
         "Merlimau", "Sungai Rambai"]
UA = {"User-Agent": "election-prediction-research/1.0"}


def raw(title: str) -> str:
    url = "https://en.wikipedia.org/w/index.php?" + urllib.parse.urlencode({"title": title, "action": "raw"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        txt = r.read().decode()
    m = re.search(r"#REDIRECT\s*\[\[([^\]]+)\]\]", txt, re.I)
    return raw(m.group(1)) if m else txt


out = {}
for i, name in enumerate(NAMES, 1):
    rec = None
    for title in (f"{name} (state constituency)", name):
        try:
            txt = raw(title)
        except Exception:
            continue
        pm = re.search(r"\{\{Pie chart(.*?)\}\}\s*\n", txt, re.S)
        if not (pm and "electorate" in pm.group(1)):
            continue
        body, d = pm.group(1), {}
        for k in range(1, 6):
            lb = re.search(rf"\|label{k}=(.*?)\|(?:value|color|label)", body)
            vl = re.search(rf"\|value{k}=([\d.]+)", body)
            if lb and vl:
                lab = lb.group(1).split("|")[-1]
                key = ("Malay" if "Malay" in lab else "Chinese" if "Chinese" in lab
                       else "Indian" if "Indian" in lab else "Other")
                d[key] = d.get(key, 0) + float(vl.group(1))
        yr = re.search(r"as of\s*\[\[([^|\]]+)", body)
        rec = {"title": title, "src": yr.group(1) if yr else "", **d}
        break
    out[f"N{i}"] = rec
    print(i, name, rec)

if "--write" in sys.argv:
    json.dump(out, open(INPUT / "ethnic_mix_2026.json", "w"), indent=1)
    print("written")
