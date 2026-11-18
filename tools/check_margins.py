"""Marge de la note unifiée : de combien le niveau bouge-t-il avec un autre tirage des parties de la saison ? (novembre 2026)

    python tools/check_margins.py        # depuis la racine du dépôt, avec data/raw/ ; environ 4 minutes

Les matchs de chaque saison (2025, 2026) sont partagés au hasard en deux moitiés et tout le calcul (statistiques, puis
note unifiée) est refait sur chacune. L'écart entre les deux niveaux d'un joueur ne contient que du bruit de mesure (son
vrai niveau est le même dans les deux moitiés). On ajuste ce bruit sous la forme C / racine(parties), C réglé sur une
saison, puis vérifié sur l'autre : environ 68 % des joueurs doivent rester à moins d'une marge combinée, 95 % à moins
de 1,96. Le C retenu (moyenne des deux saisons) est NOISE_C dans pipeline/unified.py.
Ce que la marge ne couvre pas : l'erreur du modèle lui-même (par exemple l'ordre entre cinq coéquipiers qui jouent
toujours ensemble, que seules les statistiques départagent) ; un partage en deux moitiés ne peut pas la mesurer.
L'écart-type a posteriori du modèle (`se` de unified.fit) n'est pas affiché : il ignore le bruit des statistiques de
départ et repose surtout sur TAU, que ce test ne peut pas juger.
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import build as B, unified as U
B.RAW = os.path.join(ROOT, 'data', 'raw')


def halves(year, seed=0):
    """Niveau unifié de chaque joueur sur chacune des deux moitiés de matchs de la saison (statistiques comprises)."""
    _load = B.load
    p, t = _load(year)
    match = t.date.dt.date.astype(str) + '|' + t.groupby('gameid').tid.transform(lambda x: '|'.join(sorted(x)))
    m = pd.Series(match.values, index=t.gameid.values).groupby(level=0).first()
    pick = pd.Series(np.random.default_rng(seed).integers(0, 2, m.nunique()), index=m.unique())
    side = m.map(pick)
    out = []
    for h in (0, 1):
        keep = set(side.index[side == h])
        B.load = lambda y, keep=keep: (p[p.gameid.isin(keep)].copy(), t[t.gameid.isin(keep)].copy())
        try: S = B.season(year, B.META['prior'][str(year)])
        finally: B.load = _load
        o = U.fit(S, B.META['prior'][str(year)], B.tier_of, {'with_se': False}, S['A'].Z)
        out.append(pd.DataFrame({'theta': o['theta'], 'n': S['A'].n.reindex(o['theta'].index)}))
    j = out[0].join(out[1], lsuffix='_a', rsuffix='_b', how='inner')
    j = j[(j.n_a >= 10) & (j.n_b >= 10)]
    return pd.DataFrame({'d': j.theta_a - j.theta_b, 'v': 1 / j.n_a + 1 / j.n_b})


if __name__ == '__main__':
    H = {y: halves(y) for y in (2025, 2026)}
    C = {y: float(np.sqrt(np.mean(h.d ** 2 / h.v))) for y, h in H.items()}
    for y, h in H.items():
        o = 2026 if y == 2025 else 2025
        z = h.d / (C[o] * np.sqrt(h.v))
        print(f'{y} : {len(h)} joueurs à 10 parties ou plus dans chaque moitié ; C = {C[y]:.0f} points x racine(parties)')
        print(f'  avec le C de {o} : {(z.abs() < 1).mean():.0%} à moins d\'une marge (68 % attendus), '
              f'{(z.abs() < 1.96).mean():.0%} à moins de 1,96 (95 %) ; écart-type {z.std():.2f} (1 attendu)')
    print(f'C retenu (moyenne) : {np.mean(list(C.values())):.0f} ; pour 40 parties, marge de {np.mean(list(C.values())) / np.sqrt(40):.0f} points')
