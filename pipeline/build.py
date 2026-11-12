"""Rift Scout - calcul des notes.

Entrée  : data/raw/<année>_LoL_esports_match_data_from_OraclesElixir.csv (Oracle's Elixir)
Sortie  : rift-scout/app/data.json (lu par build_page.py)

La note d'un joueur (1-100) = niveau de son équipe + écart individuel.
  1. Niveau des équipes : un modèle de victoire (Bradley-Terry) sur tous les matchs de la saison, avec un
     niveau de ligue de départ ; les tournois internationaux recalent les ligues entre elles.
  2. Pour chaque partie, les stats du joueur sont comparées à celles des joueurs du même poste
     (et corrigées du champion joué), regroupées en facettes (lane, teamfight, dégâts...).
  3. On retire ce qui s'explique par l'écart de niveau entre les deux équipes : il reste ce que le joueur
     fait en plus ou en moins de ce qu'on attend à son poste dans ce contexte.
  4. Note = niveau d'équipe + écart individuel, convertie sur une échelle 1-100 commune à toutes les ligues.
"""
import json, os, sys, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1] if len(sys.argv) > 1 else 'data/raw'
OUT = os.path.join(HERE, '..', 'app', 'data.json')
META = json.load(open(os.path.join(HERE, 'leagues.json'), encoding='utf-8'))
SEASONS = [2025, 2026]

# ----------------------------------------------------------------------------- réglages
PTS_PER_LOGIT = 200      # écart de niveau moyen par joueur qui donne 73 % de victoire
SD_TEAM, SD_LEAGUE = 160.0, 90.0   # a priori : dispersion des équipes dans une ligue, incertitude sur le niveau des ligues
K_SHRINK = 12            # parties « fictives » au niveau moyen ajoutées à chaque joueur
SIGMA_IND = 100.0        # points : un écart-type d'écart individuel
SIGMA_FACET = 185.0      # points : un écart-type sur une facette
MIN_GAMES = 10
QUALIF_GAP_DAYS = 21     # jours sans match au-delà desquels un tournoi est coupé en « qualifications » puis tournoi
SD_EVENT = 250.0         # points : à quel point le niveau d'une équipe peut s'écarter de sa saison sur un événement
K_EVENT_IND = 5          # parties de saison ajoutées à l'écart individuel d'un événement
GAP_SAT = 250.0          # points : au-delà, un écart de niveau plus grand ne change presque plus les stats attendues
SLOPE_K = 1500           # parties : poids du niveau supérieur quand on estime le lien stats / écart de niveau d'une compétition
MIN_EVENT = 3
ROLE = {'top': 'Top', 'jng': 'Jungle', 'mid': 'Mid', 'bot': 'ADC', 'sup': 'Support'}
ROLES = ['Top', 'Jungle', 'Mid', 'ADC', 'Support']

# facette -> {stat: poids}; les stats sont des z-scores par poste (signe déjà orienté : plus = mieux)
FACETS = {
    'lane':   {'golddiffat15': .40, 'xpdiffat15': .30, 'csdiffat15': .20, 'golddiffat10': .10},
    'early':  {'ka15': .40, 'nd15': .25, 'fbp': .15, 'plates_diff': .10, 'p15': .10},
    'fight':  {'kp': .30, 'lkda': .30, 'ka_late': .20, 'nd_late': .20},
    'carry':  {'dpm': .40, 'damageshare': .30, 'dmg_per_gold': .15, 'kshare': .15},
    'eco':    {'cspm': .45, 'earned gpm': .40, 'earnedgoldshare': .15},
    'vision': {'vspm': .50, 'wcpm': .25, 'cwpm': .15, 'wpm': .10},
    'safe':   {'nd_pm': .50, 'nd_share': .50},
    'obj':    {'drag_share': .30, 'grubs_diff': .20, 'firstdragon': .10, 'firstherald': .10, 'baron_share': .30},
}
FACET_ROLE = {  # variantes par poste
    'Support': {'lane': {'duo_gd15': .50, 'xpdiffat15': .30, 'golddiffat15': .20},
                'carry': {'dpm': .6, 'damageshare': .4},
                'eco': {'earned gpm': 1.0}},
    'ADC': {'lane': {'golddiffat15': .35, 'xpdiffat15': .20, 'csdiffat15': .20, 'duo_gd15': .25}},
    'Jungle': {'lane': {'golddiffat15': .40, 'xpdiffat15': .35, 'csdiffat15': .25},
               'early': {'ka15': .40, 'nd15': .15, 'fbp': .20, 'grubs_diff': .15, 'firstdragon': .10}},
}
# poids des facettes dans la note générale, par poste
WEIGHTS = {
    'Top':     {'lane': .28, 'early': .07, 'fight': .21, 'carry': .16, 'eco': .12, 'vision': .03, 'safe': .13, 'obj': 0},
    'Jungle':  {'lane': .10, 'early': .20, 'fight': .24, 'carry': .10, 'eco': .07, 'vision': .09, 'safe': .08, 'obj': .12},
    'Mid':     {'lane': .24, 'early': .08, 'fight': .23, 'carry': .20, 'eco': .11, 'vision': .03, 'safe': .11, 'obj': 0},
    'ADC':     {'lane': .18, 'early': .05, 'fight': .23, 'carry': .27, 'eco': .13, 'vision': .02, 'safe': .12, 'obj': 0},
    'Support': {'lane': .17, 'early': .14, 'fight': .28, 'carry': .02, 'eco': 0, 'vision': .22, 'safe': .12, 'obj': .05},
}
CHAMP_ADJ = ['dpm', 'damageshare', 'dmg_per_gold', 'kshare', 'cspm', 'earned gpm', 'earnedgoldshare', 'vspm', 'wcpm', 'cwpm', 'wpm',
             'golddiffat15', 'xpdiffat15', 'csdiffat15', 'golddiffat10', 'duo_gd15', 'kp', 'lkda', 'nd_pm', 'nd_share', 'ka15', 'nd15',
             'ka_late', 'nd_late', 'p15', 'fbp']
