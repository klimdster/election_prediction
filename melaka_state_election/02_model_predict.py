"""Step 2: seat-by-seat SE-16 prediction.

Only pre-election information is used: SE-15 (2021) seat results, the SE-16
candidate list, the 2026 electorate ethnic mix and assumed 2026 voting rates.
Outputs: outputs/prediction_se16.csv, outputs/prediction_se16.json
"""
import json
import numpy as np
import pandas as pd
from common import INPUT, OUT, load_ballots, load_ethnic, load_stats

# --- Assumptions (2026 BN-PN pact environment; benchmarked on Johor Jul-2026,
#     Negeri Sembilan Aug-2026 and Ilham Centre's Nov-2026 Melaka survey) ------
RATES = {  # share of each group's vote: [Malay(+Other), Chinese, Indian]
    "PH":   np.array([0.15, 0.78, 0.55]),
    "BNPN": np.array([0.84, 0.21, 0.44]),
}
W_CONTINUITY = 0.5          # weight on 2021 seat result vs ethnic-rate model
PN_TO_PACT = 0.85           # share of 2021 PN vote kept by the pact
PN_TO_PH = 0.05             # share of 2021 PN vote moving to PH
PH_DRIFT = 0.01
INCUMBENT_BONUS = 0.02
INCUMBENTS = {
    "Ab Rauf bin Yusoh", "Muhamad Akmal bin Saleh", "Kerk Chee Yee", "Adly bin Zahari",
    "Seah Shoo Chin (Allex Seah)", "Low Chee Leong", "Leng Chau Yen", "Rosli bin Abdullah",
    "Hameed bin Mytheen Kunju Basheer", "Zulkiflee bin Mohd Zin", "Ngwe Hee Sem",
    "Fairul Nizam bin Roslan", "Tuminah binti Kadi @ Mohd Hashim", "Lim Ban Hong",
    "Mohd Noor Helmy bin Abdul Halem", "Abdul Razak bin Abdul Rahman",
    "Khaidhirah binti Abu Zahar", "Mohd Yadzil bin Yaakub",
}

b = load_ballots()
E = load_ethnic()
M, C, I = E.Malay + E.Other, E.Chinese, E.Indian
X = np.c_[M, C, I]
p21 = (b[b.election == "SE-15"]
       .pivot_table(index="n", columns="coalition", values="votes_perc", aggfunc="sum")
       .fillna(0) / 100)
cands = b[b.election == "SE-16"]


def predict_seat(n: int, swing: float = 0.0) -> dict:
    cs = cands[cands.n == n]
    m, ch, ind = M[n], C[n], I[n]
    coalitions, parties = set(cs.coalition), set(cs.party)
    ph = (1 - W_CONTINUITY) * (X[n - 1] @ RATES["PH"]) + \
        W_CONTINUITY * (p21.PH[n] + PN_TO_PH * p21.PN[n] + PH_DRIFT) + swing
    bp = (1 - W_CONTINUITY) * (X[n - 1] @ RATES["BNPN"]) + \
        W_CONTINUITY * (p21.BN[n] + PN_TO_PACT * p21.PN[n]) - swing
    pact = cs[cs.coalition.isin(["BN", "PN"])]
    bparty = pact.party.iloc[0] if len(pact) else None
    # Pact candidate from PN: weaker UMNO->PN transfer (Ilham: 78% vs 91%)
    if bparty in ("PAS", "WAWASAN", "GERAKAN"):
        loss = m * 0.74 * 0.10 + (ch + ind) * 0.25 * (0.18 * ch + 0.42 * ind) / (ch + ind)
        bp -= loss
        ph += loss * 0.5
    if bparty in ("MCA", "MIC"):  # small Malay penalty for non-Malay pact candidate
        bp -= m * 0.74 * 0.04
        ph += m * 0.74 * 0.02
    v = {}
    if "BERSATU" in parties:
        if "PH" in coalitions:
            bs = 0.05 * m
            bp -= bs * 0.7
            ph -= bs * 0.3
        else:  # PH stood aside: ~60% of PH vote assumed to go to Bersatu
            bs = 0.05 * m + 0.6 * ph
            ph = 0
        v["BERSATU"] = bs
    if "BERSAMA" in parties:
        bm = 0.025 + 0.04 * (ch + ind)
        v["BERSAMA"] = bm
        ph -= bm * 0.75
        bp -= bm * 0.25
    if "PUTRA" in parties:
        v["PUTRA"] = 0.01
        bp -= 0.01
    if "BEBAS" in parties:
        v["BEBAS"] = 0.015
        bp -= 0.01
        if ph > 0:
            ph -= 0.005
    if bparty:
        v[bparty] = bp
    if "PH" in coalitions:
        v[cs[cs.coalition == "PH"].party.iloc[0]] = ph
    for _, r in cs.iterrows():
        if r["name"] in INCUMBENTS and r.party in v:
            v[r.party] += INCUMBENT_BONUS
    tot = sum(max(0, a) for a in v.values())
    v = {k: max(0, a) / tot for k, a in v.items()}
    (wp, ws), (rp, rs) = sorted(v.items(), key=lambda t: -t[1])[:2]
    cand = cs[cs.party == wp].iloc[0]
    return dict(n=n, seat=cs.seat_name.iloc[0], pred_party=wp, pred_coal=cand.coalition,
                pred_cand=cand["name"], share=ws, runner_up=rp, ru_share=rs,
                margin=ws - rs, shares=v)


