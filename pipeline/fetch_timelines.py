"""Télécharge les chronologies de parties depuis Leaguepedia et n'en garde que quelques mesures par joueur :
morts inutiles, kills gratuits, participation aux objectifs, proximité du jungler, déplacements du support.
Écrit pipeline/lp_timeline_<année>.csv.gz, complété à chaque lancement (les parties déjà traitées sont sautées).

    python pipeline/fetch_timelines.py [année] [minutes max]

Demande LEAGUEPEDIA_USER et LEAGUEPEDIA_PASSWORD pour lister les parties. La LPL n'a pas de chronologie.
"""
import csv, datetime as dt, gzip, io, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leaguepedia import Leaguepedia

HERE = os.path.dirname(os.path.abspath(__file__))
NEAR = 2500          # unités de carte : « près de » (la carte fait environ 15 000 de côté)
TRADE_DIST = 3000    # un kill allié à moins de cette distance d'une mort la rend utile
COLS = ['gameid', 'pid', 'deaths', 'worthless', 'ka', 'free_ka', 'obj_ka', 'team_obj', 'jg_prox', 'ejg_prox', 'jg_top', 'jg_mid', 'jg_bot',
        'roam', 'fwd', 'gank_d15', 'jg_ka15', 'ka15', 'jg_ok']


def team_of(pid): return 100 if pid <= 5 else 200


def dist(a, b): return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


def features(tl):
    """Une ligne par joueur (pid 1-5 côté bleu, 6-10 côté rouge, dans l'ordre top, jungle, mid, ADC, support)."""
    frames = tl['frames']
    ev = [e for f in frames for e in f.get('events', [])]
    kills = [e for e in ev if e.get('type') == 'CHAMPION_KILL' and e.get('victimId')]
    objs = []                       # (instant, équipe qui prend, joueurs impliqués)
    for e in ev:
        if e.get('type') == 'ELITE_MONSTER_KILL' and e.get('killerTeamId') in (100, 200):
            objs.append((e['timestamp'], e['killerTeamId'], [e.get('killerId', 0)] + e.get('assistingParticipantIds', [])))
        elif e.get('type') == 'BUILDING_KILL' and e.get('teamId') in (100, 200):
            objs.append((e['timestamp'], 300 - e['teamId'], [e.get('killerId', 0)] + e.get('assistingParticipantIds', [])))
    R = {p: dict(deaths=0, worthless=0, ka=0, free_ka=0, obj_ka=0, team_obj=0, gank_d15=0, jg_ka15=0, ka15=0) for p in range(1, 11)}
    for k in kills:
        v, t, pos = k['victimId'], k['timestamp'], k.get('position')
        who = [k.get('killerId', 0)] + k.get('assistingParticipantIds', [])
        vt = team_of(v)
        # mort utile : son équipe tue quelqu'un au même endroit dans la foulée, ou prend un objectif dans la minute
        traded = any(team_of(o['victimId']) != vt and -15000 <= o['timestamp'] - t <= 30000 and (not pos or not o.get('position') or dist(pos, o['position']) <= TRADE_DIST)
                     for o in kills if o is not k)
        traded = traded or any(tm == vt and 0 <= ot - t <= 60000 for ot, tm, _ in objs)
        R[v]['deaths'] += 1; R[v]['worthless'] += (not traded)
        jg_enemy = 2 if vt == 200 else 7
        if t < 900000 and jg_enemy in who: R[v]['gank_d15'] += 1
        for p in who:
            if not 1 <= p <= 10 or team_of(p) == vt: continue
            R[p]['ka'] += 1; R[p]['free_ka'] += (not traded)
            if t < 900000:
                R[p]['ka15'] += 1
                jg_own = 2 if team_of(p) == 100 else 7
                if p != jg_own and jg_own in who: R[p]['jg_ka15'] += 1
    for _, tm, who in objs:
        for p in range(1, 11):
            if team_of(p) == tm: R[p]['team_obj'] += 1; R[p]['obj_ka'] += (p in who)
    # positions, une par minute, de la 3e à la 14e minute
    P = []
    for f in frames[3:15]:
        pf = f.get('participantFrames', {})
        row = {int(k): v.get('position') for k, v in pf.items() if v.get('position')}
        if len(row) == 10: P.append(row)
    near = lambda a, b: sum(dist(r[a], r[b]) < NEAR for r in P) / len(P) if P else None
    f10 = frames[10].get('participantFrames', {}) if len(frames) > 10 else {}
    jm = {int(k): v.get('jungleMinionsKilled', 0) for k, v in f10.items()}
    out = []
    for p in range(1, 11):
        blue = p <= 5; base = 0 if blue else 5; jg, ejg = base + 2, (5 if blue else 0) + 2
        r = R[p]
        r['jg_prox'] = near(p, jg) if p != jg else None
        r['ejg_prox'] = near(p, ejg) if p != jg else None
        r['jg_top'], r['jg_mid'], r['jg_bot'] = (near(jg, base + 1), near(jg, base + 3), near(jg, base + 4)) if p == jg else (None, None, None)
        r['roam'] = (sum(dist(x[p], x[base + 4]) > 3500 for x in P) / len(P) if P else None) if p == base + 5 else None
        r['fwd'] = (sum(((x[p]['x'] + x[p]['y']) > 16000) == blue and abs(x[p]['x'] + x[p]['y'] - 15000) > 1000 for x in P) / len(P)) if P else None
        team = [q for q in jm if (q <= 5) == blue]
        r['jg_ok'] = int(bool(team) and max(team, key=lambda q: jm[q]) == jg)
        out.append(r)
    return out