STYLE = ['earnedgoldshare', 'damageshare', 'kshare', 'ka15', 'p15', 'dth_pm', 'dtshare', 'vspm', 'cspm', 'champ_carry', 'champ_tank']
PRETTY = {'WLDs': 'Worlds', 'FST': 'First Stand', 'EM': 'EMEA Masters', 'LCKC': 'LCK Challengers', 'LAS': 'LCK Academy Series',
          'AM': 'Asia Masters', 'DCup': 'Demacia Cup', 'NL': 'Nexus League', 'PRM': 'Prime League', 'AL': 'Arabian League',
          'CD': 'Circuito Desafiante', 'HM': 'Hitpoint Masters', 'HC': 'Hitpoint Challengers', 'RL': 'Rift Legends',
          'ROL': 'Road of Legends', 'LTA': 'LTA Championship', 'DCGI': 'Demacia Cup Global Invitational',
          'WSCI': 'World Star Challengers Invitational', 'HW': 'Hitpoint Winter'}
TIER_NAMES = ['Ligue majeure', 'Deuxième niveau', 'Troisième niveau']


def tier_of(lg):
    if lg in META['major']: return 0
    if lg in META['tier3']: return 2
    return 1


# ----------------------------------------------------------------------------- chargement
def load(year):
    f = os.path.join(RAW, f'{year}_LoL_esports_match_data_from_OraclesElixir.csv')
    d = pd.read_csv(f, low_memory=False)
    d['league'] = d['league'].map(lambda x: META['canon'].get(x, x))
    d['date'] = pd.to_datetime(d['date'], errors='coerce')
    d = d.drop_duplicates(['gameid', 'participantid']).dropna(subset=['result', 'date']).copy()
    d['tid'] = d.teamid.fillna(d.teamname)
    d = d.dropna(subset=['tid'])
    ok = d[d.position == 'team'].groupby('gameid').tid.nunique()
    d = d[d.gameid.isin(ok[ok == 2].index)]
    t = d[d.position == 'team'].copy()
    p = d[d.position != 'team'].copy()
    p['pid'] = p.playerid.fillna(('name:' + p.playername).where(p.playername.notna()))
    p = p.dropna(subset=['pid'])
    p['role'] = p.position.map(ROLE)
    return p, t


def detect_cups(t, min_teams=3, share=0.5):
    """Compétitions où la plupart des équipes jouent surtout ailleurs (Worlds, MSI, coupes...)."""
    g = t.groupby(['tid', 'league']).gameid.nunique().reset_index()
    home = g.sort_values('gameid').groupby('tid').league.last()
    q = t.drop_duplicates(['tid', 'league']).copy()
    q['foreign'] = q.tid.map(home) != q.league
    s = q.groupby('league').agg(n=('tid', 'size'), f=('foreign', 'mean'))
    return set(s[(s.n >= min_teams) & (s.f >= share)].index) | set(META['intl'])


# ----------------------------------------------------------------------------- niveau des équipes
def team_levels(t, cups, prior):
    dom = t[~t.league.isin(cups)]
    home = dom.groupby(['tid', 'league']).gameid.nunique().reset_index().sort_values('gameid').groupby('tid').league.last()
    teams = sorted(t.tid.unique())
    home = home.reindex(teams)
    fallback = np.mean([v for k, v in prior.items() if tier_of(k) == 1])
    lg_list = sorted(set(home.dropna()))
    pri = np.array([prior.get(home[x], fallback) if isinstance(home[x], str) else fallback for x in teams])
    ti = {x: i for i, x in enumerate(teams)}; li = {x: i for i, x in enumerate(lg_list)}
    b = t[t.side == 'Blue'].set_index('gameid'); r = t[t.side == 'Red'].set_index('gameid').reindex(b.index)
    nT, nL = len(teams), len(lg_list); n = len(b)
    X = np.zeros((n, nT + nL + 1))
    rows = np.arange(n)
    for side, sgn in ((b, 1.0), (r, -1.0)):
        idx = side.tid.map(ti).values
        np.add.at(X, (rows, idx), sgn)
        hl = side.tid.map(home).map(li)
        m = hl.notna().values
        np.add.at(X, (rows[m], nT + hl[m].astype(int).values), sgn)
    X[:, -1] = PTS_PER_LOGIT
    X /= PTS_PER_LOGIT
    off = (pri[b.tid.map(ti).values] - pri[r.tid.map(ti).values]) / PTS_PER_LOGIT
    y = b.result.values.astype(float)
    pen = np.r_[np.full(nT, 1 / SD_TEAM ** 2), np.full(nL, 1 / SD_LEAGUE ** 2), 0.0]
    beta = np.zeros(X.shape[1])
    for _ in range(30):
        eta = off + X @ beta; mu = 1 / (1 + np.exp(-eta)); w = mu * (1 - mu)
        H = X.T @ (X * w[:, None]) + np.diag(pen); gr = X.T @ (y - mu) - pen * beta
        step = np.linalg.solve(H, gr); beta += step
        if np.abs(step).max() < 1e-6: break
    R = pri + beta[:nT]
    for x, i in ti.items():
        if isinstance(home[x], str): R[i] += beta[nT + li[home[x]]]
    lvl = {l: float(prior.get(l, fallback) + beta[nT + i]) for l, i in li.items()}
    return pd.Series(R, index=teams), home, lvl, float(beta[-1])


