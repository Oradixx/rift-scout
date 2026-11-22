"""Rift Scout - note unifiée (troisième calcul, à côté de la note Rift Scout et de la note mixte ; novembre 2026).

Un seul modèle au lieu de deux qu'on moyenne. Chaque partie s'explique par la somme des niveaux des dix joueurs et le
côté de la carte ; niveau d'un joueur = niveau de sa ligue + écart individuel.
  - L'écart part des statistiques du joueur (indice `Z` de build.py : les huit facettes, corrigées du champion et de la
    compétition, avant retrait de l'écart de niveau entre les équipes), et les résultats de ses parties le corrigent :
    un joueur avec qui l'équipe gagne plus que ses statistiques ne l'annoncent monte, l'inverse baisse.
  - Observations : la victoire, et l'écart d'or de fin de partie à demi-poids (comme le niveau d'équipe de build.py).
  - Les joueurs sont notés un par un : une équipe qui aligne ses remplaçants est jugée sur ceux qui jouent vraiment.
Les dosages se règlent sur le test des transferts (tools/bench_transfers.py), pas à la main : KAPPA (poids des
statistiques, en multiples de SIGMA_IND points par écart-type) et TAU (liberté laissée aux résultats, en points).
Options essayées une par une (voir PRODUCT.md) : jeu collectif propre à chaque équipe (OMEGA), duels de lane comme
observation directe (LANE_WEIGHT), parties récentes plus lourdes (HALF_LIFE, en jours).
"""
import numpy as np, pandas as pd
from scipy import sparse
import scipy.linalg as sl

PTS_PER_LOGIT = 200.0
# Réglage retenu (novembre 2026, tools/bench_transfers.py, grille fixée d'avance puis prolongée au bord) : départ sur
# l'indice Z, KAPPA 2, TAU 100. Les options (OMEGA, LANE_WEIGHT, HALF_LIFE) n'ont pas gagné sur les deux paires : éteintes.
DEFAULT = dict(tau=100.0, kappa=2.0, omega=0.0, lane_weight=0.0, half_life=None, sigma_ind=85.0, sd_league=90.0,
               gold_weight=0.5, iters=40, with_se=True)
# Bruit de mesure du niveau : NOISE_C / racine(parties), un écart-type, en points. Mesuré par tools/check_margins.py
# (deux moitiés de saison, C = 577 en 2025 et 547 en 2026 ; le C d'une saison laisse 67 % et 73 % des joueurs de l'autre
# dans la marge, pour 68 % attendus). C'est la marge affichée. L'écart-type a posteriori (`se`) ne l'est pas : il ignore
# le bruit des statistiques de départ et repose surtout sur TAU, ce que deux moitiés de saison ne peuvent pas juger.
NOISE_C = 562.0
# Écart propre à un événement (points) : tools/check_event_unified.py, parties de chaque événement partagées en deux moitiés,
# saison refaite sur la moitié A seule, prédiction de la moitié B. Log-loss 2025 puis 2026 : sans écart 0,6221 et 0,6124 ;
# 35 : 0,6215 et 0,6118 ; 100 : 0,6195 et 0,6095 ; 150 : 0,6194 et 0,6085 ; 250 : 0,6229 et 0,6098. On garde 150.
TAU_EVENT = 150.0
LANES = {'Top': ['Top'], 'Jungle': ['Jungle'], 'Mid': ['Mid'], 'Bot': ['ADC', 'Support']}
JUNGLE_IN_LANE = 0.5     # duels de lane : part du jungler dans l'or à 15 minutes d'une lane (choix, pas une mesure)