def load(path):
    if not os.path.exists(path): return [], set()
    rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(path, 'rb'), encoding='utf-8')))
    return rows, {r['gameid'] for r in rows}


def save(path, rows):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().year
    budget = float(sys.argv[2]) * 60 if len(sys.argv) > 2 else 3600
    path = os.path.join(HERE, f'lp_timeline_{year}.csv.gz')
    rows, done = load(path)
    lp = Leaguepedia(delay=0.25)
    print('connecté en tant que :', lp.login())
    todo = lp.cargo('ScoreboardGames=SG,PostgameJsonMetadata=PJ', 'SG.RiotPlatformGameId,PJ.TimelinePage,SG.DateTime_UTC,SG.Tournament', join_on='SG.GameId=PJ.GameId',
                    where=f'SG.DateTime_UTC >= "{year}-01-01" AND SG.DateTime_UTC < "{year + 1}-01-01" AND PJ.TimelinePage IS NOT NULL', order_by='SG.DateTime_UTC DESC')
    todo = [g for g in todo if g.get('RiotPlatformGameId') and g['RiotPlatformGameId'] not in done]
    print(f'{len(done)} parties déjà traitées, {len(todo)} à traiter')
    t0, n, fails, bad_jg = time.time(), 0, 0, 0
    for g in todo:
        if time.time() - t0 > budget or fails >= 25: break
        try:
            tl = json.loads(lp.page(g['TimelinePage']))
            fs = features(tl)
        except Exception as e:
            fails += 1; print('échec', g['RiotPlatformGameId'], type(e).__name__); time.sleep(5); continue
        fails = 0
        for i, r in enumerate(fs, 1):
            r = {k: (round(v, 3) if isinstance(v, float) else ('' if v is None else v)) for k, v in r.items()}
            r['gameid'] = g['RiotPlatformGameId']; r['pid'] = i; rows.append(r)
        bad_jg += sum(1 for r in fs if not r['jg_ok']) > 0
        n += 1
        if n % 250 == 0: save(path, rows); print(f'{n} parties, {int(time.time() - t0)} s')
    save(path, rows)
    print(f'terminé : {n} parties ajoutées en {int(time.time() - t0)} s, {len(todo) - n} restantes, {bad_jg} parties où le jungler n\'est pas en position 2')


if __name__ == '__main__':
    main()