# ----------------------------------------------------------------------------- stats par partie
def features(p, t):
    p = p.copy()
    mins = p.gamelength / 60
    late = (mins - 15).clip(lower=5)
    p['kp'] = (p.kills + p.assists) / p.teamkills.replace(0, np.nan)
    p['lkda'] = np.log((p.kills + p.assists + 1) / (p.deaths + 1))
    p['dth_pm'] = p.deaths / mins
    p['nd_pm'] = -p['dth_pm']
    p['nd_share'] = -(p.deaths / p.teamdeaths.replace(0, np.nan))
    p['kshare'] = p.kills / p.teamkills.replace(0, np.nan)
    p['ka15'] = p.killsat15 + p.assistsat15
    p['nd15'] = -p.deathsat15
    p['fbp'] = ((p.firstbloodkill.fillna(0) + p.firstbloodassist.fillna(0)) > 0).astype(float).where(p.firstbloodkill.notna())
    p['ka_late'] = (p.kills + p.assists - p.ka15) / late
    p['nd_late'] = -(p.deaths - p.deathsat15) / late
    p['dmg_per_gold'] = p.damagetochampions / p.earnedgold.replace(0, np.nan)
    p['cwpm'] = p.controlwardsbought / mins
    key = ['gameid', 'tid']
    g = p.groupby(key)
    p['dtshare'] = p.damagetakenperminute / g.damagetakenperminute.transform('sum').replace(0, np.nan)
    tk15 = g.killsat15.transform('sum')
    p['teamk15'] = tk15
    p['p15'] = (p.ka15 / tk15.replace(0, np.nan)).where(tk15 >= 2)
    duo = p[p.role.isin(['ADC', 'Support'])].groupby(key).golddiffat15.sum(min_count=2).rename('duo_gd15')
    p = p.merge(duo, left_on=key, right_index=True, how='left')
    tt = t.set_index(key)
    tm = pd.DataFrame({
        'drag_share': (tt.dragons / (tt.dragons + tt.opp_dragons).replace(0, np.nan)),
        'baron_share': (tt.barons / (tt.barons + tt.opp_barons).replace(0, np.nan)).fillna(.5).where(tt.barons.notna()),
        'grubs_diff': tt.void_grubs - tt.opp_void_grubs,
        'firstdragon': tt.firstdragon, 'firstherald': tt.firstherald,
        'plates_diff': tt.turretplates - tt.opp_turretplates,
        'team_gd15': tt.golddiffat15,
    })
    p = p.drop(columns=[c for c in tm.columns if c in p.columns]).merge(tm, left_on=key, right_index=True, how='left')
    return p


def zscores(p):
    """z-score par poste de chaque stat, après correction du champion joué."""
    stats = sorted({s for f in FACETS.values() for s in f} | {s for r in FACET_ROLE.values() for f in r.values() for s in f})
    Z = pd.DataFrame(index=p.index, columns=stats, dtype=float)
    for ro, q in p.groupby('role'):
        for s in stats:
            x = q[s].astype(float)
            if s in CHAMP_ADJ:
                cm = x.groupby(q.champion).agg(['mean', 'count'])
                dev = (cm['mean'] - x.mean()) * cm['count'] / (cm['count'] + 20)
                x = x - q.champion.map(dev).fillna(0)
            # comparé aux joueurs du même poste dans la même compétition (chaque ligue a son rythme : plus de
            # combats en LPL, plus de vision en LCK) ; le niveau de la ligue est compté à part, dans le niveau d'équipe
            lm = x.groupby(q.ctx).agg(['mean', 'count'])
            x = x - q.ctx.map((lm['mean'] - x.mean()) * lm['count'] / (lm['count'] + 30)).fillna(0)
            sd = x.std()
            Z.loc[q.index, s] = ((x - x.mean()) / sd).clip(-3, 3) if sd and sd > 0 else np.nan
    F = pd.DataFrame(index=p.index, columns=list(FACETS), dtype=float)
    for ro, q in p.groupby('role'):
        for f, base in FACETS.items():
            w = FACET_ROLE.get(ro, {}).get(f, base)
            num = sum(Z.loc[q.index, s].fillna(0) * wt for s, wt in w.items())
            den = sum(Z.loc[q.index, s].notna() * wt for s, wt in w.items())
            v = (num / den).where(den >= 0.5)
            F.loc[q.index, f] = (v - v.mean()) / v.std()
    return F


def champ_index(p):
    """profil moyen de chaque champion à un poste (indépendant du joueur) : part des dégâts, dégâts subis."""
    out = {}
    for ro, q in p.groupby('role'):
        for col, name in (('damageshare', 'champ_carry'), ('dtshare', 'champ_tank')):
            x = q[col]; cm = x.groupby(q.champion).agg(['mean', 'count'])
            v = x.mean() + (cm['mean'] - x.mean()) * cm['count'] / (cm['count'] + 10)
            out[(ro, name)] = v
    return out


def pct_rank(s):
    return s.rank(pct=True)


def to_note(pts, a, b):
    """linéaire, puis tassé en douceur au-dessus de 88 pour que 99 reste hors d'atteinte."""
    x = a + b * pts
    if x > 88: x = 88 + 11 * math.tanh((x - 88) / 11)
    return float(np.clip(x, 1, 99))


