"""Banc d'essai des variantes du niveau d'équipe (novembre 2026).

    python tools/bench_team_levels.py      # depuis la racine du dépôt, avec data/raw/ ; environ 5 minutes, demande scipy

Chaque variante est jugée sur trois tests, en log-loss (plus bas = meilleur) :
  - tout : validation croisée en 5 parts sur toutes les parties ;
  - playoffs LCK+LPL : playoffs cachés, là où les groupes de niveau se rencontrent ;
  - majeures cachées : tous les matchs entre ligues majeures (LCK, LPL, LEC, LCS) cachés.
Affiche aussi le niveau de saison de quelques équipes repères. Ajouter une variante dans le dictionnaire V.
"""
import sys, numpy as np, pandas as pd
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pipeline')); import build as B

def period(d):  # janvier-mars, avril-juin, juillet-septembre, octobre-décembre
    return ((d.dt.month - 1) // 3).values

def fit(t, cups, prior, o):
    """Renvoie une fonction de prédiction p(bleu gagne) pour des lignes (tid bleu, tid rouge, date, phase)."""
    dom = t[~t.league.isin(cups)]
    home = dom.groupby(['tid', 'league']).gameid.nunique().reset_index().sort_values('gameid').groupby('tid').league.last()
    teams = sorted(t.tid.unique()); home = home.reindex(teams)
    home = pd.Series([home.get(x.replace(B.REMANIEE, '')) if (x.endswith(B.REMANIEE) and not isinstance(home[x], str)) else home[x] for x in teams], index=teams)
    fb = np.mean([v for k, v in prior.items() if B.tier_of(k) == 1])
    lgs = sorted(set(home.dropna())); pri = np.array([prior.get(home[x], fb) if isinstance(home[x], str) else fb for x in teams])
    ti = {x: i for i, x in enumerate(teams)}; li = {x: i for i, x in enumerate(lgs)}
    b = t[t.side == 'Blue'].set_index('gameid'); r = t[t.side == 'Red'].set_index('gameid').reindex(b.index)
    nT, nL = len(teams), len(lgs)
    # colonnes : équipes, ligues, côté, [équipe x période], [équipe x phase de groupe]
    per = period(b.date) if o.get('sd_period') else None
    ph = b.phase.values if o.get('sd_phase') else None
    cols = nT + nL + 1; extra = {}
    def col(key):
        if key not in extra: extra[key] = cols + len(extra)
        return extra[key]
    rows_i, rows_j, vals = [], [], []
    n = len(b); bi = b.tid.map(ti).values; ri = r.tid.map(ti).values
    hb = b.tid.map(home).map(li); hr = r.tid.map(home).map(li)
    for k in range(n):
        for idx, sgn, hl, tid in ((bi[k], 1., hb.iloc[k], b.tid.iloc[k]), (ri[k], -1., hr.iloc[k], r.tid.iloc[k])):
            rows_i.append(k); rows_j.append(idx); vals.append(sgn)
            if hl == hl: rows_i.append(k); rows_j.append(nT + int(hl)); vals.append(sgn)
            if per is not None: rows_i.append(k); rows_j.append(col(('P', tid, per[k]))); vals.append(sgn)
            if ph is not None and isinstance(ph[k], str): rows_i.append(k); rows_j.append(col(('G', tid, ph[k]))); vals.append(sgn)
    m = cols + len(extra)
    import scipy.sparse as sp
    X = sp.coo_matrix((np.array(vals) / B.PTS_PER_LOGIT, (rows_i, rows_j)), shape=(n, m)).tocsr()
    X = sp.hstack([X[:, :nT + nL], sp.csr_matrix(np.ones((n, 1))), X[:, nT + nL + 1:]]).tocsr()
    off = (pri[bi] - pri[ri]) / B.PTS_PER_LOGIT; y = b.result.values.astype(float)
    sdd = o.get('sd_league', {}); sd_t = np.array([sdd.get(home[x], 160.) if isinstance(home[x], str) else 160. for x in teams])
    pen = np.r_[1 / sd_t ** 2, np.full(nL, 1 / 90. ** 2), 0.0, np.zeros(len(extra))]
    for key, j in extra.items(): pen[j] = 1 / (o['sd_period'] if key[0] == 'P' else o['sd_phase']) ** 2
    gw = np.ones(n)
    if o.get('cross_w'): gw = np.where(hb.notna().values & hr.notna().values & (hb.values != hr.values), o['cross_w'], 1.)
    # or de fin de partie, observation continue en plus du résultat
    gd = None
    if o.get('gold'):
        gd = ((b.totalgold.values - r.totalgold.values) / 1000.).clip(-25, 25); okg = ~np.isnan(gd)
    beta = np.zeros(m)
    for it in range(40):
        eta = off + X @ beta; mu = 1 / (1 + np.exp(-eta)); w = gw * mu * (1 - mu)
        H = (X.T @ X.multiply(w[:, None])).toarray() + np.diag(pen); g = X.T @ (gw * (y - mu)) - pen * beta
        if gd is not None:
            if it == 0: cg, sg = 1.0, 1.0
            else:
                e2 = eta[okg]; cg = np.dot(e2, gd[okg]) / np.dot(e2, e2); sg = np.std(gd[okg] - cg * e2)
            lam = o['gold'] * cg ** 2 / sg ** 2
            Xg = X[okg]; resid = gd[okg] / cg - (off[okg] + Xg @ beta)
            H += lam * (Xg.T @ Xg).toarray(); g += lam * (Xg.T @ resid)
        step = np.linalg.solve(H, g); beta += step
        if np.abs(step).max() < 1e-6: break
    side = beta[nT + nL]
    lvl = pri + beta[:nT] * 1.0
    for x, i in ti.items():
        if isinstance(home[x], str): lvl[i] += beta[nT + li[home[x]]]
    def pred(tb, tr, dates, phases):
        out = []
        for a, c, d, phz in zip(tb, tr, dates, phases):
            if a not in ti or c not in ti: out.append(np.nan); continue
            s = lvl[ti[a]] - lvl[ti[c]]
            if per is not None:
                pr = (d.month - 1) // 3
                s += beta[extra[('P', a, pr)]] if ('P', a, pr) in extra else 0; s -= beta[extra[('P', c, pr)]] if ('P', c, pr) in extra else 0
            if ph is not None and isinstance(phz, str):
                s += beta[extra[('G', a, phz)]] if ('G', a, phz) in extra else 0; s -= beta[extra[('G', c, phz)]] if ('G', c, phz) in extra else 0
            out.append(1 / (1 + np.exp(-(s / B.PTS_PER_LOGIT + side))))
        return np.array(out)
    # niveau de saison : moyenne des niveaux de l'équipe sur ses parties
    season = pd.Series(lvl, index=teams)
    if per is not None or ph is not None:
        adj = {}
        for k in range(n):
            for tid, sgn in ((b.tid.iloc[k], 1), (r.tid.iloc[k], 1)):
                v = 0.
                if per is not None and ('P', tid, per[k]) in extra: v += beta[extra[('P', tid, per[k])]]
                if ph is not None and isinstance(ph[k], str) and ('G', tid, ph[k]) in extra: v += beta[extra[('G', tid, ph[k])]]
                adj.setdefault(tid, []).append(v)
        season = season + pd.Series({k: np.mean(v) for k, v in adj.items()}).reindex(teams).fillna(0)
    return pred, season, home

def prepare(year):
    p, t = B.load(year); cups = B.detect_cups(t)
    # phase de groupe : (événement, numéro de groupe) pour les parties de saison régulière jouées en groupes isolés
    t = t.copy(); t['phase'] = None
    ev = t.league + ' ' + t.split.fillna('').astype(str)
    reg = t[~t.league.isin(cups) & (t.playoffs != 1)]
    for e, q in reg.groupby(ev[reg.index]):
        opp = q.groupby('gameid').tid.apply(list)
        adj = {}
        for a in opp:
            if len(a) == 2: adj.setdefault(a[0], set()).add(a[1]); adj.setdefault(a[1], set()).add(a[0])
        comps, seen = [], set()
        for t0 in adj:
            if t0 in seen: continue
            c, st = set(), [t0]
            while st:
                x = st.pop()
                if x not in c: c.add(x); st += list(adj[x] - c)
            seen |= c; comps.append(c)
        if len(comps) < 2: continue
        for k, c in enumerate(comps):
            m = (ev == e) & (t.playoffs != 1) & t.tid.isin(c); t.loc[m, 'phase'] = f'{e}#{k}'
    return t, cups

def evaluate(year, o, data):
    t, cups = data[year]; prior = B.META['prior'][str(year)]
    b0 = t[t.side == 'Blue'].set_index('gameid'); r0 = t[t.side == 'Red'].set_index('gameid').reindex(b0.index)
    ll = lambda pp, yy: float(np.nanmean(-(yy * np.log(pp) + (1 - yy) * np.log(1 - pp))))
    res = {}
    # E1 : validation croisée en 5 parts
    rng = np.random.default_rng(7); fold = dict(zip(b0.index, rng.integers(0, 5, len(b0))))
    P = pd.Series(np.nan, index=b0.index)
    for k in range(5):
        tr = t[t.gameid.map(fold) != k]; pred, _, home = fit(tr, cups, prior, o)
        te = b0[b0.index.map(fold) == k]; rr = r0.loc[te.index]
        P.loc[te.index] = pred(te.tid.values, rr.tid.values, te.date, te.phase.values)
    _, season, home = fit(t, cups, prior, o)
    hb = b0.tid.map(lambda x: home.get(x)); hr = r0.tid.map(lambda x: home.get(x)); y = b0.result.values
    cross = (hb.notna() & hr.notna() & (hb != hr)).values
    res['tout'] = ll(P.values, y); res['entre ligues'] = ll(P.values[cross], y[cross])
    # E2 : playoffs de LCK et LPL cachés (là où les groupes se rencontrent)
    m2 = b0.league.isin(['LCK', 'LPL']) & (b0.playoffs == 1)
    pred, _, _ = fit(t[~t.gameid.isin(b0.index[m2])], cups, prior, o)
    p2 = pred(b0[m2].tid.values, r0[m2].tid.values, b0[m2].date, b0[m2].phase.values); res['playoffs LCK+LPL'] = ll(p2, b0[m2].result.values)
    # E3 : tous les matchs entre ligues majeures cachés
    maj = {'LCK', 'LPL', 'LEC', 'LCS'}; m3 = (hb.isin(maj) & hr.isin(maj) & (hb != hr)).values
    pred, _, _ = fit(t[~t.gameid.isin(b0.index[m3])], cups, prior, o)
    p3 = pred(b0[m3].tid.values, r0[m3].tid.values, b0[m3].date, b0[m3].phase.values); res['majeures cachées'] = ll(p3, y[m3])
    return res, season

if __name__ == '__main__':
    data = {y: prepare(y) for y in (2026, 2025)}
    base = {'sd_league': {'LCK': 250., 'LPL': 250.}}
    V = {
        'actuel': base,
        'phase de groupe (sd 80)': {**base, 'sd_phase': 80.},
        'phase de groupe (sd 150)': {**base, 'sd_phase': 150.},
        'niveau par trimestre (sd 80)': {**base, 'sd_period': 80.},
        'niveau par trimestre (sd 150)': {**base, 'sd_period': 150.},
        'trimestre 80 + groupe 80': {**base, 'sd_period': 80., 'sd_phase': 80.},
        'or de fin de partie (0,5)': {**base, 'gold': 0.5},
        'or de fin de partie (1)': {**base, 'gold': 1.0},
        'or (0,5) + trimestre 80': {**base, 'gold': 0.5, 'sd_period': 80.},
        'LPL plus large (350)': {'sd_league': {'LCK': 250., 'LPL': 350.}},
    }
    names = ['Ninjas in Pyjamas', 'JD Gaming', 'Weibo Gaming', 'Top Esports', 'Bilibili Gaming', 'G2 Esports', 'Karmine Corp', 'BNK FEARX', 'Nongshim RedForce', 'Gen.G']
    for year in (2026, 2025):
        t = data[year][0]; nm = t.sort_values('date').groupby('tid').teamname.last()
        rows = []
        for lab, o in V.items():
            res, season = evaluate(year, o, data)
            note = lambda tid: round(B.to_note(season[tid], B.SCALE_A, B.SCALE_B), 1) if tid in season.index else None
            lv = {n: note(nm[nm == n].index[0]) for n in names if (nm == n).any()}
            rows.append({'variante': lab, **{k: round(v, 4) for k, v in res.items()}, **lv})
        df = pd.DataFrame(rows).set_index('variante')
        pd.set_option('display.width', 300); pd.set_option('display.max_columns', 30)
        print(f'\n======== {year}'); print(df.to_string())
