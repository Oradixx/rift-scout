"""Parties absentes d'Oracle's Elixir, récupérées sur Leaguepedia et converties au format d'Oracle's Elixir.

Deux sortes de parties :
  - les ligues de clubs que seul Leaguepedia couvre (LP_LEAGUES ci-dessous : 2e division de la Prime League, Benelux,
    2e division de l'Arabian League, Islande, Nexus Tour) ;
  - toute partie jouée depuis moins de RECENT_DAYS jours, pour ne pas attendre Oracle's Elixir (finale des Worlds...).
    Une partie qu'Oracle's Elixir publie ensuite est ignorée par build.py (même identifiant de partie).
Écrit pipeline/lp_games_<année>.csv.gz, complété à chaque lancement (les parties déjà converties sont sautées).
Avec --check N, convertit aussi N parties de LEC qu'Oracle's Elixir possède, dans pipeline/lp_games_check_<année>.csv.gz,
pour comparer la conversion aux chiffres d'Oracle's Elixir (tools/check_lp_games.py).

    python pipeline/fetch_lp_games.py [année] [minutes max] [--check N]

Demande LEAGUEPEDIA_USER et LEAGUEPEDIA_PASSWORD (secrets GitHub, workflow « Parties Leaguepedia »).
Aucun nom civil n'est demandé : seulement le pseudo (page du joueur sur Leaguepedia).
"""
import csv, datetime as dt, gzip, io, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leaguepedia import Leaguepedia

HERE = os.path.dirname(os.path.abspath(__file__))
RECENT_DAYS = 21
# tournoi Leaguepedia (début du nom) -> code de ligue (voir leagues.json)
LP_LEAGUES = [('PRM 2nd Division', 'PRM2'), ('Benelux Ascend Series', 'BAS'), ('Arabian League 2nd Division', 'AL2'),
              ('Icelandic Esports League', 'IEL'), ('Nexus Tour', 'NXT')]
# tournois des ligues qu'Oracle's Elixir couvre déjà (pour les parties récentes) : début du nom -> code
OE_LEAGUES = [('Worlds', 'WLDs'), ('MSI', 'MSI'), ('First Stand', 'FST'), ('Esports World Cup', 'EWC'), ('LCK CL', 'LCKC'), ('LCK AS', 'LAS'),
              ('LCK Cup', 'LCK'), ('LCK', 'LCK'), ('LPL', 'LPL'), ('LEC', 'LEC'), ('LCS', 'LCS'), ('CBLOL', 'CBLOL'), ('LCP', 'LCP'), ('LJL', 'LJL'),
              ('PCS', 'PCS'), ('VCS', 'VCS'), ('LFL', 'LFL'), ('PRM 1st Division', 'PRM'), ('LES', 'LES'), ('NLC', 'NLC'), ('TCL', 'TCL'),
              ('EM ', 'EM'), ('NACL', 'NACL'), ('Nexus League', 'NL'), ('Arabian League', 'AL'), ('Rift Legends', 'RL'), ('EBL', 'EBL'),
              ('HLL', 'HLL'), ('LIT', 'LIT'), ('Road Of Legends', 'ROL'), ('Hitpoint Masters', 'HM'), ('Hitpoint 2nd Div Challengers', 'HC'),
              ('LRN', 'LRN'), ('LRS', 'LRS'), ('CD ', 'CD'), ('LPLOL', 'LPLOL'), ('KeSPA Cup', 'KeSPA Cup'), ('Demacia Cup Global', 'DCGI'),
              ('Demacia Cup', 'DCup'), ('World Star Challengers', 'WSCI'), ('Asia Masters', 'AM')]
POS = {'TOP': 'top', 'JUNGLE': 'jng', 'MIDDLE': 'mid', 'BOTTOM': 'bot', 'UTILITY': 'sup'}
LP_ROLE = {'Top': 'top', 'Jungle': 'jng', 'Mid': 'mid', 'Bot': 'bot', 'Support': 'sup'}
COLS = ['gameid', 'league', 'split', 'playoffs', 'date', 'patch', 'participantid', 'side', 'position', 'playername', 'playerid', 'teamname', 'teamid',
        'champion', 'gamelength', 'result', 'kills', 'deaths', 'assists', 'teamkills', 'teamdeaths', 'firstbloodkill', 'firstbloodassist',
        'damagetochampions', 'dpm', 'damageshare', 'damagetakenperminute', 'totalgold', 'earnedgold', 'earned gpm', 'earnedgoldshare', 'total cs', 'cspm',
        'visionscore', 'vspm', 'wardsplaced', 'wpm', 'wardskilled', 'wcpm', 'controlwardsbought',
        'goldat10', 'xpat10', 'csat10', 'golddiffat10', 'xpdiffat10', 'csdiffat10', 'goldat15', 'xpat15', 'csat15', 'golddiffat15', 'xpdiffat15', 'csdiffat15',
        'killsat15', 'assistsat15', 'deathsat15', 'dragons', 'opp_dragons', 'barons', 'opp_barons', 'void_grubs', 'opp_void_grubs', 'heralds',
        'towers', 'opp_towers', 'firstdragon', 'firstherald', 'firstbaron', 'firsttower', 'turretplates', 'opp_turretplates', 'source']