# ----------------------------------------------------------------------------- une saison
def season(year, prior):
    p, t = load(year)
    cups = detect_cups(t)
    R, team_home, lg_lvl, side_adv = team_levels(t, cups, prior)
    p = features(p, t)
    opp = t[['gameid', 'tid']].rename(columns={'tid': 'opp'})
    p = p.merge(opp, on='gameid'); p = p[p.tid != p.opp].reset_index(drop=True)
    p['R_own'] = p.tid.map(R); p['R_opp'] = p.opp.map(R); p['dR'] = p.R_own - p.R_opp
    # poste principal
    main = p.groupby(['pid', 'role']).size().reset_index(name='n').sort_values('n').groupby('pid').role.last()
    p = p[p.role == p.pid.map(main)].reset_index(drop=True)
    pretty = p.league.map(lambda x: PRETTY.get(x, x))
    # le segment fait partie du nom, y compris pour les tournois qui ont plusieurs éditions par an (EMEA Masters Winter...)
    p['event'] = np.where(p.split.isna() | p.split.astype(str).isin(['Season', 'nan']), pretty, pretty + ' ' + p.split.fillna('').astype(str))
    p['event'] = p.event.str.strip()
    # chaque partie : entre deux équipes de la même ligue, ou de ligues différentes ?
    # (une équipe sans ligue connue, invitée ou vue seulement en coupe, ne suffit pas à rendre un match « entre ligues »)
    h_own, h_opp = p.tid.map(team_home), p.opp.map(team_home)
    p['inter'] = h_own.notna() & h_opp.notna() & (h_own != h_opp)
    r_own, r_opp = h_own.map(META['region']), h_opp.map(META['region'])
    p['inter_reg'] = r_own.notna() & r_opp.notna() & (r_own != r_opp)      # entre deux régions (Corée, Chine, EMEA...)
    p['game_reg'] = r_own.fillna(r_opp).map(lambda x: {'Brésil & Amérique latine': 'Brésil'}.get(x, x))
    p['own_reg'] = r_own; p['own_home'] = h_own

    def scope_of(q):
        """portée d'un ensemble de parties d'après les équipes présentes : 'monde' (plusieurs régions), 'region' (plusieurs
        ligues d'une région) ou 'coupe' (une seule ligue ; une équipe invitée isolée ne change rien)."""
        def spread(col):
            v = q[col].dropna().value_counts(normalize=True); v = v[v >= 0.05]
            return len(v) >= 3 or (len(v) == 2 and v.min() >= 0.25)
        return 'monde' if spread('own_reg') else 'region' if spread('own_home') else 'coupe'
    MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    # Un tournoi joué en deux temps séparés de plusieurs semaines. Deux cas seulement justifient de le couper :
    #  - d'abord des matchs entre équipes d'une même ligue, puis le tournoi entre ligues : ce sont des qualifications régionales ;
    #  - deux phases entre ligues : ce sont deux éditions, on nomme la première par son mois.
    for ev in p.loc[p.league.isin(cups), 'event'].unique():
        m = p.event == ev
        days = np.sort(p.loc[m, 'date'].dt.normalize().unique())
        gaps = np.where(np.diff(days) > np.timedelta64(QUALIF_GAP_DAYS, 'D'))[0]
        if not len(gaps): continue
        cut = days[gaps[-1] + 1]
        early, late = m & (p.date < cut), m & (p.date >= cut)
        if scope_of(p[late]) != 'monde': continue                          # la fin n'est pas un tournoi entre régions : on ne coupe pas
        if p.loc[early, 'inter_reg'].mean() < 0.1: p.loc[early, 'event'] = ev + ', qualifications ' + p.loc[early, 'game_reg'].fillna('régionales')
        else: p.loc[early, 'event'] = ev + ', ' + MOIS[p.loc[early, 'date'].min().month - 1]
    # portée de chaque événement : international (entre régions), entre ligues d'une même région, coupe ou qualification
    # d'une seule ligue ou région, ou ligue
    is_cup = p.groupby('event').league.first().isin(cups)
    scope = pd.Series({ev: (scope_of(q) if is_cup[ev] else 'ligue') for ev, q in p.groupby('event')})
    p['scope'] = p.event.map(scope)
    p['big'] = (p.playoffs == 1) | p.scope.isin(['monde', 'region'])

    # Contexte de comparaison des stats. Des qualifications régionales se jouent entre équipes d'une même ligue, dans
    # les conditions de cette ligue : on les compare donc aux joueurs de cette ligue (qualifications EMEA de l'EWC = LEC),
    # pas à ceux du tournoi final.
    p['ctx'] = p.league
    for ev in [e for e in p.event.unique() if ', qualifications ' in e]:
        m = p.event == ev
        homes = p.loc[m, 'own_home'].dropna()
        if len(homes): p.loc[m, 'ctx'] = homes.value_counts().index[0]

    F = zscores(p)
    facets = list(FACETS)
    resid = pd.DataFrame(index=p.index, columns=facets, dtype=float)
    # Ce qu'on attend d'un joueur selon l'écart de niveau entre les deux équipes. Le lien n'est pas le même partout
    # (plus fort dans les petites ligues, plus faible en LEC ou à l'international) et il plafonne pour les gros écarts :
    # on l'estime donc par niveau de ligue, affiné par compétition, sur un écart de niveau tassé (tanh).
    p['xR'] = GAP_SAT * np.tanh(p.dR / GAP_SAT)
    p['grp'] = np.where(p.ctx.isin(cups), -1, p.ctx.map(tier_of))
    slopes = {}

    def fit(x, yv):
        m = yv.notna()
        return (float(np.cov(x[m], yv[m])[0, 1] / x[m].var()), int(m.sum())) if m.sum() > 50 and x[m].var() > 0 else (None, int(m.sum()))
    for ro, q in p.groupby('role'):
        for f in facets:
            b0, _ = fit(q.xR, F.loc[q.index, f]); b0 = b0 or 0.0
            slopes[(ro, f)] = b0
            b_row = pd.Series(b0, index=q.index)
            for g_, qg in q.groupby('grp'):
                bt, nt = fit(qg.xR, F.loc[qg.index, f])
                bt = b0 if bt is None else (nt * bt + SLOPE_K * b0) / (nt + SLOPE_K)
                slopes[(ro, f, int(g_))] = bt
                b_row.loc[qg.index] = bt
                for lg_, ql in qg.groupby('ctx'):
                    bl, nl = fit(ql.xR, F.loc[ql.index, f])
                    if bl is not None: b_row.loc[ql.index] = (nl * bl + SLOPE_K * bt) / (nl + SLOPE_K)
            resid.loc[q.index, f] = F.loc[q.index, f] - b_row * q.xR
    for f in facets: p['r_' + f] = resid[f]; p['z_' + f] = F[f]
    W = pd.DataFrame(WEIGHTS).T
    wmat = W.loc[p.role, facets].values
    rv = resid[facets].values
    ok = ~np.isnan(rv)
    p['c'] = np.where(ok, rv * wmat, 0).sum(1) / np.where(ok, wmat, 0).sum(1).clip(min=1e-9)
    p.loc[(np.where(ok, wmat, 0).sum(1) < 0.5), 'c'] = np.nan
    # ligue et équipe actuelles du joueur
    dom = p[~p.league.isin(cups)].sort_values('date')
    home = dom.groupby('pid').tail(20).groupby('pid').league.agg(lambda s: s.mode().iloc[0])
    last = p.sort_values('date').groupby('pid').agg(name=('playername', 'last'), tid=('tid', 'last'), team=('teamname', 'last'),
                                                    last_date=('date', 'max'), role=('role', 'last'))
    last['league'] = home.reindex(last.index)
    last['league'] = last.league.fillna(last.tid.map(team_home))
    last = last.dropna(subset=['league'])
    p = p[p.pid.isin(last.index)]

    # agrégats saison
    g = p.groupby('pid')
    n = g.size()
    A = pd.DataFrame({'n': n, 'T': g.R_own.mean(), 'Ropp': g.R_opp.mean(), 'c': g.c.mean()})
    shr = A.n / (A.n + K_SHRINK)
    A['c_s'] = A.c * shr
    for f in facets: A['r_' + f] = g['r_' + f].mean() * (g['r_' + f].count() / (g['r_' + f].count() + K_SHRINK))
    A['role'] = last.role; A = A.dropna(subset=['role'])
    q15 = A[A.n >= 15]
    sd_c = q15.groupby('role').c_s.std()
    A['I'] = A.c_s / A.role.map(sd_c)
    for f in facets:
        sd_f = q15.groupby('role')['r_' + f].std()
        A['i_' + f] = A['r_' + f] / A.role.map(sd_f)
    A['pts'] = A['T'] + SIGMA_IND * A.I
    for f in facets: A['p_' + f] = A['T'] + SIGMA_FACET * A['i_' + f]

    # ---- contexte : weakside / strongside (top, mid, adc), grands matchs, régularité, pool
    side = p[p.role.isin(['Top', 'Mid', 'ADC']) & p.p15.notna()].copy()
    lo = side.groupby('role').p15.transform(lambda s: s.quantile(.35)); hi = side.groupby('role').p15.transform(lambda s: s.quantile(.65))
    side['weak'] = side.p15 <= lo; side['strong'] = side.p15 >= hi
    side['wk_score'] = 0.6 * side.r_lane + 0.4 * side.r_safe
    side['st_score'] = 0.4 * side.r_lane + 0.4 * side.r_carry + 0.2 * side.r_fight
    wk = side[side.weak].groupby('pid').wk_score.agg(['mean', 'count']); st = side[side.strong].groupby('pid').st_score.agg(['mean', 'count'])
    for nm, d_ in (('weak', wk), ('strong', st)):
        v = (d_['mean'] * d_['count'] / (d_['count'] + 8)).where(d_['count'] >= 6)
        A[nm + '_n'] = d_['count'].reindex(A.index)
        A[nm] = v.reindex(A.index)
        ref = A[A[nm + '_n'] >= 8].groupby('role')[nm].std()
        A['p_' + nm] = A['T'] + SIGMA_FACET * A[nm] / A.role.map(ref)
    bg = p[p.big].groupby('pid').c.agg(['mean', 'count']); rg = p[~p.big].groupby('pid').c.agg(['mean', 'count'])
    cl = ((bg['mean'] - rg['mean']) * bg['count'] / (bg['count'] + 10)).where((bg['count'] >= 8) & (rg['count'] >= 8))
    A['clutch'] = (cl / cl.std()).reindex(A.index); A['big_n'] = bg['count'].reindex(A.index).fillna(0)
    A['c_sd'] = g.c.std()
    cnt = p.groupby(['pid', 'champion']).size()
    sh = cnt / cnt.groupby(level=0).transform('sum')
    A['pool_eff'] = np.exp(-(sh * np.log(sh)).groupby(level=0).sum()); A['pool_n'] = cnt.groupby(level=0).size()

    # ---- style de jeu (stats brutes, pas de jugement de niveau)
    ci = champ_index(p)
    for name in ('champ_carry', 'champ_tank'):
        p[name] = np.nan
        for ro in ROLES:
            m = p.role == ro
            p.loc[m, name] = p.loc[m, 'champion'].map(ci[(ro, name)])
    # centré par compétition et par poste : le style d'un joueur se lit par rapport à ceux qui jouent dans le même environnement
    sty = p[STYLE] - p.groupby(['role', 'ctx'])[STYLE].transform('mean') + p.groupby('role')[STYLE].transform('mean')
    S = sty.groupby(p.pid).mean()
    S = S.mul(shr.reindex(S.index), axis=0) + S.groupby(A.role.reindex(S.index)).transform('mean').mul(1 - shr.reindex(S.index), axis=0)
    rs = A.role.reindex(S.index)
    ref = S[A.n.reindex(S.index) >= 15]
    Sz = (S - ref.groupby(rs.reindex(ref.index)).mean().reindex(rs.values).values) / ref.groupby(rs.reindex(ref.index)).std().reindex(rs.values).values
    Sz = Sz.clip(-3, 3).fillna(0)
    A['pool_z'] = ((A.pool_eff - A[A.n >= 15].groupby('role').pool_eff.transform('mean').reindex(A.index).fillna(A.pool_eff.mean())))
    A['pool_z'] = (A.pool_eff - A.role.map(q15.assign(pe=A.pool_eff).groupby('role').pe.mean())) / A.role.map(q15.assign(pe=A.pool_eff).groupby('role').pe.std())

    # ---- lignes de stats affichées
    p['k_'] = p.kills; p['d_'] = p.deaths; p['a_'] = p.assists
    st_ = g.agg(win=('result', 'mean'), k=('kills', 'sum'), d=('deaths', 'sum'), a=('assists', 'sum'), kp=('kp', 'mean'), dpm=('dpm', 'mean'),
                dsh=('damageshare', 'mean'), gsh=('earnedgoldshare', 'mean'), gd15=('golddiffat15', 'mean'), cd15=('csdiffat15', 'mean'),
                xd15=('xpdiffat15', 'mean'), cspm=('cspm', 'mean'), vspm=('vspm', 'mean'), dpg=('deaths', 'mean'), fb=('fbp', 'mean'))
    A = A.join(st_)
    A = A.join(last[['name', 'team', 'tid', 'league', 'last_date']])
    A = A.dropna(subset=['league', 'pts'])
    A['tier'] = A.league.map(tier_of)
    return dict(p=p, A=A, R=R, lvl=lg_lvl, cups=cups, Sz=Sz, team_home=team_home, sd_c=sd_c, t=t, slopes=slopes, side=side_adv)


