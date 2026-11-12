"""Garde-fou avant publication : refuse un data.json manifestement cassé (fichier source tronqué, colonnes changées...)."""
import json, os, sys
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'data.json'), encoding='utf-8'))
err = []
last = sorted(d['seasons'])[-1]
for y, s in d['seasons'].items():
    P = s['players']
    notes = [p['note'] for p in P]
    if any(n is None or not (1 <= n <= 99) for n in notes): err.append(f'{y} : note hors de 1-99')
    if y != last and len(P) < 1000: err.append(f'{y} : seulement {len(P)} joueurs')
    majors = [p for p in P if p['tier'] == 0 and p['n'] >= 20]
    if majors:
        med = sorted(p['note'] for p in majors)[len(majors) // 2]
        if y == last and not (78 <= med <= 82): err.append(f'{y} : médiane des ligues majeures à {med}, attendue vers 80')
        if max(p['note'] for p in majors) < 90: err.append(f'{y} : aucun joueur au-dessus de 90')
    elif y != last: err.append(f'{y} : aucun joueur de ligue majeure')
    for ro in ('Top', 'Jungle', 'Mid', 'ADC', 'Support'):
        if len(P) > 300 and sum(p['role'] == ro for p in P) < 30: err.append(f'{y} : trop peu de joueurs au poste {ro}')
    print(y, len(P), 'joueurs,', s['games'], 'parties, jusqu\'au', s['to'])
if err:
    print('\n'.join('ERREUR ' + e for e in err)); sys.exit(1)
print('vérification passée')
