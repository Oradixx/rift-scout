"""Note attendue la saison suivante dans chacun des trois calculs de la note (Rift Scout, mixte, unifiée), novembre 2026.

    python tools/bench_next_modes.py         # depuis la racine du dépôt, avec data/raw/ et LoL-ratings ; environ 4 minutes

Pour chaque calcul, sur ses propres notes : droites « déjà en ligue majeure » et « montée » réglées sur une paire de saisons,
poids de la saison d'avant (joueur déjà en ligue majeure dont la saison d'avant, 15 parties ou plus, s'est aussi jouée en
ligue majeure : valeur + poids × (note d'avant − note), sans constante) réglé sur la même paire, puis jugés sur l'autre
paire (2024 -> 2025 et 2025 -> 2026). Deux juges : l'erreur par joueur (écart quadratique, joueurs à 15 parties ou plus en
ligue majeure la saison suivante) et le power ranking attendu (protocole de tools/bench_rosters.py : effectifs d'ouverture
de N+1, corrélation de rang dans chaque ligue majeure et erreur à moyenne de ligue égale, contre le niveau d'équipe réel).
Les notes mixte et unifiée sont calculées comme dans build.py (même ramenée à l'échelle, même repli sur la note Rift Scout).
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import bench_transfers as T, build as B, bench_rosters as BR, unified as U

to_note = BR.to_note
YS = (2023, 2024, 2025, 2026)


def uni_note(S, A, y):
    T.setup_year(y)
    try: th = U.fit(S, T.prior_for(y), B.tier_of, {'with_se': False}, S['A'].Z)['theta'].reindex(A.index)
    finally: T.setup_year(None)
    ref = th.notna() & (A.n >= 15); k = A.pts[ref].std() / th[ref].std(); m = A.pts[ref].mean() - k * th[ref].mean()
    return (m + k * th).map(lambda v: to_note(v) if pd.notna(v) else np.nan).fillna(A.pts.map(to_note))


def main():
    SE = {y: T.season(y) for y in YS}; RA = {y: T.rated(SE[y]) for y in YS}
    NO = {}
    for y in YS:
        NO[('rift', y)] = T.m_note(SE[y], y); NO[('mix', y)] = T.m_mix(SE[y], y); NO[('uni', y)] = uni_note(SE[y], RA[y], y)

    def pair(mode, y):
        A0, A1, Am = RA[y], RA[y + 1], RA[y - 1]
        j = A0[A0.n >= 15][['tier']].join(A1[(A1.n >= 15) & (A1.tier == 0)][[]], how='inner')
        j['x'], j['z'] = NO[(mode, y)].reindex(j.index), NO[(mode, y + 1)].reindex(j.index)
        j['xm'] = NO[(mode, y - 1)].where((Am.n >= 15) & (Am.tier == 0)).reindex(j.index)
        return j.dropna(subset=['x', 'z'])

    def fit(mode, y):
        j = pair(mode, y); out = {}
        for k, m in (('maj', j.tier == 0), ('low', j.tier > 0)): b, a = np.polyfit(j[m].x, j[m].z, 1); out[k] = (a, b)
        g = j[(j.tier == 0) & j.xm.notna()]; r = g.z - (out['maj'][0] + out['maj'][1] * g.x); d = g.xm - g.x
        out['c'] = float((r * d).sum() / (d * d).sum()); out['r'], out['d'] = r, d
        return out

    rows, prow, lrow = [], [], []
    for y in (2024, 2025):
        S1 = SE[y + 1]; lg1 = pd.Series(S1['team_recent']).combine_first(pd.Series(S1['team_home'])); R1 = pd.Series(S1['R']).map(to_note)
        ros = BR.opening(S1)
        ros = ros[ros.index.map(lambda t: isinstance(lg1.get(t), str) and B.tier_of(lg1[t]) == 0 and not str(t).endswith(B.REMANIEE))].dropna(how='any')
        lg = lg1.reindex(ros.index); o = 2025 if y == 2024 else 2024; A0 = RA[y]; low = A0.tier > 0
        for mode in ('rift', 'mix', 'uni'):
            F, FR = fit(mode, o), fit('rift', o)
            j = pair(mode, y); g = j[(j.tier == 0) & j.xm.notna()]
            e_rs = g.z - (FR['maj'][0] + FR['maj'][1] * g.x); e0 = g.z - (F['maj'][0] + F['maj'][1] * g.x); e1 = e0 - F['c'] * (g.xm - g.x)
            prow.append({'calcul': mode, 'paire': f'{y}->{y + 1}', 'joueurs': len(g), 'poids (autre paire)': F['c'], 'droites Rift Scout': np.sqrt((e_rs ** 2).mean()),
                         'droites du calcul': np.sqrt((e0 ** 2).mean()), "+ saison d'avant": np.sqrt((e1 ** 2).mean())})
            gl = j[j.tier > 0]   # joueurs montés (droite « montée », celle de l'onglet Cracks)
            el_rs = gl.z - (FR['low'][0] + B.LOW_SHIFT + FR['low'][1] * gl.x); el = gl.z - (F['low'][0] + B.LOW_SHIFT + F['low'][1] * gl.x)
            lrow.append({'calcul': mode, 'paire': f'{y}->{y + 1}', 'joueurs montés': len(gl), 'droite Rift Scout': np.sqrt((el_rs ** 2).mean()),
                         'droite du calcul': np.sqrt((el ** 2).mean()), 'biais (calcul)': el.mean(), 'erreur médiane (calcul)': el.abs().median()})
            notes = NO[(mode, y)].reindex(A0.index)
            xm = NO[(mode, y - 1)].where((RA[y - 1].n >= 15) & (RA[y - 1].tier == 0)).reindex(A0.index); has = (~low) & xm.notna()

            def line(L, sh=B.LOW_SHIFT):
                return pd.Series(np.where(low, L['low'][0] + sh + L['low'][1] * notes, L['maj'][0] + L['maj'][1] * notes), index=notes.index)

            def evalv(label, nx):
                fill = lg.map(ros.stack().map(nx).groupby(lg.reindex(ros.stack().index.get_level_values(0)).values).quantile(0.25))
                pred = ros.apply(lambda c: c.map(nx)).apply(lambda c: c.fillna(fill)).mean(axis=1); rs, err = [], []
                for l, idx in lg.groupby(lg).groups.items():
                    if len(idx) < 6: continue
                    a, b = pred.reindex(idx), R1.reindex(idx); rs.append(a.rank().corr(b.rank())); err.append((a - a.mean() - (b - b.mean())).abs().mean())
                rows.append({'calcul': mode, 'paire': y, 'variante': label, 'rang': np.mean(rs), 'erreur': np.mean(err)})
            evalv('droites Rift Scout', line(FR)); base = line(F)
            for sh in (0, -2): evalv(f'droites du calcul, montée {sh:+d}', line(F, sh))
            evalv('droites du calcul (montée -1)', base)
            evalv("droites du calcul + saison d'avant", base.where(~has, base + F['c'] * (xm - notes)))
    with pd.option_context('display.width', 200):
        print('erreur par joueur (points), joueurs avec une saison d\'avant en ligue majeure')
        print(pd.DataFrame(prow).round(3).to_string(index=False))
        print('joueurs montés, droite « montée » (abaissée de LOW_SHIFT) :')
        print(pd.DataFrame(lrow).round(3).to_string(index=False))
        R = pd.DataFrame(rows)
        print(R.pivot_table(index=['calcul', 'variante'], columns='paire', values=['rang', 'erreur']).round(3).to_string())
        print(R.groupby(['calcul', 'variante'])[['rang', 'erreur']].mean().round(3).to_string())
    for mode in ('rift', 'mix', 'uni'):
        F = [fit(mode, y) for y in (2024, 2025)]; r = pd.concat([f['r'] for f in F]); d = pd.concat([f['d'] for f in F])
        print(f"{mode} : poids de la saison d'avant, deux paires réunies {(r * d).sum() / (d * d).sum():.3f} ({len(r)} joueurs)")


if __name__ == '__main__':
    main()