def event_levels(p, R, side_adv):
    """Niveau de chaque équipe sur chaque événement. Même modèle de victoire que sur la saison, relancé sur les seules
    parties de l'événement : toutes les équipes sont estimées ensemble, donc battre une équipe compte selon ce que
    cette équipe a fait dans ce même événement. Le niveau de saison ne sert que de point de départ, faible."""
    out = {}
    g = p.drop_duplicates(['gameid', 'tid'])
    for ev, q in g.groupby('event'):
        b = q[q.side == 'Blue'].set_index('gameid'); r = q[q.side == 'Red'].set_index('gameid').reindex(b.index)
        ok = r.tid.notna().values; b, r = b[ok], r[ok]
        teams = sorted(set(b.tid) | set(r.tid)); ti = {t: i for i, t in enumerate(teams)}
        if not len(b): continue
        X = np.zeros((len(b), len(teams))); rows = np.arange(len(b))
        X[rows, b.tid.map(ti).values] = 1 / PTS_PER_LOGIT; X[rows, r.tid.map(ti).values] = -1 / PTS_PER_LOGIT
        off = (b.tid.map(R).values - r.tid.map(R).values) / PTS_PER_LOGIT + side_adv
        y = b.result.values.astype(float); d = np.zeros(len(teams))
        for _ in range(25):
            mu = 1 / (1 + np.exp(-(off + X @ d))); w = mu * (1 - mu)
            H = X.T @ (X * w[:, None]) + np.eye(len(teams)) / SD_EVENT ** 2
            step = np.linalg.solve(H, X.T @ (y - mu) - d / SD_EVENT ** 2); d += step
            if np.abs(step).max() < 1e-6: break
        for t, i in ti.items(): out[(ev, t)] = R[t] + d[i]
    return out


