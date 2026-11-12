"""Récupère depuis Leaguepedia :
  1. les fiches joueurs (pseudo, équipe, poste, pays, résidence, date de naissance, fin de contrat) -> pipeline/lp_players.json
  2. la couverture des données détaillées par tournoi pour la saison (parties, stats complètes, chronologie) -> pipeline/lp_coverage.json

Demande LEAGUEPEDIA_USER et LEAGUEPEDIA_PASSWORD dans l'environnement (voir leaguepedia.py).
Les noms civils ne sont ni demandés ni stockés.
"""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leaguepedia import Leaguepedia

HERE = os.path.dirname(os.path.abspath(__file__))
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().year


def players(lp):
    rows = lp.cargo('Players', 'ID,OverviewPage,Team,Role,Country,NationalityPrimary,Residency,Birthdate,Contract,IsRetired',
                    where='IsRetired="0" AND (Team IS NOT NULL OR Contract IS NOT NULL OR Birthdate IS NOT NULL)', order_by='OverviewPage')
    out = []
    for r in rows:
        out.append({'name': r.get('ID'), 'page': r.get('OverviewPage'), 'team': r.get('Team') or None, 'role': r.get('Role') or None,
                    'country': r.get('NationalityPrimary') or r.get('Country') or None, 'residency': r.get('Residency') or None,
                    'birth': (r.get('Birthdate') or None) if str(r.get('Birthdate__precision', '1')) == '1' else None,
                    'contract': r.get('Contract') or None})
    json.dump({'source': 'https://lol.fandom.com', 'fetched': dt.date.today().isoformat(), 'players': out},
              open(os.path.join(HERE, 'lp_players.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('joueurs :', len(out), '| avec date de naissance :', sum(1 for p in out if p['birth']), '| avec contrat :', sum(1 for p in out if p['contract']),
          '| avec résidence :', sum(1 for p in out if p['residency']))


def coverage(lp):
    rows = lp.cargo('ScoreboardGames=SG,PostgameJsonMetadata=PJ', 'SG.GameId,SG.Tournament,SG.DateTime_UTC,PJ.StatsPage,PJ.TimelinePage',
                    join_on='SG.GameId=PJ.GameId', where=f'SG.DateTime_UTC >= "{YEAR}-01-01" AND SG.DateTime_UTC < "{YEAR + 1}-01-01"', order_by='SG.DateTime_UTC')
    T = {}
    for r in rows:
        t = T.setdefault(r.get('Tournament') or '?', {'games': 0, 'stats': 0, 'timeline': 0, 'sample': None})
        t['games'] += 1; t['stats'] += bool(r.get('StatsPage')); t['timeline'] += bool(r.get('TimelinePage'))
        if r.get('TimelinePage'): t['sample'] = r['TimelinePage']
    tot = {k: sum(t[k] for t in T.values()) for k in ('games', 'stats', 'timeline')}
    print(f'saison {YEAR} : {tot["games"]} parties, {tot["stats"]} avec stats complètes, {tot["timeline"]} avec chronologie')
    for name, t in sorted(T.items(), key=lambda x: -x[1]['games'])[:90]:
        print(f'  {name[:52]:52s} {t["games"]:5d} parties  stats {100 * t["stats"] // t["games"]:3d} %  chronologie {100 * t["timeline"] // t["games"]:3d} %')
    # vérifie qu'une chronologie se lit vraiment pour quelques grandes compétitions
    for key in ('LCK', 'LPL', 'LEC', 'LCS', 'World', 'MSI'):
        name = next((n for n, t in sorted(T.items(), key=lambda x: -x[1]['games']) if key in n and t['sample']), None)
        if not name: print(f'  [{key}] aucune chronologie référencée'); continue
        txt = lp.page(T[name]['sample'])
        try:
            d = json.loads(txt); fr = d['frames']
            kills = sum(1 for f in fr for e in f.get('events', []) if e.get('type') == 'CHAMPION_KILL')
            pos = sum(1 for f in fr for v in f.get('participantFrames', {}).values() if v.get('position'))
            print(f'  [{key}] {name} : chronologie lue, {len(fr)} minutes, {kills} kills, {pos} positions de joueurs')
        except Exception as e:
            print(f'  [{key}] {name} : chronologie illisible ({type(e).__name__})')
    for t in T.values(): t.pop('sample')
    json.dump({'fetched': dt.date.today().isoformat(), 'year': YEAR, 'total': tot, 'tournaments': T},
              open(os.path.join(HERE, 'lp_coverage.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    lp = Leaguepedia(delay=1.1)
    print('connecté en tant que :', lp.login())
    players(lp)
    coverage(lp)