def run(swing: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame([predict_seat(n, swing) for n in E.index]).set_index("n")


if __name__ == "__main__":
    cfg = json.load(open(INPUT / "config.json"))
    rationale = json.load(open(INPUT / "rationale.json"))
    th = cfg["confidence_thresholds_pts"]
    df = run()
    s = load_stats()
    w21 = b[(b.election == "SE-15") & (b.result == "won")].set_index("n")
    rows = []
    for n, r in df.iterrows():
        mpts = r.margin * 100
        conf = ("Safe" if mpts >= th["Safe"] else "Likely" if mpts >= th["Likely"]
                else "Lean" if mpts >= th["Lean"] else "Toss-up")
        conf = cfg["confidence_overrides"].get(str(n), conf)
        rows.append({
            "seat_no": f"N{n}", "seat": r.seat,
            "malay_pct": round(E.Malay[n] * 100, 1), "chinese_pct": round(E.Chinese[n] * 100, 1),
            "indian_pct": round(E.Indian[n] * 100, 1),
            "winner_2021": f"{w21.party[n]} ({w21.coalition[n]})",
            "bn_2021_pct": round(p21.BN[n] * 100, 1), "ph_2021_pct": round(p21.PH[n] * 100, 1),
            "pn_2021_pct": round(p21.PN[n] * 100, 1),
            "pred_party": r.pred_party, "pred_coalition": r.pred_coal, "pred_candidate": r.pred_cand,
            "pred_share_pct": round(r.share * 100, 1), "runner_up": r.runner_up,
            "runner_up_share_pct": round(r.ru_share * 100, 1), "pred_margin_pts": round(mpts, 1),
            "confidence": conf,
            "pred_shares_pct": json.dumps({k: round(x * 100, 1) for k, x in
                                           sorted(r.shares.items(), key=lambda t: -t[1])}),
            "rationale": rationale.get(str(n), ""),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "prediction_se16.csv", index=False)
    out.to_json(OUT / "prediction_se16.json", orient="records", indent=1, force_ascii=False)
    print(out[["seat_no", "seat", "pred_party", "pred_coalition", "pred_margin_pts", "confidence"]]
          .to_string(index=False))
    print("Seat tally:", out.pred_party.value_counts().to_dict())
    print("Coalition tally:", out.pred_coalition.value_counts().to_dict())
    for sw in (-0.03, 0.03, 0.05, 0.08):
        d = run(sw)
        print(f"Sensitivity, PH swing {sw:+.0%}: {d.pred_coal.value_counts().to_dict()}")
