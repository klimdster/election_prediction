"""Step 4: compare SE-16 actual results with the prediction, plus the Bersama
(Melaka vs Johor) and N24 Bemban analyses.

Outputs (outputs/):
  actual_vs_predicted_se16.csv   per-seat winner, margins, bloc shares, turnout
  scorecard.json                 seats correct, MAE/bias by bloc, statewide shares
  bersama_melaka_vs_johor.csv
  bemban_history.csv             N24 candidates SE-13..SE-16
  bemban_vote_flow.csv           bloc totals 2021 vs 2026 (2021 scaled to 2026 valid votes)
  bersama_by_seat.csv            Bersama share vs ethnic mix and whether PH stood
"""
import json
import numpy as np
import pandas as pd
from common import OUT, bloc_of, load_ballots, load_ethnic, load_stats

b, s, E = load_ballots(), load_stats(), load_ethnic()
x = b[b.election == "SE-16"].copy()
if (x.result == "pending").any():
    raise SystemExit("SE-16 results not published yet in data/raw; run 01_download_clean.py --refresh")
x["bloc"] = x.party.map(bloc_of)
x["pct"] = x.votes / x.groupby("n").votes.transform("sum") * 100
A = x.pivot_table(index="n", columns="bloc", values="pct", aggfunc="sum").fillna(0)

pred = pd.read_csv(OUT / "prediction_se16.csv")
pred["n"] = pred.seat_no.str[1:].astype(int)
pred = pred.set_index("n")
Pb = pd.DataFrame([{bloc_of(k): 0 for k in []} | pd.Series(json.loads(js)).groupby(
    lambda k: bloc_of(k)).sum().to_dict() for js in pred.pred_shares_pct], index=pred.index).fillna(0)

xs = x.sort_values(["n", "votes"], ascending=[True, False])
win = xs.groupby("n").nth(0).set_index("n")
ru = xs.groupby("n").nth(1).set_index("n")
st = s[s.election == "SE-16"].set_index("n")
cmp = pd.DataFrame({
    "seat_no": "N" + pred.index.astype(str), "seat": pred.seat,
    "pred_winner": pred.pred_party + "/" + pred.pred_coalition,
    "actual_winner": win.party + "/" + win.coalition, "actual_candidate": win["name"],
    "pred_margin_pts": pred.pred_margin_pts, "actual_margin_pts": (win.pct - ru.pct).round(1),
    "confidence": pred.confidence,
    "turnout_pct": st.voter_turnout.round(1), "voters": st.voters_total, "valid_votes": st.votes_valid,
})
cmp["correct"] = cmp.pred_winner.str.split("/").str[0] == cmp.actual_winner.str.split("/").str[0]
blocs = ["BNPN", "PH", "BERSATU", "BERSAMA", "OTH"]
for c in blocs:
    cmp[f"pred_{c}_pct"] = Pb.get(c, 0).round(1)
    cmp[f"actual_{c}_pct"] = A.get(c, 0).round(1)
cmp.to_csv(OUT / "actual_vs_predicted_se16.csv", index=False)

score = {"seats_correct": int(cmp.correct.sum()), "seats": len(cmp), "bloc_error": {}}
for c in blocs[:4]:
    m = (cmp[f"actual_{c}_pct"] > 0) | (cmp[f"pred_{c}_pct"] > 0)
    e = (cmp[f"actual_{c}_pct"] - cmp[f"pred_{c}_pct"])[m]
    score["bloc_error"][c] = {"seats": int(m.sum()), "mae_pts": round(e.abs().mean(), 1),
                              "bias_actual_minus_pred_pts": round(e.mean(), 1)}
score["statewide_actual_pct"] = (x.groupby("bloc").votes.sum() / x.votes.sum() * 100).round(2).to_dict()
w = pred.index.map(lambda n: st.voters_total[n])
score["statewide_pred_pct"] = (Pb.mul(w, axis=0).sum() / Pb.mul(w, axis=0).sum().sum() * 100).round(2).to_dict()
t = s.groupby("election")[["ballots_issued", "voters_total"]].sum()
score["turnout_pct"] = {e: round(t.loc[e].ballots_issued / t.loc[e].voters_total * 100, 1) for e in ("SE-15", "SE-16")}
cmp["abs_margin_err"] = (cmp.actual_margin_pts - cmp.pred_margin_pts).abs()
score["biggest_margin_misses"] = cmp.sort_values("abs_margin_err", ascending=False).head(6)[
    ["seat_no", "seat", "pred_margin_pts", "actual_margin_pts"]].to_dict("records")