def event_table(S):
    p, A, R = S['p'], S['A'], S['R']
    lv = event_levels(p, R, S['side'])
    p = p.assign(R_ev=[lv.get(k, r) for k, r in zip(zip(p.event, p.tid), p.R_own)])
    g = p.groupby(['pid', 'event'])
    E = g.agg(n=('c', 'size'), csum=('c', 'sum'), cn=('c', 'count'), win=('result', 'mean'), wins=('result', 'sum'), Ropp=('R_opp', 'mean'),
              Rown=('R_own', 'mean'), T=('R_ev', 'mean'), k=('kills', 'sum'), d=('deaths', 'sum'), a=('assists', 'sum'), start=('date', 'min'),
              end=('date', 'max'), team=('teamname', 'last'), league=('league', 'last'), scope=('scope', 'last')).reset_index()
    E = E[E.n >= MIN_EVENT]
    E = E[E.pid.isin(A.index)]
    cs = A.c_s.reindex(E.pid).values; role = A.role.reindex(E.pid).values
    E['I'] = ((E.csum + K_EVENT_IND * cs) / (E.cn + K_EVENT_IND)) / S['sd_c'].reindex(role).values
    E['pts'] = E['T'] + SIGMA_IND * E.I
    return E


def form_table(S, last_n=15):
    p, A = S['p'], S['A']
    q = p.sort_values('date').groupby('pid').tail(last_n)
    g = q.groupby('pid')
    F = g.agg(n=('c', 'size'), csum=('c', 'sum'), cn=('c', 'count'), wins=('result', 'sum'), Ropp=('R_opp', 'mean'), Rown=('R_own', 'mean'))
    F = F[F.index.isin(A.index)]
    cs = A.c_s.reindex(F.index); role = A.role.reindex(F.index)
    F['I'] = ((F.csum + 8 * cs) / (F.cn + 8)) / S['sd_c'].reindex(role.values).values
    perf = F.Ropp + PTS_PER_LOGIT * np.log((F.wins + 1) / (F.n - F.wins + 1))
    F['pts'] = F.Rown + (F.n / (F.n + 12)) * (perf - F.Rown).clip(-400, 400) + SIGMA_IND * F.I
    return F.pts