def league_of(tournament):
    for pre, code in LP_LEAGUES:
        if tournament.startswith(pre): return code, True
    for pre, code in OE_LEAGUES:
        if tournament.startswith(pre): return code, False
    return None, False


def split_of(t):
    m = re.search(r'(Winter|Spring|Summer|Fall|Autumn|Season Finals|Etape \d+|Last Chance|Kickoff|Split \d+|Play-In|Main Event)', t)
    s = m.group(1) if m else None
    return {'Autumn': 'Fall'}.get(s, s)


def unwrap(txt):
    d = json.loads(txt)
    return d.get('info', d) if isinstance(d, dict) else d


def convert(g, stats, tl, sp):
    """g : ligne ScoreboardGames ; stats / tl : JSON Riot (match et chronologie) ; sp : {(côté, poste): (pseudo, équipe, champion)}"""
    P = stats['participants']; minutes = stats.get('gameDuration', 0)
    if minutes > 20000: minutes /= 1000           # anciennes versions en millisecondes
    gl = float(minutes); mins = gl / 60
    frames = tl.get('frames', []) if tl else []
    def frame(k): return frames[k].get('participantFrames', {}) if len(frames) > k else {}
    f10, f15 = frame(10), frame(15)
    ev = [e for f in frames for e in f.get('events', [])]
    kills15 = [e for e in ev if e.get('type') == 'CHAMPION_KILL' and e.get('timestamp', 1e12) <= 900000]
    plates = {100: 0, 200: 0}
    for e in ev:
        if e.get('type') == 'TURRET_PLATE_DESTROYED' and e.get('teamId') in (100, 200): plates[300 - e['teamId']] += 1
    side = {100: 'Blue', 200: 'Red'}
    team_obj = {t['teamId']: t.get('objectives', {}) for t in stats.get('teams', [])}
    win = {t['teamId']: int(bool(t.get('win'))) for t in stats.get('teams', [])}
    tk = {s: sum(p.get('kills', 0) for p in P if p.get('teamId') == s) for s in (100, 200)}
    td = {s: sum(p.get('deaths', 0) for p in P if p.get('teamId') == s) for s in (100, 200)}
    dmg = {s: sum(p.get('totalDamageDealtToChampions', 0) for p in P if p.get('teamId') == s) for s in (100, 200)}
    passive = max(0.0, 122.4 * (mins - 65 / 60))
    earned = {p['participantId']: max(0.0, p.get('goldEarned', 0) - 500 - passive) for p in P}
    egold = {s: sum(earned[p['participantId']] for p in P if p.get('teamId') == s) for s in (100, 200)}
    pos_of = {p['participantId']: POS.get(p.get('teamPosition') or p.get('individualPosition'), None) for p in P}
    opp = {}
    for p in P:
        for q in P:
            if q['teamId'] != p['teamId'] and pos_of[q['participantId']] == pos_of[p['participantId']]: opp[p['participantId']] = q['participantId']
    def at(fr, pid, what):
        x = fr.get(str(pid)) or {}
        if what == 'gold': return x.get('totalGold')
        if what == 'xp': return x.get('xp')
        if what == 'cs': return (x.get('minionsKilled', 0) + x.get('jungleMinionsKilled', 0)) if x else None
    def diff(fr, pid, what):
        a, b = at(fr, pid, what), at(fr, opp.get(pid), what) if opp.get(pid) else None
        return None if a is None or b is None else a - b
    league, _ = league_of(g['Tournament'])
    base = dict(gameid=g['RiotPlatformGameId'], league=league, split=split_of(g['Tournament']), playoffs=int('Playoff' in g['Tournament'] or 'Final' in g['Tournament']),
                date=(g.get('DateTime_UTC') or '').replace('T', ' ')[:19], patch=stats.get('gameVersion', '')[:5], gamelength=round(gl), source='leaguepedia')
    # côté de chaque joueur : Leaguepedia note 1 / 2 ; on vérifie avec les champions joués et on inverse si besoin
    norm = lambda x: re.sub(r'[^a-z]', '', (x or '').lower())
    ok = sum(norm((sp.get((side[p['teamId']], pos_of[p['participantId']])) or (0, 0, ''))[2]) == norm(p.get('championName')) for p in P)
    sw = sum(norm((sp.get((side[300 - p['teamId']], pos_of[p['participantId']])) or (0, 0, ''))[2]) == norm(p.get('championName')) for p in P)
    if sw > ok: sp = {(('Red' if k[0] == 'Blue' else 'Blue'), k[1]): v for k, v in sp.items()}
    rows, teamname = [], {}
    for p in P:
        pid, s = p['participantId'], p['teamId']; po = pos_of[pid]
        if po is None: return None
        nm, team, champ = sp.get((side[s], po), (None, None, None))
        if not nm or not team: return None
        teamname[s] = team
        cs = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
        r = dict(base, participantid=pid, side=side[s], position=po, playername=nm, playerid='lp:' + nm, teamname=team, teamid='lp:' + team,
                 champion=champ or p.get('championName'), result=win.get(s, 0), kills=p.get('kills', 0), deaths=p.get('deaths', 0), assists=p.get('assists', 0),
                 teamkills=tk[s], teamdeaths=td[s], firstbloodkill=int(bool(p.get('firstBloodKill'))), firstbloodassist=int(bool(p.get('firstBloodAssist'))),
                 damagetochampions=p.get('totalDamageDealtToChampions', 0), dpm=round(p.get('totalDamageDealtToChampions', 0) / mins, 2),
                 damageshare=round(p.get('totalDamageDealtToChampions', 0) / dmg[s], 4) if dmg[s] else None,
                 damagetakenperminute=round(p.get('totalDamageTaken', 0) / mins, 2), totalgold=p.get('goldEarned', 0), earnedgold=round(earned[pid]),
                 **{'earned gpm': round(earned[pid] / mins, 2), 'total cs': cs}, earnedgoldshare=round(earned[pid] / egold[s], 4) if egold[s] else None,
                 cspm=round(cs / mins, 3), visionscore=p.get('visionScore', 0), vspm=round(p.get('visionScore', 0) / mins, 3),
                 wardsplaced=p.get('wardsPlaced', 0), wpm=round(p.get('wardsPlaced', 0) / mins, 3), wardskilled=p.get('wardsKilled', 0),
                 wcpm=round(p.get('wardsKilled', 0) / mins, 3), controlwardsbought=p.get('visionWardsBoughtInGame', 0),
                 goldat10=at(f10, pid, 'gold'), xpat10=at(f10, pid, 'xp'), csat10=at(f10, pid, 'cs'),
                 golddiffat10=diff(f10, pid, 'gold'), xpdiffat10=diff(f10, pid, 'xp'), csdiffat10=diff(f10, pid, 'cs'),
                 goldat15=at(f15, pid, 'gold'), xpat15=at(f15, pid, 'xp'), csat15=at(f15, pid, 'cs'),
                 golddiffat15=diff(f15, pid, 'gold'), xpdiffat15=diff(f15, pid, 'xp'), csdiffat15=diff(f15, pid, 'cs'),
                 killsat15=sum(e.get('killerId') == pid for e in kills15) if frames else None,
                 assistsat15=sum(pid in e.get('assistingParticipantIds', []) for e in kills15) if frames else None,
                 deathsat15=sum(e.get('victimId') == pid for e in kills15) if frames else None)
        rows.append(r)
    for s in (100, 200):
        o, oo = team_obj.get(s, {}), team_obj.get(300 - s, {})
        k = lambda d, x: (d.get(x) or {}).get('kills')
        f = lambda d, x: int(bool((d.get(x) or {}).get('first')))
        g15 = [at(f15, p['participantId'], 'gold') for p in P]
        tg15 = None if None in g15 else sum(x for x, p in zip(g15, P) if p['teamId'] == s) - sum(x for x, p in zip(g15, P) if p['teamId'] != s)
        rows.append(dict(base, participantid=100 + (s // 100), side=side[s], position='team', playername=None, playerid=None, teamname=teamname.get(s),
                         teamid='lp:' + str(teamname.get(s)), champion=None, result=win.get(s, 0), kills=tk[s], deaths=td[s], teamkills=tk[s], teamdeaths=td[s],
                         damagetochampions=dmg[s], dpm=round(dmg[s] / mins, 2), totalgold=sum(p.get('goldEarned', 0) for p in P if p['teamId'] == s),
                         earnedgold=round(egold[s]), golddiffat15=tg15, dragons=k(o, 'dragon'), opp_dragons=k(oo, 'dragon'), barons=k(o, 'baron'),
                         opp_barons=k(oo, 'baron'), void_grubs=k(o, 'horde'), opp_void_grubs=k(oo, 'horde'), heralds=k(o, 'riftHerald'),
                         towers=k(o, 'tower'), opp_towers=k(oo, 'tower'), firstdragon=f(o, 'dragon'), firstherald=f(o, 'riftHerald'), firstbaron=f(o, 'baron'),
                         firsttower=f(o, 'tower'), turretplates=plates[s], opp_turretplates=plates[300 - s]))
    return rows


def load(path):
    if not os.path.exists(path): return [], set()
    rows = list(csv.DictReader(io.TextIOWrapper(gzip.open(path, 'rb'), encoding='utf-8')))
    return rows, {r['gameid'] for r in rows}


def save(path, rows):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS, extrasaction='ignore'); w.writeheader(); w.writerows(rows)