json.dump(score, open(OUT / "scorecard.json", "w"), indent=1)
print(json.dumps(score, indent=1))

# --- Bersama: Melaka vs Johor ------------------------------------------------
rows = []
for state, label in (("mlk", "Melaka"), ("jhr", "Johor")):
    bb = load_ballots(state)
    y = bb[bb.election == "SE-16"]
    bs = y[y.party == "BERSAMA"]
    seats = bs.seat.unique()
    ph_seats = set(y[y.coalition == "PH"].seat)
    rows.append({
        "state": label, "date": y.date.iloc[0], "seats_total": y.seat.nunique(),
        "bersama_votes": int(bs.votes.sum()), "total_valid_votes": int(y.votes.sum()),
        "statewide_pct": round(bs.votes.sum() / y.votes.sum() * 100, 2),
        "seats_contested": len(seats),
        "pct_in_contested_seats": round(bs.votes.sum() / y[y.seat.isin(seats)].votes.sum() * 100, 2),
        "best_seat": bs.sort_values("votes_perc").iloc[-1].seat,
        "best_seat_pct": round(bs.votes_perc.max(), 1),
        "deposits_lost": int((bs.result == "lost_deposit").sum()),
        "contested_without_PH": int(sum(1 for z in seats if z not in ph_seats)),
    })
bj = pd.DataFrame(rows)
bj.to_csv(OUT / "bersama_melaka_vs_johor.csv", index=False)
print(bj.to_string(index=False))

# --- Bersama by seat vs ethnic mix -------------------------------------------
bs = x[x.party == "BERSAMA"]
ph_n = set(x[x.coalition == "PH"].n)
bsd = pd.DataFrame({"seat_no": "N" + bs.n.astype(str), "seat": bs.seat_name.values,
                    "bersama_pct": bs.votes_perc.round(1).values,
                    "malay_pct": (E.Malay[bs.n] * 100).round(1).values,
                    "non_malay_pct": ((E.Chinese + E.Indian)[bs.n] * 100).round(1).values,
                    "ph_contested": [n in ph_n for n in bs.n]})
fit = np.polyfit(bsd[bsd.ph_contested].non_malay_pct, bsd[bsd.ph_contested].bersama_pct, 1)
bsd["expected_if_ph_contested"] = np.polyval(fit, bsd.non_malay_pct).round(1)
bsd.to_csv(OUT / "bersama_by_seat.csv", index=False)
print(bsd.sort_values("non_malay_pct").to_string(index=False))

# --- N24 Bemban ---------------------------------------------------------------
N = 24
hist = b[(b.n == N) & b.election.isin(["SE-13", "SE-14", "SE-15", "SE-16"])][
    ["election", "date", "seat", "name", "ethnicity", "party", "coalition", "votes", "votes_perc", "result"]]
sth = s[(s.n == N) & s.election.isin(hist.election.unique())][
    ["election", "voters_total", "ballots_issued", "votes_valid", "voter_turnout", "majority"]]
hist = hist.merge(sth, on="election")
hist.to_csv(OUT / "bemban_history.csv", index=False)
print(hist.to_string(index=False))


def bemban_bloc(r):
    if r.election == "SE-15":
        return {"BN": "BN+PN pact", "PN": "BN+PN pact", "PH": "PH"}.get(r.coalition, "Independents/others")
    return {"BNPN": "BN+PN pact", "BERSATU": "Bersatu", "BERSAMA": "Bersama"}.get(bloc_of(r.party), "Independents/others")


h = hist[hist.election.isin(["SE-15", "SE-16"])].copy()
h["bloc"] = h.apply(bemban_bloc, axis=1)
flow = h.pivot_table(index="bloc", columns="election", values="votes", aggfunc="sum").fillna(0)
v21 = sth.set_index("election").votes_valid
scale = v21["SE-16"] / v21["SE-15"]
flow["SE-15_scaled_to_SE-16"] = (flow["SE-15"] * scale).round()
for e in ("SE-15", "SE-16"):
    flow[f"{e}_pct"] = (flow[e] / v21[e] * 100).round(1)
flow.to_csv(OUT / "bemban_vote_flow.csv")
print(flow.to_string())
print("Expected Bersama in Bemban from PH-contested fit:",
      round(float(np.polyval(fit, (E.Chinese[N] + E.Indian[N]) * 100)), 1), "%")
