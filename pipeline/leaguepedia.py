"""Accès à Leaguepedia (lol.fandom.com) avec un mot de passe de bot.

Identifiants lus dans l'environnement : LEAGUEPEDIA_USER (ex. Pseudo@nomdubot) et LEAGUEPEDIA_PASSWORD.
Ils ne sont jamais affichés ni écrits sur disque.

    python pipeline/leaguepedia.py        # test de connexion et inventaire de ce qui est disponible
"""
import json, os, time
import requests

API = 'https://lol.fandom.com/api.php'


class Leaguepedia:
    def __init__(self, delay=1.0):
        self.s = requests.Session()
        self.s.headers['User-Agent'] = 'rift-scout-data-script (github.com/Oradixx/rift-scout)'
        self.delay = delay
        self.user = None

    def _get(self, **params):
        params['format'] = 'json'
        for attempt in range(4):
            r = self.s.get(API, params=params, timeout=60)
            d = r.json()
            if d.get('error', {}).get('code') == 'ratelimited':
                time.sleep(20 * (attempt + 1)); continue
            time.sleep(self.delay)
            return d
        return d

    def login(self):
        user, pw = os.environ.get('LEAGUEPEDIA_USER'), os.environ.get('LEAGUEPEDIA_PASSWORD')
        if not user or not pw: raise SystemExit('LEAGUEPEDIA_USER / LEAGUEPEDIA_PASSWORD absents de l\'environnement')
        tok = self._get(action='query', meta='tokens', type='login')['query']['tokens']['logintoken']
        r = self.s.post(API, data={'action': 'login', 'lgname': user.strip(), 'lgpassword': pw.strip(), 'lgtoken': tok, 'format': 'json'}, timeout=60).json()
        res = r.get('login', {})
        if res.get('result') != 'Success': raise SystemExit(f"connexion refusée : {res.get('result')} ({res.get('reason', '')})")
        self.user = res.get('lgusername')
        return self.user

    def cargo(self, tables, fields, where=None, join_on=None, order_by=None, limit=500, max_rows=None):
        out, offset = [], 0
        while True:
            p = dict(action='cargoquery', tables=tables, fields=fields, limit=limit, offset=offset)
            if where: p['where'] = where
            if join_on: p['join_on'] = join_on
            if order_by: p['order_by'] = order_by
            d = self._get(**p)
            if 'error' in d: raise RuntimeError(f"{d['error'].get('code')}: {d['error'].get('info')}")
            rows = [x['title'] for x in d.get('cargoquery', [])]
            out += rows; offset += len(rows)
            if len(rows) < limit or (max_rows and len(out) >= max_rows): return out[:max_rows] if max_rows else out

    def fields(self, table):
        d = self._get(action='cargofields', table=table)
        return d.get('cargofields') if 'error' not in d else None

    def page(self, title):
        d = self._get(action='query', prop='revisions', rvprop='content', rvslots='main', titles=title)
        for pg in d.get('query', {}).get('pages', {}).values():
            rev = pg.get('revisions')
            if rev: return rev[0]['slots']['main']['*']
        return None


def main():
    lp = Leaguepedia()
    print('connecté en tant que :', lp.login())
    ui = lp._get(action='query', meta='userinfo', uiprop='ratelimits|groups')['query']['userinfo']
    print('groupes :', ui.get('groups')); print('limite cargo-query :', ui.get('ratelimits', {}).get('cargo-query'))
    for t in ['Players', 'Tenures', 'RosterChanges', 'TournamentRosters', 'Contracts', 'ScoreboardGames', 'ScoreboardPlayers', 'MatchScheduleGame', 'PostgameJsonMetadata']:
        f = lp.fields(t)
        print(f'\n[{t}]', 'introuvable' if f is None else ', '.join(sorted(f)))
    print('\n--- joueurs : exemple')
    try:
        for r in lp.cargo('Players', 'ID,OverviewPage,Team,Role,Country,Residency,Birthdate,Contract,IsRetired', where='ID IN ("Chovy","kyeahoo","Labrov")'): print(r)
    except Exception as e: print('erreur', e)
    print('\n--- dernières parties et identifiant Riot')
    games = []
    try:
        games = lp.cargo('ScoreboardGames=SG,MatchScheduleGame=MSG', 'SG.GameId,SG.Tournament,SG.Team1,SG.Team2,SG.DateTime_UTC,MSG.RiotPlatformGameId,MSG.RiotVersion',
                         join_on='SG.GameId=MSG.GameId', where='SG.DateTime_UTC > "2026-10-01"', order_by='SG.DateTime_UTC DESC', limit=5, max_rows=5)
        for g in games: print(g)
    except Exception as e: print('erreur', e)
    print('\n--- stats par joueur d\'une partie')
    try:
        if games:
            for r in lp.cargo('ScoreboardPlayers', 'Link,Team,Role,Champion,Kills,Deaths,Assists,Gold,CS,DamageToChampions,VisionScore', where=f'GameId="{games[0]["GameId"]}"', limit=10, max_rows=10): print(r)
    except Exception as e: print('erreur', e)
    print('\n--- chronologie d\'une partie (événements à la seconde)')
    for g in games:
        rid = g.get('RiotPlatformGameId')
        if not rid: continue
        for title in (f'V5 data:{rid}/Timeline', f'V5 data:{rid}'):
            txt = lp.page(title)
            if not txt: print(title, ': page absente'); continue
            print(title, ':', len(txt) // 1000, 'Ko')
            try:
                d = json.loads(txt)
                if 'frames' in d:
                    ev = {}
                    for fr in d['frames']:
                        for e in fr.get('events', []): ev[e.get('type')] = ev.get(e.get('type'), 0) + 1
                    print('  images :', len(d['frames']), '| intervalle (ms) :', d.get('frameInterval'), '| événements :', ev)
                    k = next((e for fr in d['frames'] for e in fr.get('events', []) if e.get('type') == 'CHAMPION_KILL'), None)
                    print('  exemple de kill, champs :', sorted(k) if k else None)
                    pf = d['frames'][5]['participantFrames'] if len(d['frames']) > 5 else {}
                    one = next(iter(pf.values()), {}); print('  suivi par joueur chaque minute, champs :', sorted(one))
                else:
                    print('  clés :', sorted(d)[:20]); p0 = (d.get('participants') or [{}])[0]; print('  champs par joueur :', len(p0), sorted(p0)[:60])
            except Exception as e: print('  lecture impossible :', e)
        break
    print('\ntest terminé')


if __name__ == '__main__':
    main()
