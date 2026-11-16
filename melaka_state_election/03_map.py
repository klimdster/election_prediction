"""Step 3: thematic map of predicted winners -> outputs/melaka_se16_prediction_map.png

Colours (user spec): red = PH and Bersatu, blue = BN and PN, yellow = Bersama, grey = other.
Hatched = Lean / Toss-up.
"""
from collections import Counter
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import pandas as pd
from common import OUT, RAW

COL = {"PH": "#D7262B", "BERSATU": "#D7262B", "BN": "#1F4E9A", "PN": "#1F4E9A", "BERSAMA": "#F2C500"}
CITY = [19, 20, 21, 22]

pred = pd.read_csv(OUT / "prediction_se16.csv")
pred["n"] = pred.seat_no.str[1:].astype(int)
P = pred.set_index("n")


def colour(n: int) -> str:
    q = P.loc[n]
    if q.pred_party in ("BERSATU", "BERSAMA"):
        return COL[q.pred_party]
    return COL.get(q.pred_coalition, "#9E9E9E")


g = gpd.read_file(RAW / "peninsular_2018_dun.geojson")
g = g[g.state == "Melaka"].copy()
g["n"] = g.code_dun.str.extract(r"N\.?0*(\d+)", expand=False).astype(int)
g["c"] = g.n.map(colour)
g["conf"] = g.n.map(P.confidence)
g = g.to_crs(3375)

fig, (ax, ins) = plt.subplots(1, 2, figsize=(18, 8.5), dpi=150, gridspec_kw={"width_ratios": [1.55, 1]})


def draw(a, fs, labels):
    for _, r in g.iterrows():
        gpd.GeoSeries([r.geometry], crs=g.crs).plot(
            ax=a, color=r.c, edgecolor="white", linewidth=0.8,
            hatch="///" if r.conf in ("Lean", "Toss-up") else None)
    for _, r in g.iterrows():
        if r.n in labels:
            pt = r.geometry.representative_point()
            a.annotate(f"N{r.n}", (pt.x, pt.y), ha="center", va="center", fontsize=fs,
                       color="white", fontweight="bold")


draw(ax, 9, [i for i in range(1, 29) if i not in CITY])
draw(ins, 11, [13, 14, 15, 16, 17, 19, 20, 21, 22, 23])
sub = g[g.n.isin(CITY)].total_bounds
pad = 2500
bx = [sub[0] - pad, sub[1] - pad, sub[2] + pad, sub[3] + pad]
ins.set_xlim(bx[0], bx[2])
ins.set_ylim(bx[1], bx[3])
ax.add_patch(mp.Rectangle((bx[0], bx[1]), bx[2] - bx[0], bx[3] - bx[1], fill=False, ec="0.2", lw=1.2, ls="--"))
for a in (ax, ins):
    a.set_xticks([]); a.set_yticks([]); a.set_xlabel(""); a.set_ylabel("")
ax.set_axis_off()
ins.set_title("Inset: Melaka city (dashed box) — N19 to N22", fontsize=11)
ax.set_title("Melaka SE-16 (14 Nov 2026): model-predicted winner by DUN seat\n"
             "Prediction, not a result. Hatched = Lean / Toss-up", fontsize=14, loc="left")
cnt = Counter(P.pred_coalition)
leg = [mp.Patch(color=COL["PH"], label=f"PH / Bersatu (red): PH {cnt.get('PH', 0)}, "
                                        f"Bersatu {(P.pred_party == 'BERSATU').sum()}"),
       mp.Patch(color=COL["BN"], label=f"BN / PN (blue): BN {cnt.get('BN', 0)}, PN {cnt.get('PN', 0)}"),
       mp.Patch(color=COL["BERSAMA"], label=f"Bersama (yellow): {(P.pred_party == 'BERSAMA').sum()}"),
       mp.Patch(color="#9E9E9E", label="Other (grey)"),
       mp.Patch(facecolor="white", edgecolor="k", hatch="///", label="Lean / Toss-up")]
ax.legend(handles=leg, loc="lower left", fontsize=10, frameon=True)
fig.text(0.01, 0.02, "Sources: electiondata.my (ballots, stats, 2018 DUN boundaries); electorate ethnic mix "
         "via Wikipedia (China Press 2026).", fontsize=8, color="0.3")
plt.tight_layout()
plt.savefig(OUT / "melaka_se16_prediction_map.png", bbox_inches="tight", facecolor="white")
print("saved", OUT / "melaka_se16_prediction_map.png")
