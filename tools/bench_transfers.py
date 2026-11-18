"""Test des transferts : les notes d'une saison prédisent-elles les matchs de la saison suivante des effectifs remaniés ?
C'est le juge de tout changement du partage entre niveau d'équipe et part individuelle (novembre 2026).

    python tools/bench_transfers.py              # paires 2024 -> 2025 et 2025 -> 2026, depuis la racine du dépôt (1 minute)
    python tools/bench_transfers.py 2023         # contrôle final 2023 -> 2024 (échelle réglée sur les deux autres paires) :
                                                 # seulement une fois le réglage figé

Demande data/raw/ (fichiers d'Oracle's Elixir des saisons concernées) et, pour LoL Ratings et les saisons 2023-2024,
le dépôt Oradixx/LoL-ratings cloné à côté de celui-ci (ou son chemin dans la variable LOL_RATINGS).

Protocole (celui de PRODUCT.md, fixé avant les essais) :
  - notes de la saison N telles que la page les montre (joueurs à 10 parties ou plus) ;
  - parties de la saison N+1 où au moins 4 joueurs de chaque côté ont une note Rift Scout en N, et où au moins 2 joueurs
    d'une des deux équipes viennent d'ailleurs (pas notés en N avec cette équipe) ;
  - somme des notes des joueurs alignés ; un joueur sans note dans une méthode y compte pour la moyenne de ses
    coéquipiers notés ;
  - P(bleu gagne) = sigmoïde(a + b x (somme bleue - somme rouge)) ; a et b sont réglés sur l'autre paire de saisons (une
    méthode ne choisit pas son échelle sur les parties qui la jugent ; avec une seule paire, validation croisée en deux
    moitiés de matchs) ;
  - log-loss, et écart à la note Rift Scout avec un intervalle à 95 % (bootstrap par match : mêmes équipes, même jour).
Une méthode = une fonction (saison N calculée, année) -> note par joueur ; en ajouter une dans METHODS ou via run().
"""
import os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import build as B
B.RAW = os.path.join(ROOT, 'data', 'raw')      # build.py lit sinon son chemin dans les arguments de la ligne de commande

LR_DIR = os.environ.get('LOL_RATINGS', os.path.join(ROOT, '..', 'LoL-ratings'))
N_BOOT = 2000
# 2023-2024 : ligues de premier niveau et de troisième niveau de l'époque (mêmes listes que src/leagues.py de LoL Ratings)
MAJOR_2324 = ['CBLOL', 'LCK', 'LCO', 'LCS', 'LEC', 'LJL', 'LLA', 'LPL', 'PCS', 'VCS']
TIER3_2324 = ['IGNIS', 'NLC Aurora Open']
_META0 = {k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v) for k, v in B.META.items()}


def setup_year(year):
    """Réglages de ligues propres à la saison (les fichiers 2025-2026 n'ont plus les mêmes ligues majeures)."""
    for k, v in _META0.items(): B.META[k] = list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v
    if year in (2023, 2024):
        B.META['major'] = MAJOR_2324
        B.META['tier3'] = sorted(set(_META0['tier3']) | set(TIER3_2324))
        try:      # régions des ligues de 2023-2024, reprises de LoL Ratings
            ns = {}; exec(open(os.path.join(LR_DIR, 'src', 'leagues.py'), encoding='utf-8').read(), ns)
            B.META['region'] = {**ns['REGION'], **_META0['region']}
        except OSError:
            pass


def prior_for(year):
    """Niveaux de ligue de départ : ceux de leagues.json, sinon la moyenne des points LoL Ratings par ligue (même règle)."""
    if str(year) in _META0['prior']: return _META0['prior'][str(year)]
    r = pd.read_csv(os.path.join(LR_DIR, 'results', f'ratings_{year}.csv'))
    return r.groupby('league').points.mean().round(0).to_dict()


def lr_points(year):
    f = os.path.join(ROOT, 'pipeline', f'lr_ratings_{year}.csv')
    if not os.path.exists(f): f = os.path.join(LR_DIR, 'results', f'ratings_{year}.csv')
    return pd.read_csv(f).set_index('pid').points


_SEASONS, _GAMES = {}, {}


def season(year):
    if year not in _SEASONS:
        setup_year(year); _SEASONS[year] = B.season(year, prior_for(year)); setup_year(None)
    return _SEASONS[year]