def norm(x):
    return ''.join(ch for ch in str(x).lower() if ch.isalnum())


TEAM_STOP = {'team', 'esports', 'esport', 'gaming', 'club', 'the', 'academy', 'challengers', 'youth'}
LEAGUE_ALIAS = {'Circuito Desafiante': 'CD'}


def team_tokens(x):
    return {w for w in ''.join(ch if ch.isalnum() else ' ' for ch in str(x).lower()).split() if len(w) >= 2 and w not in TEAM_STOP}


def match_contracts(A):
    """date de fin de contrat par joueur, depuis la base publique de Riot (pipeline/contracts.json).
    On exige le même pseudo et la même équipe ; à défaut, le même pseudo dans la même ligue s'il y est unique."""
    path = os.path.join(HERE, 'contracts.json')
    if not os.path.exists(path): return {}, None
    C = json.load(open(path, encoding='utf-8'))
    by = {}
    for c in C['contracts']: by.setdefault(norm(c['name']), []).append(c)
    out = {}
    for pid, r in A.iterrows():
        cand = by.get(norm(r['name']), [])
        if not cand: continue
        tt = team_tokens(r.team)
        same_team = [c for c in cand if tt & team_tokens(c['team']) or norm(c['team']) in norm(r.team) or norm(r.team) in norm(c['team'])]
        same_lg = [c for c in cand if LEAGUE_ALIAS.get(c['league'], c['league']) == r.league or (c['league'] == 'LCK' and r.league in ('LCKC', 'LAS'))]
        pick = same_team[0] if same_team else (same_lg[0] if len(same_lg) == 1 and len(cand) == 1 else None)
        if pick: out[pid] = pick['end']
    return out, C


LP_ROLE = {'Top': 'Top', 'Jungle': 'Jungle', 'Mid': 'Mid', 'Bot': 'ADC', 'Support': 'Support'}


def match_leaguepedia(A, today):
    """âge, pays, résidence et fin de contrat depuis Leaguepedia (pipeline/lp_players.json).
    Même règle que pour les contrats : même pseudo et même équipe ; à défaut, un seul joueur de ce pseudo à ce poste."""
    path = os.path.join(HERE, 'lp_players.json')
    if not os.path.exists(path): return {}, None
    L = json.load(open(path, encoding='utf-8'))
    by = {}
    for c in L['players']:
        if LP_ROLE.get(c['role']): by.setdefault(norm(c['name']), []).append(c)
    out = {}
    for pid, r in A.iterrows():
        cand = by.get(norm(r['name']), [])
        if not cand: continue
        tt = team_tokens(r.team)
        same_team = [c for c in cand if c['team'] and (tt & team_tokens(c['team']) or norm(c['team']) in norm(r.team) or norm(r.team) in norm(c['team']))]
        same_role = [c for c in cand if LP_ROLE[c['role']] == r.role]
        pick = same_team[0] if same_team else (same_role[0] if len(same_role) == 1 and len(cand) == 1 else None)
        if not pick: continue
        age = None
        if pick['birth']:
            b = pd.Timestamp(pick['birth']); age = int(today.year - b.year - ((today.month, today.day) < (b.month, b.day)))
            if not 14 <= age <= 45: age = None
        out[pid] = {'age': age, 'cty': pick['country'], 'res': pick['residency'], 'contract': pick['contract']}
    return out, L


def r1(x, k=1):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else round(float(x), k)


