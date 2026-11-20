"""Niveaux de ligue : faut-il les laisser plus libres, ou partir d'autre chose que LoL Ratings ? (novembre 2026)

    python tools/check_league_priors.py      # depuis la racine du dépôt, avec data/raw/ ; environ 10 minutes

Juge : chaque tournoi entre régions (First Stand, MSI, EWC, Worlds, Demacia Cup internationale...) est caché à son tour,
le niveau des équipes est refait sur tout le reste de la saison (y compris les autres tournois), puis ses parties entre
régions sont prédites. C'est la situation réelle du modèle : les autres tournois servent, celui qu'on juge non.

Biais du juge à connaître : les niveaux de départ actuels (leagues.json) sont la moyenne des notes LoL Ratings de la
MÊME saison, calculées avec tous ses tournois, celui qu'on cache compris. Le juge favorise donc ces niveaux de départ.
Variante sans ce biais : les niveaux de ligue de Rift Scout de la saison précédente.

Mesures : log-loss sur les parties entre régions cachées, écart avec le modèle actuel et intervalle à 95 % (bootstrap
apparié par match) ; victoires de l'Occident (LEC, LCS) contre la LCK et la LPL, réelles et annoncées. Le facteur
d'étalement des niveaux (écart d'or) est celui du modèle publié, le même pour toutes les variantes.
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B

EAST, WEST = {'LCK', 'LPL'}, {'LEC', 'LCS'}


def prev_prior(y, cur):
    """Niveaux de ligue de Rift Scout de la saison précédente ; ligue absente : niveau actuel décalé de l'écart moyen."""
    lv = T.season(y - 1)['lvl']
    com = [l for l in cur if l in lv]
    shift = np.mean([lv[l] - cur[l] for l in com]) if com else 0.0
    return {l: float(lv.get(l, cur[l] + shift)) for l in cur}


def run_year(y, variants):
    S = T.season(y); t, home = S['t'], S['team_home']; reg = B.META['region']
    Cf = B._levels_core(t, S['cups'], T.prior_for(y))[0]
    k = float(np.polyfit(Cf - Cf.mean(), S['R'].reindex(Cf.index) - S['R'].reindex(Cf.index).mean(), 1)[0]); side = S['side']
    tl = t.assign(h=t.tid.map(home)); tl['r'] = tl.h.map(reg)
    inter = tl.groupby('gameid').r.agg(lambda x: x.dropna().nunique() == 2)
    evs = sorted(set(tl[tl.gameid.isin(inter[inter].index) & tl.league.isin(S['cups'])].league))
    rows = []
    for name, (prior, sdl) in variants.items():
        pri = prior(y); old = B.SD_LEAGUE; B.SD_LEAGUE = sdl
        try:
            for ev in evs:
                hid = set(tl.gameid[tl.league == ev])
                C = B._levels_core(t[~t.gameid.isin(hid)], S['cups'], pri)[0]
                R = C.mean() + k * (C - C.mean())
                g = tl[tl.gameid.isin(hid) & tl.gameid.isin(inter[inter].index)]
                b = g[g.side == 'Blue'].set_index('gameid'); r = g[g.side == 'Red'].set_index('gameid').reindex(b.index)
                for gid in b.index:
                    if b.tid[gid] not in R.index or r.tid[gid] not in R.index: continue
                    pb = 1 / (1 + np.exp(-((R[b.tid[gid]] - R[r.tid[gid]]) / B.PTS_PER_LOGIT + side))); yb = float(b.result[gid])
                    hb, hr = b.h[gid], r.h[gid]
                    west = hb in WEST and hr in EAST or hr in WEST and hb in EAST
                    w, pw = ((yb, pb) if hb in WEST else (1 - yb, 1 - pb)) if west else (np.nan, np.nan)
                    rows.append({'saison': y, 'variante': name, 'tournoi': ev, 'gameid': gid, 'match': f'{b.date[gid].date()}|{min(hb or "", hr or "")}|{ev}|{"|".join(sorted([b.tid[gid], r.tid[gid]]))}',
                                 'll': -(yb * np.log(pb) + (1 - yb) * np.log(1 - pb)), 'west': west, 'w': w, 'pw': pw})
        finally:
            B.SD_LEAGUE = old
    return pd.DataFrame(rows)


if __name__ == '__main__':
    cur = lambda y: T.prior_for(y)
    prev = lambda y: prev_prior(y, T.prior_for(y))
    V = {'actuel (LoL Ratings, SD_LEAGUE 90)': (cur, 90.0), 'LoL Ratings, SD_LEAGUE 150': (cur, 150.0),
         'saison précédente Rift Scout, SD_LEAGUE 90': (prev, 90.0), 'saison précédente, SD_LEAGUE 150': (prev, 150.0),
         'saison précédente, SD_LEAGUE 250': (prev, 250.0)}
    D = pd.concat([run_year(y, V) for y in (2025, 2026)])
    ref = 'actuel (LoL Ratings, SD_LEAGUE 90)'; rng = np.random.default_rng(0)
    for y in (2025, 2026, 'les deux'):
        Dy = D if y == 'les deux' else D[D.saison == y]
        base = Dy[Dy.variante == ref].set_index('gameid')
        codes, uniq = pd.factorize(base.match); boot = rng.integers(0, len(uniq), (2000, len(uniq)))
        print(f'\n== {y} : {len(base)} parties entre régions cachées ({len(uniq)} matchs), dont {int(base.west.sum())} Occident contre LCK/LPL')
        for v in V:
            x = Dy[Dy.variante == v].set_index('gameid').reindex(base.index)
            d = (x.ll - base.ll).values; per = np.bincount(codes, d, len(uniq)); cnt = np.bincount(codes, None, len(uniq))
            bs = np.array([per[i].sum() / cnt[i].sum() for i in boot])
            wst = x[x.west]
            print(f'  {v:45s} log-loss {x.ll.mean():.4f}  écart {d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f} ; {np.percentile(bs, 97.5):+.4f}]'
                  f'  | Occident {int(wst.w.sum())} victoires pour {wst.pw.sum():.1f}')
    W = D[(D.variante == ref) & D.west]
    print('\nModèle actuel, Occident contre LCK/LPL par tournoi caché :')
    print(W.groupby(['saison', 'tournoi']).agg(parties=('w', 'size'), victoires=('w', 'sum'), annoncées=('pw', 'sum')).round(1).to_string())