def games(year):
    """Une ligne par partie : joueurs bleus, joueurs rouges, victoire du bleu, match (mêmes équipes, même jour)."""
    if year not in _GAMES:
        setup_year(year); p, t = B.load(year); setup_year(None)
        q = p[['gameid', 'side', 'pid', 'tid', 'date', 'result']].drop_duplicates(['gameid', 'pid'])
        g = q.groupby(['gameid', 'side']).agg(pids=('pid', tuple), tid=('tid', 'first'), date=('date', 'first'), res=('result', 'first'))
        g = g.unstack('side').dropna()
        out = pd.DataFrame({'blue': g[('pids', 'Blue')], 'red': g[('pids', 'Red')], 'y': g[('res', 'Blue')].astype(float),
                            'date': g[('date', 'Blue')], 'tb': g[('tid', 'Blue')], 'tr': g[('tid', 'Red')]})
        out = out[(out.blue.map(len) == 5) & (out.red.map(len) == 5)]
        out['match'] = [f'{d.date()}|{min(a, b)}|{max(a, b)}' for d, a, b in zip(out.date, out.tb, out.tr)]
        _GAMES[year] = out
    return _GAMES[year]


# ----------------------------------------------------------------------------- méthodes
def rated(S):
    A = S['A']; return A[A.n >= B.MIN_GAMES]


def m_note(S, year):
    A = rated(S); return A.pts.map(lambda v: B.to_note(v, B.SCALE_A, B.SCALE_B))


def m_team(S, year):
    A = rated(S); return A['T'].map(lambda v: B.to_note(v, B.SCALE_A, B.SCALE_B))


def m_ind(S, year):
    return rated(S).I


def m_lr(S, year):
    return lr_points(year)


def m_mix(S, year):
    """Même calcul que la note mixte de la page (main() de build.py)."""
    A = rated(S); note = m_note(S, year); lr = lr_points(year).reindex(A.index)
    com = lr.notna() & (A.n >= 15)
    lr_note = note[com].mean() + (lr - lr[com].mean()) * note[com].std() / lr[com].std()
    return ((note + lr_note) / 2).clip(1, 99).fillna(note)


METHODS = {'Rift Scout': m_note, "Niveau d'équipe seul": m_team, 'Part individuelle seule': m_ind,
           'LoL Ratings': m_lr, 'Mixte': m_mix}


def m_unified(cfg=None, start='Z'):
    """Note unifiée (pipeline/unified.py) avec un dosage donné. start : point de départ des joueurs, 'Z' (statistiques
    avant retrait de l'écart de niveau entre les équipes, comme la page), 'I' (part individuelle de la note) ou 'pts'
    (la note Rift Scout complète, niveau d'équipe compris)."""
    import unified as U

    def f(S, year):
        setup_year(year)
        try:
            cf = {'with_se': False, **(cfg or {})}
            out = U.fit(S, prior_for(year), B.tier_of, cf, base=S['A'].pts) if start == 'pts' else U.fit(S, prior_for(year), B.tier_of, cf, S['A'][start])
        finally: setup_year(None)
        return out['theta'].reindex(rated(S).index)
    return f


def m_history(method, alpha):
    """Plusieurs saisons d'historique : la note de la saison N mêlée à celle de N-1, au prorata des parties, celles de N-1
    comptant alpha fois moins. Un joueur sans note en N-1 garde sa note de N."""
    def f(S, year):
        r = method(S, year); A = rated(S)
        S0 = season(year - 1); r0 = method(S0, year - 1).reindex(r.index); n0 = rated(S0).n.reindex(r.index)
        n = A.n.reindex(r.index); w0 = (alpha * n0).where(r0.notna(), 0.0).fillna(0.0)
        return (n * r + w0 * r0.fillna(0.0)) / (n + w0)
    return f


# ----------------------------------------------------------------------------- test
def test_set(year, R=None):
    """Parties de year+1 jugées : au moins 4 joueurs notés de chaque côté, au moins 2 joueurs d'une équipe venus d'ailleurs."""
    S = season(year); G = games(year + 1).copy()
    A = rated(S); ref = set(A.index)
    team_n = A.tid.astype(str).str.replace(B.REMANIEE, '', regex=False)

    def n_rated(pids): return sum(i in ref for i in pids)

    def n_new(pids, tid): return sum(team_n.get(i) != str(tid) for i in pids)
    nb, nr = G.blue.map(n_rated), G.red.map(n_rated)
    eb = np.array([n_new(x, t) for x, t in zip(G.blue, G.tb)]); er = np.array([n_new(x, t) for x, t in zip(G.red, G.tr)])
    return G[((nb >= 4) & (nr >= 4)).values & ((eb >= 2) | (er >= 2))]


