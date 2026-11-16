# election_prediction

A home for Malaysian election prediction models: transparent, seat-by-seat models built from
public results data (mainly [electiondata.my](https://electiondata.my)), with the assumptions and
the post-election scorecard kept next to the code.

## Subprojects

| Folder | Election | Status |
|---|---|---|
| [`melaka_state_election/`](melaka_state_election/) | 16th Melaka state election (SE-16), 14 Nov 2026, 28 DUN seats | Prediction made 13 Nov 2026; scored against results: 28/28 winners correct |

## Conventions

- Each subproject has its own `README.md`, `requirements.txt`, numbered scripts and an `outputs/` folder.
- Small source snapshots are committed under `data/raw/`; large files (e.g. boundary GeoJSON) are downloaded by the scripts.
- Predictions are model-based estimates, not certainties.
