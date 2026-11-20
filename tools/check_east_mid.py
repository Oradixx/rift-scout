"""Le milieu de tableau de la LCK et de la LPL est-il surévalué face aux meilleures équipes occidentales ? (novembre 2026)

    python tools/check_east_mid.py       # depuis la racine du dépôt, avec data/raw/ ; environ 3 minutes

Hypothèse testée : les équipes de LCK et de LPL qui jouent à l'international sont les meilleures de leur ligue ; le niveau
du reste de la ligue est déduit des matchs de ligue. Si l'écart entre le haut et le milieu y est sous-estimé, le milieu est
surévalué face à l'Occident. Test : toutes les parties entre une équipe de LEC ou de LCS et une équipe de LCK ou de LPL
sont cachées au modèle de niveau d'équipe, qui est refait sans elles ; on compare ensuite les victoires réelles de
l'Occident à celles annoncées, selon le rang de l'adversaire dans sa ligue (rang du modèle refait). Variantes : écart
interne de la LCK et de la LPL plus large (SD_TEAM_BY_LEAGUE).
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B

EAST, WEST = {'LCK', 'LPL'}, {'LEC', 'LCS'}
rows = []
for y in (2025, 2026):
    S = T.season(y); t, home = S['t'], S['team_home']
    lg = t.tid.map(home)
    other = t.assign(lg=lg).groupby('gameid').lg.agg(lambda x: tuple(sorted(x.dropna())))
    hid = set(other.index[other.map(lambda v: len(v) == 2 and len({*v} & EAST) == 1 and len({*v} & WEST) == 1)])
    VAR = {'actuel': ({}, None), 'LEC et LCS 250': ({'LEC': 250.0, 'LCS': 250.0}, None), 'LCK et LPL 325': ({'LCK': 325.0, 'LPL': 325.0}, None),
           'ligues plus libres (SD_LEAGUE 150)': ({}, 150.0), 'LEC et LCS 250 + SD_LEAGUE 150': ({'LEC': 250.0, 'LCS': 250.0}, 150.0)}
    Cf = B._levels_core(t, S['cups'], T.prior_for(y))[0]
    k = float(np.polyfit(Cf - Cf.mean(), S['R'].reindex(Cf.index) - S['R'].reindex(Cf.index).mean(), 1)[0])
    for sd, (upd, sdl) in VAR.items():
        old = dict(B.SD_TEAM_BY_LEAGUE); old_l = B.SD_LEAGUE; B.SD_TEAM_BY_LEAGUE.update(upd)
        if sdl: B.SD_LEAGUE = sdl
        # niveau refait sans les parties cachées ; ré-étalement (écart d'or) repris du modèle publié (approximation pour les variantes)
        try:
            sf = S['side']
            C, _, _, side, _ = B._levels_core(t[~t.gameid.isin(hid)], S['cups'], T.prior_for(y))
            R = C.mean() + k * (C - C.mean()); side = sf
        finally: B.SD_TEAM_BY_LEAGUE.clear(); B.SD_TEAM_BY_LEAGUE.update(old); B.SD_LEAGUE = old_l
        rank = {}
        for l in EAST:
            ids = [k for k in R.index if home.get(k) == l and not str(k).endswith(B.REMANIEE)]
            rank.update({k: i + 1 for i, k in enumerate(R[ids].sort_values(ascending=False).index)})
        g = t[t.gameid.isin(hid)]
        b = g[g.side == 'Blue'].set_index('gameid'); r = g[g.side == 'Red'].set_index('gameid').reindex(b.index)
        for gid in b.index:
            tb, tr, yb = b.tid[gid], r.tid[gid], float(b.result[gid])
            if tb not in R.index or tr not in R.index: continue
            pb = 1 / (1 + np.exp(-((R[tb] - R[tr]) / B.PTS_PER_LOGIT + side)))
            we, ea, w, pw = (tb, tr, yb, pb) if home.get(tb) in WEST else (tr, tb, 1 - yb, 1 - pb)
            wl = home.get(we); wr = R[[k for k in R.index if home.get(k) == wl and not str(k).endswith(B.REMANIEE)]].rank(ascending=False)
            rows.append({'saison': y, 'sd': sd, 'adversaire': 'top 4' if rank.get(ea, 99) <= 4 else 'hors top 4', 'v': w, 'att': pw,
                         'occident': 'top 2 de sa ligue' if wr.get(we, 99) <= 2 else 'hors top 2', 'compétition': b.league[gid],
                         'll': -(w * np.log(pw) + (1 - w) * np.log(1 - pw))})
D = pd.DataFrame(rows)
A0 = D[D.sd == 'actuel']
print('Modèle actuel, parties cachées, par compétition et par niveau des équipes :')
print(A0.groupby(['adversaire', 'occident']).agg(parties=('v', 'size'), victoires=('v', 'sum'), attendues=('att', 'sum')).round(1).to_string())
print(A0.groupby(['compétition', 'adversaire']).agg(parties=('v', 'size'), victoires=('v', 'sum'), attendues=('att', 'sum')).round(1).to_string())
out = D.groupby(['sd', 'adversaire']).agg(parties=('v', 'size'), victoires_occident=('v', 'sum'), attendues=('att', 'sum'), logloss=('ll', 'mean'))
out['écart'] = out.victoires_occident - out.attendues
out['écart-type'] = D.groupby(['sd', 'adversaire']).att.apply(lambda a: np.sqrt((a * (1 - a)).sum()))
print(out.round(3).to_string())
print(D.groupby('sd').ll.mean().round(4).to_string())