def main():
    out = {'seasons': {}, 'facets': list(FACETS), 'style': STYLE, 'weights': WEIGHTS, 'tiers': TIER_NAMES,
           'region': META['region'], 'desc': META['desc'], 'pretty': PRETTY, 'source_note': META['source']}
    runs = {y: season(y, META['prior'][str(y)]) for y in SEASONS}
    # échelle 1-100 commune : calée sur la saison la plus récente
    ref = runs[SEASONS[-1]]['A']; ref = ref[ref.n >= 20]
    top = ref.pts.quantile(0.999); med = ref[ref.tier == 0].pts.median()
    b = (97.5 - 80) / (top - med); a = 80 - b * med
    out['scale'] = {'a': a, 'b': b}
    for y, S in runs.items():
        A, p = S['A'], S['p']
        E = event_table(S); form = form_table(S)
        A = A[A.n >= MIN_GAMES].copy()
        A['note'] = [to_note(v, a, b) for v in A.pts]
        ev_by = {k: v for k, v in E.groupby('pid')}
        champs = p.groupby(['pid', 'champion']).agg(n=('result', 'size'), w=('result', 'mean')).reset_index()
        ch_by = {k: v.sort_values('n', ascending=False).head(6) for k, v in champs.groupby('pid')}
        fac = list(FACETS)
        # centiles par poste et par niveau de ligue
        for f in fac + ['weak', 'strong']:
            A['pc_' + f] = A.groupby(['role', 'tier'])['p_' + f].rank(pct=True)
        A['pc_note'] = A.groupby(['role', 'tier']).pts.rank(pct=True)
        A['pc_sd'] = 1 - A[A.n >= 15].groupby(['role', 'tier']).c_sd.rank(pct=True).reindex(A.index)
        A['pc_pool'] = A[A.n >= 15].groupby(['role', 'tier']).pool_eff.rank(pct=True).reindex(A.index)
        contracts, cmeta = match_contracts(A) if y == SEASONS[-1] else ({}, None)
        if cmeta:
            out['contracts'] = {'source': cmeta['source'], 'fetched': cmeta['fetched'], 'season': str(y), 'matched': len(contracts),
                                'free_until': str((p.date.max() + pd.Timedelta(days=75)).date())}
            print('contrats reliés :', len(contracts), 'sur', len(cmeta['contracts']))
        meta, lmeta = match_leaguepedia(A, pd.Timestamp.today()) if y == SEASONS[-1] else ({}, None)
        if lmeta:
            out['meta'] = {'season': str(y), 'fetched': lmeta['fetched'], 'matched': len(meta)}
            extra = {k: v['contract'] for k, v in meta.items() if v['contract'] and k not in contracts}
            contracts.update(extra)
            if 'contracts' in out: out['contracts']['matched'] = len(contracts); out['contracts']['from_leaguepedia'] = len(extra)
            print('fiches Leaguepedia reliées :', len(meta), '| contrats ajoutés :', len(extra))
        players = []
        for pid, r in A.sort_values('pts', ascending=False).iterrows():
            evs = []
            if pid in ev_by:
                for _, e in ev_by[pid].sort_values('start').iterrows():
                    evs.append({'e': e.event, 'n': int(e.n), 'w': r1(e.win, 3), 'kda': r1((e.k + e.a) / max(e.d, 1), 2),
                                'note': r1(to_note(e.pts, a, b)), 'team': e.team, 'd': str(e.end.date()),
                                'cup': bool(e.league in S['cups']), 'sc': e.scope})
            sz = S['Sz'].loc[pid] if pid in S['Sz'].index else None
            players.append({
                'id': pid.replace('oe:player:', ''), 'name': r['name'], 'team': r.team, 'tid': str(r.tid).replace('oe:team:', ''), 'league': r.league,
                'region': META['region'].get(r.league, 'Autre'), 'tier': int(r.tier), 'role': r.role, 'n': int(r.n),
                'note': r1(r.note), 'pts': r1(r.pts, 0), 'team_lvl': r1(to_note(r['T'], a, b)), 'ind': r1(r.I, 2),
                'form': r1(to_note(form.get(pid, r.pts), a, b)), 'last': str(r.last_date.date()),
                'f': [r1(to_note(r['p_' + f], a, b)) if not pd.isna(r['p_' + f]) else None for f in fac],
                'fp': [r1(r['pc_' + f], 3) for f in fac], 'pc': r1(r.pc_note, 3),
                'weak': r1(to_note(r.p_weak, a, b)) if not pd.isna(r.p_weak) else None, 'weak_pc': r1(r.pc_weak, 3),
                'strong': r1(to_note(r.p_strong, a, b)) if not pd.isna(r.p_strong) else None, 'strong_pc': r1(r.pc_strong, 3),
                'clutch': r1(r.clutch, 2), 'big_n': int(r.big_n), 'reg': r1(r.pc_sd, 3), 'pool': r1(r.pc_pool, 3),
                'pool_n': int(r.pool_n), 'pool_eff': r1(r.pool_eff),
                's': [r1(v, 2) for v in sz.values] if sz is not None else None,
                'st': {'win': r1(r.win, 3), 'kda': r1((r.k + r.a) / max(r.d, 1), 2), 'kp': r1(r.kp, 3), 'dpm': r1(r.dpm, 0), 'dsh': r1(r.dsh, 3),
                       'gsh': r1(r.gsh, 3), 'gd15': r1(r.gd15, 0), 'cd15': r1(r.cd15), 'xd15': r1(r.xd15, 0), 'cspm': r1(r.cspm, 2),
                       'vspm': r1(r.vspm, 2), 'dpg': r1(r.dpg, 2), 'fb': r1(r.fb, 3)},
                'c': contracts.get(pid), 'age': meta.get(pid, {}).get('age'), 'cty': meta.get(pid, {}).get('cty'), 'res': meta.get(pid, {}).get('res'), 'ev': evs,
                'ch': [[c.champion, int(c.n), r1(c.w, 2)] for _, c in ch_by.get(pid, pd.DataFrame()).iterrows()],
            })
        # équipes : effectif des 12 dernières parties
        t = S['t']; teams = []
        tl = t.sort_values('date').groupby('tid').agg(name=('teamname', 'last'), last=('date', 'max'), n=('gameid', 'nunique'), win=('result', 'mean'))
        for tid, tr in tl.iterrows():
            lg = S['team_home'].get(tid)
            if not isinstance(lg, str) or tr.n < 8: continue
            gids = t[t.tid == tid].sort_values('date').gameid.tail(12)
            q = p[(p.tid == tid) & p.gameid.isin(gids)]
            ros = q.groupby(['role', 'pid']).size().reset_index(name='k').sort_values('k').groupby('role').pid.last()
            teams.append({'tid': str(tid).replace('oe:team:', ''), 'name': tr['name'], 'league': lg, 'tier': tier_of(lg),
                          'region': META['region'].get(lg, 'Autre'), 'lvl': r1(to_note(S['R'][tid], a, b)), 'n': int(tr.n), 'win': r1(tr.win, 3),
                          'last': str(tr['last'].date()),
                          'roster': {ro: ros[ro].replace('oe:player:', '') for ro in ROLES if ro in ros.index and ros[ro] in A.index}})
        out['seasons'][str(y)] = {
            'players': players, 'teams': teams,
            'leagues': {l: r1(to_note(v, a, b)) for l, v in S['lvl'].items()},
            'games': int(p.gameid.nunique()), 'from': str(p.date.min().date()), 'to': str(p.date.max().date()),
        }
        print(y, 'joueurs', len(players), 'équipes', len(teams), 'parties', p.gameid.nunique(), 'avantage côté bleu', round(S['side'], 3))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('écrit', OUT, os.path.getsize(OUT) // 1000, 'Ko')
    return runs, out


if __name__ == '__main__':
    main()