def event_deltas(S, theta, side, tau, games=None, gold_weight=0.5, iters=25):
    """Note unifiée par événement : écart de chaque joueur à son niveau de saison (theta), estimé sur les seules parties de
    l'événement (victoire et écart d'or), ramené vers 0 avec l'écart-type TAU_EVENT. games : sous-ensemble de parties
    (validation). Renvoie {(événement, joueur) : écart en points}."""
    p, t = S['p'], S['t']
    q = p[['gameid', 'side', 'pid', 'event']].drop_duplicates(['gameid', 'pid'])
    if games is not None: q = q[q.gameid.isin(games)]
    b = t[t.side == 'Blue'].set_index('gameid'); r = t[t.side == 'Red'].set_index('gameid')
    out = {}
    for ev, qe in q.groupby('event'):
        n5 = qe.groupby(['gameid', 'side']).size().unstack(fill_value=0).reindex(columns=['Blue', 'Red'], fill_value=0)
        g_ok = n5.index[((n5.Blue == 5) & (n5.Red == 5)).values]
        g_ok = [g_ for g_ in g_ok if g_ in b.index and g_ in r.index]
        if not len(g_ok) or tau <= 0: continue
        qe = qe[qe.gameid.isin(g_ok)]
        pl = sorted(qe.pid.unique()); pi = pd.Series(np.arange(len(pl)), index=pl); gi = pd.Series(np.arange(len(g_ok)), index=g_ok)
        sg = np.where(qe.side.values == 'Blue', 1.0, -1.0) / (5 * PTS_PER_LOGIT)
        X = sparse.csr_matrix((sg, (gi[qe.gameid].values, pi[qe.pid].values)), shape=(len(g_ok), len(pl)))
        off = X @ theta.reindex(pl).fillna(theta.median()).values + side
        y = b.loc[g_ok].result.values.astype(float)
        gd = ((b.loc[g_ok].totalgold.values - r.loc[g_ok].totalgold.values) / 1000.0).clip(-25, 25); okg = ~np.isnan(gd)
        d = np.zeros(len(pl)); pen = 1 / tau ** 2; cg, s_ = 1.0, 1.0
        for it in range(iters):
            eta = off + X @ d; m = 1 / (1 + np.exp(-eta))
            H = (X.T @ X.multiply((m * (1 - m))[:, None])).toarray() + pen * np.eye(len(pl)); gr = X.T @ (y - m) - pen * d
            if gold_weight and okg.sum() > 5:
                e2 = eta[okg]
                if it: cg = float(np.dot(e2, gd[okg]) / np.dot(e2, e2)); s_ = float(np.std(gd[okg] - cg * e2)) or 1.0
                lam = gold_weight * cg ** 2 / s_ ** 2; Xg = X[okg]
                H += lam * (Xg.T @ Xg).toarray(); gr += lam * (Xg.T @ (gd[okg] / cg - e2))
            st = np.linalg.lstsq(H, gr, rcond=None)[0]; d += st
            if np.abs(st).max() < 1e-6: break
        for x, i in pi.items(): out[(ev, x)] = float(d[i])
    return out