def clean_name(link):
    return re.sub(r'\s*\(.*\)$', '', link or '').strip() or None


def run(lp, games, path, budget, t0):
    rows, done = load(path)
    todo = [g for g in games if g['RiotPlatformGameId'] not in done]
    print(f'{os.path.basename(path)} : {len(done)} parties déjà converties, {len(todo)} à convertir')
    # pseudos, équipes et champions par partie (une requête par tournoi)
    sp = {}
    for tour in sorted({g['Tournament'] for g in todo}):
        for r in lp.cargo('ScoreboardPlayers=SP,ScoreboardGames=SG', 'SG.RiotPlatformGameId=rid,SP.Link,SP.Team,SP.Side,SP.Role,SP.Champion',
                          join_on='SP.GameId=SG.GameId', where=f'SG.Tournament="{tour}"'):
            po = LP_ROLE.get(r.get('Role'))
            if r.get('rid') and po: sp.setdefault(r['rid'], {})[('Blue' if str(r.get('Side')) == '1' else 'Red', po)] = (clean_name(r.get('Link')), r.get('Team'), r.get('Champion'))
    n = fails = skipped = 0
    for g in todo:
        if time.time() - t0 > budget or fails >= 25: break
        rid = g['RiotPlatformGameId']
        try:
            st = lp.page(g.get('StatsPage') or f'V5 data:{rid}'); tl = lp.page(g.get('TimelinePage') or f'V5 data:{rid}/Timeline')
            if not st: skipped += 1; continue
            out = convert(g, unwrap(st), unwrap(tl) if tl else None, sp.get(rid, {}))
        except Exception as e:
            fails += 1; print('échec', rid, type(e).__name__, str(e)[:120]); time.sleep(5); continue
        fails = 0
        if not out: skipped += 1; continue
        rows += out; n += 1
        if n % 100 == 0: save(path, rows); print(f'{n} parties, {int(time.time() - t0)} s')
    save(path, rows)
    print(f'{n} parties ajoutées, {skipped} sans données exploitables, {len(todo) - n - skipped} restantes')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    year = int(args[0]) if args else dt.date.today().year
    budget = float(args[1]) * 60 if len(args) > 1 else 3600
    check = int(sys.argv[sys.argv.index('--check') + 1]) if '--check' in sys.argv else 0
    lp = Leaguepedia(delay=0.25)
    print('connecté en tant que :', lp.login())
    where = f'SG.DateTime_UTC >= "{year}-01-01" AND SG.DateTime_UTC < "{year + 1}-01-01"'
    try:
        allg = lp.cargo('ScoreboardGames=SG,PostgameJsonMetadata=PJ', 'SG.RiotPlatformGameId,SG.Tournament,SG.DateTime_UTC,PJ.StatsPage,PJ.TimelinePage',
                        join_on='SG.GameId=PJ.GameId', where=where, order_by='SG.DateTime_UTC DESC')
    except RuntimeError as e:      # champ StatsPage absent : les pages se déduisent de l'identifiant Riot
        print('requête sans StatsPage :', e)
        allg = lp.cargo('ScoreboardGames=SG,PostgameJsonMetadata=PJ', 'SG.RiotPlatformGameId,SG.Tournament,SG.DateTime_UTC,PJ.TimelinePage',
                        join_on='SG.GameId=PJ.GameId', where=where, order_by='SG.DateTime_UTC DESC')
    allg = [g for g in allg if g.get('RiotPlatformGameId') and g.get('Tournament')]
    recent = (dt.datetime.utcnow() - dt.timedelta(days=RECENT_DAYS)).strftime('%Y-%m-%d')
    games = []
    for g in allg:
        code, lp_only = league_of(g['Tournament'])
        if code and (lp_only or (g.get('DateTime_UTC') or '') >= recent): games.append(g)
    print(f'{len(allg)} parties sur Leaguepedia en {year}, {len(games)} retenues (ligues absentes d\'Oracle\'s Elixir, ou jouées depuis le {recent})')
    t0 = time.time()
    run(lp, games, os.path.join(HERE, f'lp_games_{year}.csv.gz'), budget, t0)
    if check:
        lec = [g for g in allg if g['Tournament'].startswith('LEC') and (g.get('DateTime_UTC') or '') < recent][:check]
        run(lp, lec, os.path.join(HERE, f'lp_games_check_{year}.csv.gz'), budget + 600, t0)


if __name__ == '__main__':
    main()