def side_sum(pids, r):
    v = r.reindex(list(pids)).dropna()
    return 5 * v.mean() if len(v) else np.nan


def diff_of(G, r):
    """Somme bleue - somme rouge ; 0 si un côté n'a aucun joueur noté dans cette méthode (rare : LoL Ratings seul)."""
    return np.nan_to_num(np.array([side_sum(b, r) - side_sum(rr, r) for b, rr in zip(G.blue, G.red)]))


def fit_ab(x, y):
    a, b = 0.0, 0.0
    for _ in range(50):
        mu = 1 / (1 + np.exp(-(a + b * x))); w = mu * (1 - mu)
        g = np.array([np.sum(y - mu), np.dot(x, y - mu)])
        Hm = np.array([[w.sum(), np.dot(w, x)], [np.dot(w, x), np.dot(w * x, x)]]) + 1e-9 * np.eye(2)
        st = np.linalg.solve(Hm, g); a += st[0]; b += st[1]
        if np.abs(st).max() < 1e-10: break
    return a, b


def ll(y, pr):
    pr = np.clip(pr, 1e-6, 1 - 1e-6); return -(y * np.log(pr) + (1 - y) * np.log(1 - pr))


def run(years=(2024, 2025), methods=None, ref='Rift Scout', verbose=True):
    """Juge chaque méthode sur chaque paire year -> year+1. Renvoie un tableau (paire, méthode, log-loss, écart, IC)."""
    methods = methods or METHODS
    data = {}
    for y in years:
        S = season(y)
        R = {k: f(S, y) for k, f in methods.items()}
        G = test_set(y, R)
        data[y] = (G, {k: diff_of(G, r) for k, r in R.items()})
        if verbose: print(f'{y} -> {y + 1} : {len(G)} parties jugées sur {len(games(y + 1))} ({G.match.nunique()} matchs)')
    rows = []
    rng = np.random.default_rng(0)
    for y in years:
        G, X = data[y]; yv = G.y.values
        others = [o for o in years if o != y]
        # une seule paire : les mêmes deux moitiés de matchs pour toutes les méthodes
        half = pd.Series(rng.integers(0, 2, G.match.nunique()), index=G.match.unique()).reindex(G.match).values
        L = {}
        for k in methods:
            if others:     # échelle réglée sur l'autre paire (ou les autres)
                xo = np.concatenate([data[o][1][k] for o in others]); yo = np.concatenate([data[o][0].y.values for o in others])
                a, b = fit_ab(xo, yo); L[k] = ll(yv, 1 / (1 + np.exp(-(a + b * X[k]))))
            else:          # une seule paire : chaque moitié est jugée avec l'échelle réglée sur l'autre
                L[k] = np.zeros(len(G))
                for h in (0, 1):
                    a, b = fit_ab(X[k][half != h], yv[half != h])
                    L[k][half == h] = ll(yv[half == h], 1 / (1 + np.exp(-(a + b * X[k][half == h]))))
        codes, uniq = pd.factorize(G.match)
        boot = rng.integers(0, len(uniq), (N_BOOT, len(uniq)))
        for k in methods:
            d = L[k] - L[ref]
            per = np.bincount(codes, d, len(uniq)); cnt = np.bincount(codes, None, len(uniq))
            bs = np.array([per[i].sum() / cnt[i].sum() for i in boot])
            rows.append({'paire': f'{y}->{y + 1}', 'méthode': k, 'parties': len(G), 'logloss': L[k].mean(), 'écart': d.mean(),
                         'bas': np.percentile(bs, 2.5), 'haut': np.percentile(bs, 97.5)})
    out = pd.DataFrame(rows)
    if verbose:
        with pd.option_context('display.width', 160, 'display.max_columns', 10):
            print(out.round({'logloss': 4, 'écart': 4, 'bas': 4, 'haut': 4}).to_string(index=False))
    return out


if __name__ == '__main__':
    # 2023 : contrôle final, l'échelle de 2023 -> 2024 étant réglée sur les deux paires de réglage
    ys = (2023, 2024, 2025) if '2023' in sys.argv[1:] else tuple(int(a) for a in sys.argv[1:]) or (2024, 2025)
    run(ys, {**METHODS, 'Note unifiée': m_unified()})