def subset_deltas(S, theta, side, tau, rows, gold_weight=0.5, iters=25):
    """Note unifiée sur un sous-ensemble des parties de chaque joueur (niveau de ligue, ligue, équipe, forme, période récente) :
    écart à son niveau de saison (theta), estimé sur ces seules parties (victoire et écart d'or), les neuf autres joueurs à
    leur niveau de saison, ramené vers 0 avec l'écart-type tau. rows : parties (gameid, pid, key). Renvoie {(key, joueur) :
    écart en points}. Même observation que event_deltas, mais joueur par joueur : un sous-ensemble propre à chaque joueur
    (sa forme, son équipe) ne réunit pas les dix joueurs d'une partie."""
    p, t = S['p'], S['t']
    q = p[['gameid', 'side', 'pid']].drop_duplicates(['gameid', 'pid'])
    n5 = q.groupby(['gameid', 'side']).size().unstack(fill_value=0).reindex(columns=['Blue', 'Red'], fill_value=0)
    b = t[t.side == 'Blue'].set_index('gameid'); r = t[t.side == 'Red'].set_index('gameid')
    ok = n5.index[((n5.Blue == 5) & (n5.Red == 5)).values]; ok = ok[ok.isin(b.index) & ok.isin(r.index)]
    q = q[q.gameid.isin(ok)]
    sg = np.where(q.side.values == 'Blue', 1.0, -1.0) / (5 * PTS_PER_LOGIT)
    off = pd.Series(sg * theta.reindex(q.pid).fillna(theta.median()).values, index=q.gameid.values).groupby(level=0).sum().reindex(ok) + side
    y = b.loc[ok].result.astype(float); gd = ((b.loc[ok].totalgold - r.loc[ok].totalgold) / 1000.0).clip(-25, 25)
    okg = gd.notna().values; e0 = off.values[okg]
    cg = float(np.dot(e0, gd.values[okg]) / np.dot(e0, e0)); s_ = float(np.std(gd.values[okg] - cg * e0)) or 1.0
    lam = gold_weight * cg ** 2 / s_ ** 2 if gold_weight else 0.0
    R = rows[['gameid', 'pid', 'key']].drop_duplicates(['gameid', 'pid', 'key']); R = R[R.gameid.isin(ok)]
    sd = q.set_index(['gameid', 'pid']).side.reindex(pd.MultiIndex.from_arrays([R.gameid, R.pid])).values
    s = np.where(sd == 'Blue', 1.0, -1.0) / (5 * PTS_PER_LOGIT)
    grp, keys = pd.MultiIndex.from_arrays([R.key, R.pid]).factorize()
    o, yy, g2 = off.reindex(R.gameid).values, y.reindex(R.gameid).values, gd.reindex(R.gameid).values
    hg = ~np.isnan(g2); g2 = np.nan_to_num(g2); k = len(keys)
    d = np.zeros(k); pen = 1 / tau ** 2
    for _ in range(iters):
        eta = o + s * d[grp]; m = 1 / (1 + np.exp(-eta))
        gr = np.bincount(grp, s * (yy - m), k) - pen * d; H = np.bincount(grp, s * s * m * (1 - m), k) + pen
        if lam:
            gr += lam * np.bincount(grp, np.where(hg, s * (g2 / cg - eta), 0.0), k); H += lam * np.bincount(grp, np.where(hg, s * s, 0.0), k)
        st = gr / H; d += st
        if np.abs(st).max() < 1e-6: break
    return {kp: float(v) for kp, v in zip(keys, d)}


