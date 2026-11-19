"""Note unifiée par événement : l'écart propre à un événement est-il du signal ou du bruit ? (novembre 2026)

    python tools/check_event_unified.py      # depuis la racine du dépôt, avec data/raw/ ; environ 3 minutes

Dans chaque événement, les matchs sont partagés au hasard en deux moitiés A et B. Niveau de saison (note unifiée) refait
sans les parties B ; écart propre à l'événement estimé sur A avec différentes valeurs de TAU_EVENT ; prédiction des
parties B avec niveau de saison + écart, en log-loss. TAU_EVENT = 0 : pas d'écart (le niveau de saison seul).
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B, unified as U

TAUS = [0, 25, 35, 50, 75, 100, 150]

for y in (2025, 2026):
    S = T.season(y); p, t = S['p'], S['t']
    g = p.drop_duplicates('gameid')[['gameid', 'event', 'date']]
    tm = t.groupby('gameid').tid.agg(lambda x: '|'.join(sorted(x)))
    g['match'] = g.event + '|' + g.date.dt.date.astype(str) + '|' + g.gameid.map(tm)
    pick = pd.Series(np.random.default_rng(1).integers(0, 2, g.match.nunique()), index=g.match.unique())
    g['half'] = g.match.map(pick).values
    A_ids, B_ids = set(g.gameid[g.half == 0]), set(g.gameid[g.half == 1])
    S_A = {**S, 'p': p[p.gameid.isin(A_ids)], 't': t[t.gameid.isin(A_ids)]}
    o = U.fit(S_A, T.prior_for(y), B.tier_of, {'with_se': False}, S['A'].Z)
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
        res[tau] = -np.mean(yv * np.log(pr) + (1 - yv) * np.log(1 - pr))
    print(y, len(bl), 'parties B ; log-loss par TAU_EVENT :', {k: round(v, 4) for k, v in res.items()})
