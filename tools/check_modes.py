"""Les trois calculs de la note (Rift Scout, Mixte, Unifiée) sans mélange, novembre 2026.

    python tools/check_modes.py              # depuis la racine du dépôt, après pipeline/build.py ; quelques secondes
    python tools/check_modes.py LEC LCK      # power ranking attendu recalculé pour ces ligues (LEC par défaut)

1. Données (app/data.json) : chaque note de joueur existe dans les trois calculs (saison, événements, niveau de ligue,
   ligue, équipe, forme, période récente) et chaque droite réglée sur les notes en a une par calcul (D.next.lines,
   D.proj). Une note mixte ou unifiée peut manquer (pas de LoL Ratings pour ce joueur, partie incomplète) : la page affiche
   alors la note Rift Scout, comme pour la note de saison ; le contrôle refuse seulement un champ absent ou une couverture
   anormalement basse.
2. Page (app/app.js) : aucun accès à une droite d'un seul calcul (D.next.lines.maj, D.proj.a...).
3. Recalcul hors page du power ranking attendu dans chacun des trois calculs : à comparer à l'onglet Transferts de la page
   dans chaque calcul (mêmes valeurs à 0,1 près).
pipeline/check.py appelle les parties 1 et 2 avant chaque publication.
"""
import json, os, re, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CALCS = {'rift': 'note', 'mix': 'nm', 'uni': 'nu'}
ROLES = ['Top', 'Jungle', 'Mid', 'ADC', 'Support']
# notes partielles : champ, longueur attendue, place de la note mixte (l'unifiée suit)
SUB = {'tr': (6, 4), 'lg': (6, 4), 'rc': (6, 4), 'tm': (9, 7)}


def mode_errors(d, js=None):
    err = []
    nx = d.get('next') or {}
    for name, obj in (('D.next.lines', nx.get('lines')), ('D.proj', d.get('proj'))):
        if obj is None: continue
        miss = [c for c in CALCS if c not in obj]
        if miss: err.append(f'{name} sans les calculs {miss}')
    for c, L in (nx.get('lines') or {}).items():
        if not all(k in L for k in ('maj', 'low', 'prev')): err.append(f'D.next.lines.{c} incomplet')
    for y, s in d['seasons'].items():
        P = s['players']; cnt = {k: [0, 0, 0] for k in list(SUB) + ['fm', 'ev']}   # entrées, avec mixte, avec unifiée
        for p in P:
            for k, (n, j) in SUB.items():
                v = p.get(k)
                rows = [] if v is None else list(v.values()) if isinstance(v, dict) else v if k == 'tm' else [v]
                for r in rows:
                    if len(r) != n: err.append(f'{y} {p["name"]} : {k} sans ses notes mixte et unifiée'); break
                    cnt[k][0] += 1; cnt[k][1] += r[j] is not None and p.get('nm') is not None; cnt[k][2] += r[j + 1] is not None
            if 'fm' not in p or len(p['fm']) != 2: err.append(f'{y} {p["name"]} : forme sans ses notes mixte et unifiée')
            else: cnt['fm'][0] += 1; cnt['fm'][1] += p['fm'][0] is not None and p.get('nm') is not None; cnt['fm'][2] += p['fm'][1] is not None
            for e in p['ev']:
                cnt['ev'][0] += 1; cnt['ev'][1] += e.get('nm') is not None; cnt['ev'][2] += e.get('nu') is not None
        if len(err) > 20: break
        has_m = sum(p.get('nm') is not None for p in P) / len(P); has_u = sum(p.get('nu') is not None for p in P) / len(P)
        for k, (n_, m_, u_) in cnt.items():
            if not n_: continue
            if u_ / n_ < 0.9 * has_u: err.append(f'{y} : {k}, note unifiée pour {u_ / n_:.0%} des entrées seulement (saison {has_u:.0%})')
            if has_m and k != 'ev' and m_ / n_ < 0.8 * has_m: err.append(f'{y} : {k}, note mixte pour {m_ / n_:.0%} des entrées seulement (saison {has_m:.0%})')
    if js is not None:
        for pat in (r'D\.next\.lines\s*\[\s*p\.tier', r'D\.next\.lines\.(maj|low)\b', r"D\.next\.lines\[\s*'(maj|low)'", r'D\.proj\.(a|b)\b'):
            for m in re.finditer(pat, js): err.append(f'app.js : droite d\'un seul calcul ({m.group(0)}), à prendre dans le calcul choisi')
    return err


def expected(d, lg, calc):
    """Même règle que tvalue() et transferModel() d'app.js, dans le calcul donné."""
    N = d['next']; L = N['lines'][calc]; col = CALCS[calc]; last = sorted(d['seasons'])[-1]
    P1 = {p['id']: p for p in d['seasons'][last]['players']}; P0 = {p['id']: p for p in d['seasons'].get(str(int(last) - 1), {'players': []})['players']}
    note = lambda p: p[col] if p.get(col) is not None else p['note']

    def tv(p):
        if p['tier'] > 0: return L['low']['a'] + L['low']['b'] * note(p)
        q = P0.get(p['id']); v = L['maj']['a'] + L['maj']['b'] * note(p)
        return v + (L['prev'] * (note(q) - note(p)) if L['prev'] and q and q['tier'] == 0 and q['n'] >= 15 else 0)
    T = [t for t in N['teams'] if t['league'] == lg]
    known = [tv(P1[t['cur'][r]]) for t in T for r in ROLES if t['cur'].get(r) in P1]   # équipe nouvelle : cur vide
    dflt = float(np.quantile(known, 0.25)) if known else 0.0
    slot = lambda x: tv(P1[x]) if isinstance(x, str) and x in P1 else dflt
    return sorted(((round(float(np.mean([slot((t['nxt'] or t['cur'])[r]) for r in ROLES])), 1), t['name']) for t in T), reverse=True)


def main():
    d = json.load(open(os.path.join(ROOT, 'app', 'data.json'), encoding='utf-8'))
    js = open(os.path.join(ROOT, 'app', 'app.js'), encoding='utf-8').read()
    err = mode_errors(d, js)
    print('\n'.join('ERREUR ' + e for e in err) if err else 'trois calculs : données et page sans mélange')
    for lg in sys.argv[1:] or ['LEC']:
        for calc in CALCS:
            print(f'{lg} {calc:4s} :', ', '.join(f'{n} {v:.1f}' for v, n in expected(d, lg, calc)))
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