def fit(S, prior, tier_of, cfg=None, ind=None, base=None):
    """S : une saison calculée par build.season ; prior : niveaux de ligue de départ ; tier_of : niveau d'une ligue ;
    ind : point de départ de chaque joueur en écarts-types de son poste (par défaut la part individuelle `I`) ;
    base : variante, point de départ donné directement en points (niveau complet, ligue comprise).
    Renvoie le niveau de chaque joueur en points (même échelle que la note Rift Scout), sa marge d'incertitude
    (écart-type a posteriori), le jeu collectif de chaque équipe, le niveau des ligues et l'avantage du côté bleu."""
    c = {**DEFAULT, **(cfg or {})}
    p, t, home = S['p'], S['t'], S['team_home']
    b = t[t.side == 'Blue'].set_index('gameid'); r = t[t.side == 'Red'].set_index('gameid').reindex(b.index)
    b, r = b[r.tid.notna().values], r[r.tid.notna().values]
    q = p[['gameid', 'side', 'pid', 'tid', 'role', 'golddiffat15']].drop_duplicates(['gameid', 'pid'])
    q = q[q.gameid.isin(b.index)]
    n_side = q.groupby(['gameid', 'side']).size().unstack(fill_value=0).reindex(b.index, fill_value=0)
    keep = b.index[(n_side.get('Blue', 0) == 5).values & (n_side.get('Red', 0) == 5).values]
    b, r, q = b.loc[keep], r.loc[keep], q[q.gameid.isin(keep)]
    gi = pd.Series(np.arange(len(b)), index=b.index)
    # poids de chaque partie : 1, ou plus faible pour les parties anciennes (demi-vie HALF_LIFE jours)
    gw = np.ones(len(b)) if not c['half_life'] else np.power(0.5, (b.date.max() - b.date).dt.days.values / c['half_life'])

    players = sorted(q.pid.unique()); pi = pd.Series(np.arange(len(players)), index=players)
    teams = sorted(set(b.tid) | set(r.tid)); ti = pd.Series(np.arange(len(teams)), index=teams)
    # ligue de rattachement d'un joueur : celles des équipes avec lesquelles il a joué, au prorata des parties
    q = q.assign(lg=q.tid.map(home))
    fallback = float(np.mean([v for k, v in prior.items() if tier_of(k) == 1]))
    leagues = sorted(set(q.lg.dropna())) + ['?']
    li = pd.Series(np.arange(len(leagues)), index=leagues)
    w = q.assign(lg=q.lg.fillna('?')).groupby(['pid', 'lg']).size()
    w = w / w.groupby(level=0).transform('sum')
    Hm = sparse.csr_matrix((w.values, (pi[w.index.get_level_values(0)].values, li[w.index.get_level_values(1)].values)),
                           shape=(len(players), len(leagues)))
    pri_L = np.array([prior.get(l, fallback) if l != '?' else fallback for l in leagues])

    # point de départ de chaque joueur : ses statistiques
    ind = S['A'].I if ind is None else ind
    mu = c['kappa'] * c['sigma_ind'] * ind.reindex(players).fillna(0.0).values
    if base is not None:
        b0 = base.reindex(players).values; hp = Hm @ pri_L
        mu = np.where(np.isnan(b0), mu, b0 - hp)

    nP, nL, nT = len(players), len(leagues), len(teams)
    sgn = np.where(q.side.values == 'Blue', 1.0, -1.0)
    Xp = sparse.csr_matrix((sgn / (5 * PTS_PER_LOGIT), (gi[q.gameid].values, pi[q.pid].values)), shape=(len(b), nP))
    rows = np.arange(len(b))
    Xt = sparse.csr_matrix((np.r_[np.full(len(b), 1 / PTS_PER_LOGIT), np.full(len(b), -1 / PTS_PER_LOGIT)],
                            (np.r_[rows, rows], np.r_[ti[b.tid].values, ti[r.tid].values])), shape=(len(b), nT))
    XL = Xp @ Hm
    X = sparse.hstack([Xp, XL, Xt, sparse.csr_matrix(np.ones((len(b), 1)))]).tocsr()
    off = Xp @ mu + XL @ pri_L
    pen = np.r_[np.full(nP, 1 / c['tau'] ** 2), np.full(nL, 1 / c['sd_league'] ** 2),
                np.full(nT, 1 / c['omega'] ** 2) if c['omega'] > 0 else np.full(nT, 1e12), 1e-8]
    y = b.result.values.astype(float)
    gd = ((b.totalgold.values - r.totalgold.values) / 1000.0).clip(-25, 25)
    okg = ~np.isnan(gd); Xg = X[okg]; gwg = gw[okg]

    # Duels de lane : or à 15 minutes d'une lane contre la lane d'en face (le duo pour le bas), où le jungler compte pour
    # moitié. Une observation par lane et par partie, du point de vue du côté bleu.
    lanes = []
    if c['lane_weight']:
        piv = q.drop_duplicates(['gameid', 'side', 'role']).set_index(['gameid', 'side', 'role'])
        for lane, roles in LANES.items():
            yv = piv.golddiffat15.reindex([(g_, 'Blue', ro) for g_ in b.index for ro in roles]).values.reshape(len(b), len(roles))
            yl = np.nansum(yv, axis=1) / 1000.0; yl[np.isnan(yv).any(axis=1)] = np.nan
            ents = [(ro, 1.0) for ro in roles] + ([('Jungle', JUNGLE_IN_LANE)] if lane != 'Jungle' else [])
            ri, ci, vv = [], [], []
            for ro, coef in ents:
                for side_, s_ in (('Blue', 1.0), ('Red', -1.0)):
                    pid_ = piv.pid.reindex([(g_, side_, ro) for g_ in b.index]).values
                    ok_ = pd.notna(pid_)
                    ri.append(rows[ok_]); ci.append(pi[pid_[ok_]].values); vv.append(np.full(ok_.sum(), s_ * coef / PTS_PER_LOGIT))
            Xl_p = sparse.csr_matrix((np.concatenate(vv), (np.concatenate(ri), np.concatenate(ci))), shape=(len(b), nP))
            okl = ~np.isnan(yl)
            Xl = sparse.hstack([Xl_p, Xl_p @ Hm, sparse.csr_matrix((len(b), nT + 1))]).tocsr()[okl]
            lanes.append((Xl, (Xl_p @ mu + (Xl_p @ Hm) @ pri_L)[okl], yl[okl].clip(-6, 6), gw[okl]))

    beta = np.zeros(X.shape[1]); cg, sg = 1.0, 1.0; cl = [(1.0, 1.0)] * len(lanes)
    for it in range(c['iters']):
        eta = off + X @ beta; m = 1 / (1 + np.exp(-eta)); wt = gw * m * (1 - m)
        Hs = (X.T @ X.multiply(wt[:, None])).toarray() + np.diag(pen)
        gr = X.T @ (gw * (y - m)) - pen * beta
        if c['gold_weight']:
            if it:      # lien entre écart de niveau et écart d'or, réestimé à chaque tour (comme build.py)
                e2 = eta[okg]; cg = float(np.dot(e2, gd[okg]) / np.dot(e2, e2)); sg = float(np.std(gd[okg] - cg * e2))
            lam = c['gold_weight'] * cg ** 2 / sg ** 2
            Hs += lam * (Xg.T @ Xg.multiply(gwg[:, None])).toarray(); gr += lam * (Xg.T @ (gwg * (gd[okg] / cg - (off[okg] + Xg @ beta))))
        for k_, (Xl, ofl, yl, wl) in enumerate(lanes):
            z = ofl + Xl @ beta
            if it: cl[k_] = (float(np.dot(z, yl) / np.dot(z, z)), float(np.std(yl - np.dot(z, yl) / np.dot(z, z) * z)))
            a_, s_ = cl[k_]; lam = c['lane_weight'] * a_ ** 2 / s_ ** 2
            Hs += lam * (Xl.T @ Xl.multiply(wl[:, None])).toarray(); gr += lam * (Xl.T @ (wl * (yl / a_ - z)))
        cho = sl.cho_factor(Hs)
        step = sl.cho_solve(cho, gr); beta += step
        if np.abs(step).max() < 1e-6: break
    v, dL, ct, side = beta[:nP], beta[nP:nP + nL], beta[nP + nL:nP + nL + nT], beta[-1]
    L = pri_L + dL
    theta = Hm @ L + mu + v
    se = np.full(nP, np.nan)
    if c['with_se']:    # marge d'incertitude : écart-type a posteriori du niveau (écart individuel + niveau de sa ligue)
        cov = sl.cho_solve(cho, np.eye(len(beta))[:, :nP + nL])
        Cvv = np.diag(cov[:nP, :nP]); CLL = cov[nP:nP + nL, nP:nP + nL]; CvL = cov[:nP, nP:nP + nL]
        Hd = Hm.toarray()
        se = np.sqrt(np.clip(Cvv + np.einsum('ij,jk,ik->i', Hd, CLL, Hd) + 2 * np.einsum('ij,ij->i', Hd, CvL), 0, None))
    return dict(theta=pd.Series(theta, index=players), se=pd.Series(se, index=players), team=pd.Series(ct, index=teams),
                league=dict(zip(leagues, L)), side=float(side), games=len(b), cfg=c)
