"""Garde-fou avant publication. Refuse un data.json manifestement cassé (fichier source tronqué, colonnes changées...)
et le compare à la page actuellement publiée : une mise à jour ne doit ni perdre des parties, ni déplacer les notes en bloc."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, '..', 'app', 'data.json'), encoding='utf-8'))
err = []
last = sorted(d['seasons'])[-1]
for y, s in d['seasons'].items():
    P = s['players']
    if any(p['note'] is None or not (1 <= p['note'] <= 99) for p in P): err.append(f'{y} : note hors de 1-99')
    if y != last and len(P) < 1000: err.append(f'{y} : seulement {len(P)} joueurs')
    majors = [p for p in P if p['tier'] == 0 and p['n'] >= 20]
    if majors and max(p['note'] for p in majors) < 90: err.append(f'{y} : aucun joueur au-dessus de 90')
    if not majors and y != last: err.append(f'{y} : aucun joueur de ligue majeure')
    for ro in ('Top', 'Jungle', 'Mid', 'ADC', 'Support'):
        if len(P) > 300 and sum(p['role'] == ro for p in P) < 30: err.append(f'{y} : trop peu de joueurs au poste {ro}')
    print(y, len(P), 'joueurs,', s['games'], 'parties, jusqu\'au', s['to'])

# comparaison avec la page publiée (docs/index.html)
try:
    page = open(os.path.join(HERE, '..', 'docs', 'index.html'), encoding='utf-8').read()
    i = page.index('window.DATA=') + len('window.DATA='); j = page.index(';</script>', i)
    old = json.loads(page[i:j].replace('<\\/', '</'))
except Exception as e:
    old = None; print('pas de comparaison avec la page publiée :', type(e).__name__)
if old:
    for y, s in d['seasons'].items():
        o = old['seasons'].get(y)
        if not o: continue
        if s['games'] < 0.98 * o['games']: err.append(f"{y} : {s['games']} parties contre {o['games']} dans la page publiée")
        prev = {p['id']: p['note'] for p in o['players'] if p['tier'] == 0 and p['n'] >= 30}
        diff = sorted(abs(p['note'] - prev[p['id']]) for p in s['players'] if p['id'] in prev)
        if diff:
            med, big = diff[len(diff) // 2], sum(x > 5 for x in diff) / len(diff)
            print(f'{y} : par rapport à la page publiée, écart médian {med:.1f}, {big:.0%} des joueurs à plus de 5 points')
            if med > 2 or big > 0.10: err.append(f'{y} : les notes ont bougé en bloc (écart médian {med:.1f}, {big:.0%} à plus de 5 points)')
if err:
    print('\n'.join('ERREUR ' + e for e in err)); sys.exit(1)
print('vérification passée')
