"""Compare la conversion Leaguepedia -> format Oracle's Elixir aux chiffres d'Oracle's Elixir, sur les mêmes parties.
Lit pipeline/lp_games_check_<année>.csv.gz (parties de LEC converties par fetch_lp_games.py --check N) et le fichier Oracle's Elixir.

    python tools/check_lp_games.py [année] [dossier des CSV]
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
year = sys.argv[1] if len(sys.argv) > 1 else '2026'
raw = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', 'data', 'raw')
L = pd.read_csv(os.path.join(HERE, '..', 'pipeline', f'lp_games_check_{year}.csv.gz'), low_memory=False)
O = pd.read_csv(os.path.join(raw, f'{year}_LoL_esports_match_data_from_OraclesElixir.csv'), low_memory=False)
O = O[O.gameid.isin(set(L.gameid))]
k = ['gameid', 'side', 'position']
M = L.merge(O, on=k, suffixes=('_lp', '_oe'))
print(f'{L.gameid.nunique()} parties converties, {O.gameid.nunique()} retrouvées chez Oracle\'s Elixir, {len(M)} lignes comparées')
same = lambda a, b: (M[a + '_lp'].astype(str).str.lower() == M[b + '_oe'].astype(str).str.lower()).mean()
print(f'même pseudo : {same("playername", "playername"):.0%}, même champion : {same("champion", "champion"):.0%}, même équipe : {same("teamname", "teamname"):.0%}')
cols = ['result', 'kills', 'deaths', 'assists', 'teamkills', 'damagetochampions', 'dpm', 'damageshare', 'damagetakenperminute', 'totalgold', 'earnedgold',
        'earned gpm', 'earnedgoldshare', 'cspm', 'vspm', 'wpm', 'wcpm', 'controlwardsbought', 'golddiffat10', 'golddiffat15', 'xpdiffat15', 'csdiffat15',
        'killsat15', 'assistsat15', 'deathsat15', 'firstbloodkill', 'dragons', 'barons', 'void_grubs', 'turretplates', 'firstdragon', 'firstherald', 'gamelength']
for c in cols:
    if c + '_lp' not in M or c + '_oe' not in M: continue
    a, b = pd.to_numeric(M[c + '_lp'], errors='coerce'), pd.to_numeric(M[c + '_oe'], errors='coerce'); m = a.notna() & b.notna()
    if m.sum() < 5: print(f'  {c:22s} trop peu de valeurs ({m.sum()})'); continue
    r = np.corrcoef(a[m], b[m])[0, 1] if a[m].std() > 0 and b[m].std() > 0 else float('nan')
    print(f'  {c:22s} n={m.sum():4d}  corrélation {r:6.3f}  écart moyen {np.mean(a[m] - b[m]):+10.3f}  écart absolu moyen {np.mean(abs(a[m] - b[m])):9.3f}  (moyenne OE {b[m].mean():.3f})')
