"""Power ranking attendu d'après les effectifs : validé sur les saisons passées (novembre 2026).

    python tools/bench_rosters.py            # depuis la racine du dépôt, avec data/raw/ ; environ 2 minutes

Pour chaque équipe d'une ligue en saison N+1 : effectif d'ouverture (joueur le plus aligné à chaque poste sur ses 10
premières parties de ligue), niveau attendu = moyenne des notes de saison N de ces cinq joueurs. Un joueur sans note en
N (recrue, joueur venu d'une ligue sans données) reçoit une valeur par défaut, choisie ici. Jugé contre le niveau réel
de l'équipe sur toute la saison N+1 (corrélation de rang dans chaque ligue, et erreur en points de note), comparé à la
méthode naïve « même niveau que l'équipe en N » (une équipe nouvelle prend la moyenne de sa ligue).
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B

ROLES = B.ROLES
to_note = lambda v: B.to_note(v, B.SCALE_A, B.SCALE_B)


def opening(S1):
    """Effectif d'ouverture de chaque équipe en N+1 : le plus aligné à chaque poste sur ses 10 premières parties de ligue."""
    p = S1['p']; dom = p[~p.league.isin(S1['cups'])]
    first = dom.drop_duplicates(['gameid', 'tid']).sort_values('date').groupby('tid').head(10)[['gameid', 'tid']]
    q = dom.merge(first, on=['gameid', 'tid'])
    ro = q.groupby(['tid', 'role', 'pid']).size().reset_index(name='k').sort_values('k').groupby(['tid', 'role']).pid.last().unstack()
    return ro.reindex(columns=ROLES)


def expected(roster, notes, fill):
    v = roster.apply(lambda c: c.map(notes))
    return v.fillna(fill.reindex(roster.index).to_frame().values @ np.ones((1, len(ROLES)))).mean(axis=1) if hasattr(fill, 'reindex') else v.fillna(fill).mean(axis=1)


def next_lines(y):
    """Note en ligue majeure la saison suivante, d'après la note de N : une droite pour les joueurs déjà en ligue majeure,
    une pour ceux qui montent d'un niveau inférieur (au moins 15 parties de chaque côté). Tient compte du retour vers la
    moyenne : un joueur très bien noté une saison l'est en moyenne un peu moins la suivante."""
    A0, A1 = T.rated(T.season(y)), T.rated(T.season(y + 1))
    j = A0[A0.n >= 15].join(A1[(A1.n >= 15) & (A1.tier == 0)][['pts']], rsuffix='_1', how='inner')
    x, z = j.pts.map(to_note), j.pts_1.map(to_note)
    return {k: tuple(np.polyfit(x[m], z[m], 1)[::-1]) + (int(m.sum()),) for k, m in (('maj', j.tier == 0), ('low', j.tier > 0))}


