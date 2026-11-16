# Melaka state election 2026 (SE-16): seat-by-seat prediction

Model-based forecast of all 28 Melaka DUN seats for polling on 14 Nov 2026, made on
13 Nov 2026, then scored against the official results on 15 Nov 2026.

**Result: 28/28 winners called correctly.** The predicted party tally was exact
(UMNO 18, DAP 4, MCA 2, PAS 2, MIC 1, Wawasan 1). By coalition: BN 21, PN 3, PH 4.

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python 01_download_clean.py          # downloads boundary GeoJSON; --refresh re-downloads the CSVs too
python 02_model_predict.py           # -> outputs/prediction_se16.csv / .json
python 03_map.py                     # -> outputs/melaka_se16_prediction_map.png
python 04_actual_vs_predicted.py     # -> scorecard, actual-vs-predicted, Bersama and Bemban analyses
# optional: python 00_fetch_ethnic_mix.py [--write]   rebuild ethnic mix from Wikipedia
```

Note: `--refresh` pulls the latest electiondata.my files. The model only reads the SE-15 (2021)
results and the SE-16 candidate list, so the prediction is the same with or without SE-16 results.

## Files

| Path | What |
|---|---|
| `common.py` | Paths, seat-number cleaning, party-to-bloc mapping |
| `data/raw/` | electiondata.my snapshots (downloaded 15 Nov 2026): Melaka ballots and stats, Johor ballots |
| `data/input/ethnic_mix_2026.json` | Electorate ethnic mix per seat (Wikipedia, citing China Press 2026; Telok Mas = 2021 figure) |
| `data/input/config.json` | Confidence thresholds and manual overrides |
| `data/input/rationale.json` | Per-seat written rationale used on the prediction page |
| `outputs/` | Prediction, map, scorecard and analysis CSVs |

## Method

1. **Seat cleaning.** Seats appear as `N.01 Kuala Linggi` (ballots, stats) and `code_dun = N.01`
   (map). The number is extracted with a regex (`N\.?\s*0*(\d+)`) to 1-28 and used as the join key.
   Only 2004 onward is used: before the 2003 redelineation Melaka had 20 seats (1959-1990), then
   25 (1995-1999), so the same N-number meant a different place. Three seats renamed in 2018 are
   treated as continuous: N8 Machap to Machap Jaya, N15 Bachang to Pengkalan Batu, N17 Bukit Baru
   to Bukit Katil.
2. **Coalition mapping.** BN = UMNO, MCA, MIC. PH = PKR, DAP, Amanah (in 2018 PH also included
   Bersatu; in 2008-2013 DAP, PKR and PAS ran as BA/PR). PN in 2021 = Bersatu, PAS, Gerakan.
   In 2026 BN and PN ran as a no-clash pact (BN 23 seats, PN 5: PAS, Gerakan, Wawasan), Bersatu
   ran alone (7 seats), and Bersama (Rafizi Ramli's party) was new (16 seats).
3. **Continuity + ethnic blend.** Each seat's projected shares are 50% its 2021 result
   (PH keeps its 2021 share + 1 pt + 5% of the 2021 PN vote; the pact gets BN + 85% of PN) and 50%
   an ethnic-rate model with assumed 2026 rates (benchmarked on the 2026 Johor and Negeri Sembilan
   elections and Ilham Centre's survey). PH gets 15% of Malay, 78% of Chinese and 55% of Indian
   voters; the pact gets 84%, 21% and 44%.
4. **Pact transfer and minor-party rules.**
   - If the pact candidate is from PN, cut its Malay vote by 10% (Ilham: 78% of BN voters back PN
     vs 91% the other way) and lose a quarter of its non-Malay vote.
   - If it is MCA or MIC in a Malay-majority seat, apply a small Malay penalty.
   - Bersatu takes 5% of Malay voters, plus 60% of PH's vote where PH stood aside.
   - Bersama takes 2.5% plus 4% x the non-Malay share, mostly from PH.
   - Putra and independents get small fixed shares; incumbents +2 pts. Shares are then normalised.
5. **Call and confidence.** Winner = highest share (first past the post). Margin of 30+ pts =
   Safe, 18-30 = Likely, 8-18 = Lean, under 8 = Toss-up, with manual overrides in `config.json`.

## Scorecard (actual vs predicted)

| | Value |
|---|---|
| Winners correct | 28 / 28 |
| BN+PN pact share, mean abs. error (28 seats) | 4.6 pts (actual 1.9 pts above model on average) |
| PH share, mean abs. error (24 seats) | 4.4 pts (actual 3.9 pts below model) |
| Bersatu share error (7 seats) | 6.9 pts |
| Bersama share error (16 seats) | 2.4 pts |
| Statewide pact / PH / Bersama / Bersatu | predicted 60.0 / 33.6 / 2.9 / 3.3% vs actual 63.2 / 29.3 / 3.9 / 3.2% |
| Turnout | 71.8% (65.8% in 2021) |

Biggest margin misses (predicted vs actual, pts): Pantai Kundor 55.2 vs 18.4 (Bersatu 40.8%
in a straight fight), Asahan 38.9 vs 64.0, Duyong 25.4 vs 50.0, Bukit Katil 9.5 vs 26.2
(called a toss-up), Merlimau 44.4 vs 59.4, Rim 41.9 vs 56.3.

## Proposed refinements

- **Drop the PN-candidate penalty.** PAS beat its modelled share in Bukit Katil and Paya Rumput;
  transfer between pact partners was close to complete.
- **Lower PH's Malay rate** from 15% to about 10-12%. PH fell short of the model in 21 of its 24 seats.
- **Bersatu:** in a straight fight with the pact, give it the whole non-pact pool. In multi-cornered
  seats it got 4-12%.
- **Bersama:** about right in Malay seats; raise it in Chinese-majority urban seats (5.5-9.9% actual
  vs 4.8-5.7% modelled). Where PH stands aside, Bersama can absorb much of the PH vote (Bemban 22.5%).
- **Differential turnout:** rural Malay seats voted at 75-80%, Chinese urban seats at 58-67%.
- **Widen the confidence bands:** every Lean or Toss-up seat was won by 21+ pts.

## Bersama: Melaka vs Johor (`outputs/bersama_melaka_vs_johor.csv`)

| State election | Bersama votes | Statewide share | Seats contested | Share where contested | Deposits lost |
|---|---|---|---|---|---|
| Melaka, 14 Nov 2026 | 19,176 / 488,737 | 3.92% | 16 / 28 | 5.93% (4.93% excl. Bemban) | 15 / 16 |
| Johor, 11 Jul 2026 | 28,816 / 1,874,918 | 1.54% | 15 / 56 | 3.39% | 15 / 15 |

## N24 Bemban (`outputs/bemban_history.csv`, `bemban_vote_flow.csv`, `bersama_by_seat.csv`)

PH did not stand in Bemban in 2026; it stood aside for Bersatu. The BN+PN pact held roughly its 2021
combined share (64.6% vs 66.5%). Bersama took 22.5%, against about 4.3% expected from its
performance in seats where PH stood (2.6% in Gadek, the closest ethnic match). That gap of about
18 pts is close to PH's 2021 share of 25.4%. Bersatu got only 11.5%. Reading: Bersama's Bemban vote
most likely came mainly from 2021 PH/DAP voters, plus some new voters, with little sign of large
BN/PN leakage. This is an inference from seat totals only; polling-district or survey data would be
needed to confirm how individual voters moved.

## Sources

- **Primary data: [ElectionData.my](https://electiondata.my) by Thevesh Theva.** Ballots, seat statistics and DUN boundaries are all from this open dataset. Credit and thanks to Thevesh.

- electiondata.my: `headline_ballots_state_mlk`, `headline_stats_state_mlk`, `headline_ballots_state_jhr`,
  `peninsular_2018_dun`
- Wikipedia constituency pages (electorate ethnic mix, citing China Press 2026)
- Ilham Centre survey (NST / FMT / Malay Mail, 13 Nov 2026); Ong Kian Ming projection (TRP, 13 Nov 2026)
- Johor (Jul 2026) and Negeri Sembilan (Aug 2026) state election results
