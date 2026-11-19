"""Note unifiée par événement : de combien laisser l'écart propre à un événement s'éloigner de la saison ? (novembre 2026)

    python tools/check_event_unified.py      # depuis la racine du dépôt, avec data/raw/ ; environ 5 minutes

Dans chaque événement, les matchs sont partagés au hasard en deux moitiés A et B. Toute la saison (statistiques, niveaux,
note unifiée) est refaite sur les seules parties A : rien de B n'y entre. L'écart propre à l'événement est estimé sur A
avec différentes valeurs de TAU_EVENT, puis on prédit les parties B (niveau de saison + écart), en log-loss.
TAU_EVENT = 0 : pas d'écart (le niveau de saison seul). Première version (corrigée après relecture) : les statistiques de
départ venaient de toute la saison, B compris, ce qui faisait paraître l'écart inutile.
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B, unified as U

TAUS = [0, 35, 75, 100, 150, 200, 250]

for y in (2025, 2026):
    S = T.season(y); p, t = S['p'], S['t']
    g = p.drop_duplicates('gameid')[['gameid', 'event', 'date']]
    tm = t.groupby('gameid').tid.agg(lambda x: '|'.join(sorted(x)))
    g['match'] = g.event + '|' + g.date.dt.date.astype(str) + '|' + g.gameid.map(tm)
    pick = pd.Series(np.random.default_rng(1).integers(0, 2, g.match.nunique()), index=g.match.unique())
    half = pd.Series(g.match.map(pick).values, index=g.gameid.values)
    A_ids = set(half.index[half == 0]); B_ids = set(half.index[half == 1])
    # saison refaite sur les seules parties A (mêmes identifiants de partie que dans le calcul complet)
    _load = B.load; T.setup_year(y); p0, t0 = _load(y)
    B.load = lambda yy: (p0[p0.gameid.isin(A_ids)].copy(), t0[t0.gameid.isin(A_ids)].copy())
    try: S_A = B.season(y, T.prior_for(y))
    finally: B.load = _load; T.setup_year(None)
    o = U.fit(S_A, T.prior_for(y), B.tier_of, {'with_se': False}, S_A['A'].Z)
    th = o['theta']
    q = p[p.gameid.isin(B_ids)][['gameid', 'side', 'pid', 'event']].drop_duplicates(['gameid', 'pid'])
    bl = t[(t.side == 'Blue') & t.gameid.isin(B_ids)].set_index('gameid').result
    res = {}
    for tau in TAUS:
        D = U.event_deltas(S_A, th, o['side'], tau) if tau else {}
        v = q.pid.map(th).fillna(th.median()).values + np.array([D.get((e, x), 0.0) for e, x in zip(q.event, q.pid)])
        s = pd.Series(np.where(q.side.values == 'Blue', 1, -1) * v / 5, index=q.gameid.values).groupby(level=0).sum()
        s = s.reindex(bl.index).dropna(); yv = bl.reindex(s.index).values.astype(float)
        pr = np.clip(1 / (1 + np.exp(-(s.values / U.PTS_PER_LOGIT + o['side']))), 1e-6, 1 - 1e-6)
        res[tau] = round(float(-np.mean(yv * np.log(pr) + (1 - yv) * np.log(1 - pr))), 4)
    print(y, len(bl), 'parties B ; log-loss par TAU_EVENT :', res, flush=True)