def run(y):
    S0, S1 = T.season(y), T.season(y + 1)
    A0 = T.rated(S0); notes = A0.pts.map(to_note)
    lg1 = pd.Series(S1['team_recent']).combine_first(pd.Series(S1['team_home']))
    R1 = pd.Series(S1['R']).map(to_note)
    ros = opening(S1)
    ros = ros[ros.index.map(lambda t: isinstance(lg1.get(t), str) and B.tier_of(lg1[t]) == 0 and not str(t).endswith(B.REMANIEE))]
    ros = ros.dropna(how='any')
    lg = lg1.reindex(ros.index)
    # valeurs par défaut pour un joueur sans note en N : centiles des notes N des titulaires de la ligue
    st = ros.stack().map(notes).groupby(lg.reindex(ros.stack().index.get_level_values(0)).values)
    R0 = pd.Series(S0['R']).map(to_note)
    out = {}
    for q in (0.1, 0.25, 0.5):
        fill = lg.map(st.quantile(q))
        v = ros.apply(lambda c: c.map(notes)); n_unk = int(v.isna().sum().sum())
        out[f'moyenne des notes N, inconnu = {int(q * 100)}e centile de la ligue'] = v.apply(lambda c: c.fillna(fill)).mean(axis=1)
    # variante : note d'un joueur de deuxième ou troisième niveau convertie en note estimée en ligue majeure (droite de
    # l'onglet Cracks, ajustée sur la saison N : joueurs ayant joué aux deux niveaux)
    tr0 = B.tier_table(S0); tr0 = tr0[tr0.n >= 15]
    w = tr0.pivot_table(index='pid', columns='tier', values='pts', aggfunc='first').dropna(subset=[0, 1]) if 1 in set(tr0.tier) else None
    sl, ic = np.polyfit(w[1].map(to_note), w[0].map(to_note), 1)
    conv = notes.where(A0.tier == 0, ic + sl * notes)
    fill = lg.map(st.quantile(0.25))
    out['notes N converties au niveau majeur, inconnu = 25e centile'] = ros.apply(lambda c: c.map(conv)).apply(lambda c: c.fillna(fill)).mean(axis=1)
    # variante : droites « saison suivante » réglées sur l'AUTRE paire de saisons (retour vers la moyenne, montées)
    Lw = next_lines(2025 if y == 2024 else 2024)
    print(f'  droites réglées sur l\'autre paire : majeure {Lw["maj"][0]:.1f} + {Lw["maj"][1]:.2f} x ({Lw["maj"][2]} joueurs), '
          f'montée {Lw["low"][0]:.1f} + {Lw["low"][1]:.2f} x ({Lw["low"][2]})')
    nx = pd.Series(np.where(A0.tier == 0, Lw['maj'][0] + Lw['maj'][1] * notes, Lw['low'][0] + B.LOW_SHIFT + Lw['low'][1] * notes), index=notes.index)
    fill_n = lg.map(ros.stack().map(nx).groupby(lg.reindex(ros.stack().index.get_level_values(0)).values).quantile(0.25))
    out['droites saison suivante (autre paire), inconnu = 25e centile'] = ros.apply(lambda c: c.map(nx)).apply(lambda c: c.fillna(fill_n)).mean(axis=1)
    # variantes : saison N-1 mêlée à N au prorata des parties (N-1 comptée alpha fois), avec ou sans conversion
    Am = T.rated(T.season(y - 1)); nm_ = Am.pts.map(to_note)
    for alpha in (0.25, 0.5, 1.0):
        n0 = A0.n; n1 = (alpha * Am.n).reindex(A0.index.union(Am.index)).fillna(0)
        for lab, base in (('sans conversion', notes), ('convertie', conv)):
            idx = base.index.union(nm_.index)
            bv, mv = base.reindex(idx), nm_.reindex(idx)
            w0, w1 = n0.reindex(idx).fillna(0).where(bv.notna(), 0), n1.reindex(idx).fillna(0).where(mv.notna(), 0)
            mix = (w0 * bv.fillna(0) + w1 * mv.fillna(0)) / (w0 + w1).replace(0, np.nan)
            out[f'N + N-1 x{alpha}, {lab}'] = ros.apply(lambda c: c.map(mix)).apply(lambda c: c.fillna(fill)).mean(axis=1)
    out['naïf : niveau de l\'équipe en N'] = R0.reindex(ros.index).fillna(lg.map(R0.groupby(pd.Series(S0['team_home'])).mean()))
    rows = []
    for k, pred in out.items():
        rs, err = [], []
        for l, idx in lg.groupby(lg).groups.items():
            if len(idx) < 6: continue
            a, b = pred.reindex(idx), R1.reindex(idx)
            rs.append(a.rank().corr(b.rank())); err.append((a - a.mean() - (b - b.mean())).abs().mean())
        rows.append({'saisons': f'{y}->{y + 1}', 'méthode': k, 'ligues': len(rs), 'corrélation de rang moyenne': np.mean(rs),
                     'erreur moyenne (points, à moyenne de ligue égale)': np.mean(err)})
    print(f'{y} -> {y + 1} : {len(ros)} équipes de ligue majeure, {n_unk} titulaires sans note en {y}')
    return pd.DataFrame(rows)


if __name__ == '__main__':
    res = pd.concat([run(2024), run(2025)])
    with pd.option_context('display.width', 200):
        print(res.round(3).to_string(index=False))
