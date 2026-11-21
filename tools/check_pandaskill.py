"""PandaSkill (PandaScore, arXiv 2501.10049) jugé sur notre test des transferts (novembre 2026).

    python tools/check_pandaskill.py /chemin/vers/PandaSkill      # dépôt cloné, fichiers Git LFS récupérés

PandaSkill publie ses notes partie par partie, de septembre 2019 au 15 septembre 2024 (dernières régions avant les
Worlds 2024). On prend la note de chaque joueur après sa dernière partie de 2024 : la note prudente qu'ils classent
(μ − 3σ) et la moyenne μ. Juge : les parties de 2025 des effectifs remaniés, comme tools/bench_transfers.py, sur la seule
paire 2024 -> 2025 (échelle réglée par deux moitiés de matchs). Pour comparer à données égales, la note Rift Scout est
aussi recalculée sur les seules parties de 2024 jouées jusqu'au 15 septembre. Joueurs reliés par pseudo et poste.
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import bench_transfers as T, build as B

PS = sys.argv[1] if len(sys.argv) > 1 else '/tmp/PandaSkill'
D = os.path.join(PS, 'pandaskill', 'artifacts', 'data')
rd = lambda f: pd.read_csv(os.path.join(D, f + '.real') if os.path.exists(os.path.join(D, f + '.real')) else os.path.join(D, f))
CUT = pd.Timestamp('2024-09-15 23:59')
ROLE = {'top': 'Top', 'jungle': 'Jungle', 'mid': 'Mid', 'bot': 'ADC', 'adc': 'ADC', 'support': 'Support'}


def pandaskill_ratings():
    R = rd('app/pandaskill_skill_ratings.csv')
    meta = rd('raw/game_metadata.csv')[['game_id', 'date']]
    ps = rd('raw/game_players_stats.csv')[['game_id', 'player_id', 'player_name', 'role']]
    R = R.merge(meta, on='game_id').merge(ps, on=['game_id', 'player_id'])
    R['date'] = pd.to_datetime(R.date, format='mixed')
    R = R[(R.date >= '2024-01-01') & (R.date <= CUT)].sort_values('date')
    last = R.groupby('player_id').tail(1)
    n24 = R.groupby('player_id').size()
    last = last.assign(n=last.player_id.map(n24), role=last.role.str.lower().map(ROLE))
    return last[['player_name', 'role', 'n', 'skill_rating_after', 'skill_rating_after_mu']]


def link(last, A):
    """pseudo + poste -> identifiant Rift Scout (un seul candidat)."""
    key = A.assign(k=A.name.str.lower() + '|' + A.role).reset_index().groupby('k').pid.agg(list)
    out = {}
    for r in last.itertuples():
        c = key.get(f'{str(r.player_name).lower()}|{r.role}', [])
        if len(c) == 1: out[c[0]] = r
    return out


if __name__ == '__main__':
    last = pandaskill_ratings()
    S = T.season(2024); A = T.rated(S)
    L = link(last, A)
    print(f'PandaSkill : {len(last)} joueurs notés en 2024, {len(L)} reliés à un joueur Rift Scout (sur {len(A)} notés)')
    theta = pd.Series({k: v.skill_rating_after for k, v in L.items()}); mu = pd.Series({k: v.skill_rating_after_mu for k, v in L.items()})
    # Rift Scout sur les seules parties de 2024 jusqu'au 15 septembre
    _load = B.load; T.setup_year(2024); p0, t0 = _load(2024)
    B.load = lambda y: (p0[p0.date <= CUT].copy(), t0[t0.date <= CUT].copy())
    try: S_cut = B.season(2024, T.prior_for(2024))
    finally: B.load = _load; T.setup_year(None)
    rs_cut = T.rated(S_cut).pts.map(lambda v: B.to_note(v, B.SCALE_A, B.SCALE_B))
    methods = {'Rift Scout (2024 complet)': T.m_note,
               'Rift Scout (2024 jusqu\'au 15 sept.)': lambda S_, y: rs_cut,
               'Rift Scout (15 sept.), mêmes joueurs que PandaSkill': lambda S_, y: rs_cut.reindex(theta.index),
               'PandaSkill, note prudente (mu - 3 sigma)': lambda S_, y: theta,
               'PandaSkill, moyenne mu': lambda S_, y: mu}
    res = T.run((2024,), methods, ref='Rift Scout (2024 jusqu\'au 15 sept.)', verbose=False)
    with pd.option_context('display.width', 200):
        print(res.round(4).to_string(index=False))
    # couverture : part des joueurs alignés en 2025 (parties jugées) qui ont une note PandaSkill
    G = T.test_set(2024); ids = pd.Series([i for x in list(G.blue) + list(G.red) for i in x])
    print(f'joueurs alignés dans les parties jugées : {ids.isin(A.index).mean():.0%} notés par Rift Scout, {ids.isin(theta.index).mean():.0%} par PandaSkill (reliés)')
    maj = A[(A.tier == 0) & (A.n >= 20)]
    c = pd.DataFrame({'rs': rs_cut.reindex(maj.index), 'ps': mu.reindex(maj.index)}).dropna()
    print(f'corrélation de rang Rift Scout / PandaSkill (mu), ligues majeures 2024 : {c.rs.rank().corr(c.ps.rank()):.2f} ({len(c)} joueurs)')
