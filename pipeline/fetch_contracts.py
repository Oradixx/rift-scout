"""Télécharge la base publique des contrats reconnus par Riot (« League-Recognized Contract Database »)
et n'en garde que : ligue, équipe, pseudo, poste, date de fin de contrat. Écrit pipeline/contracts.json.

Source : https://docs.google.com/spreadsheets/d/1Y7k5kQ2AegbuyiGwEPsa62e883FYVtHqr6UVut9RC4o/pubhtml
"""
import datetime as dt, html, json, os, re, urllib.request

DOC = 'https://docs.google.com/spreadsheets/d/1Y7k5kQ2AegbuyiGwEPsa62e883FYVtHqr6UVut9RC4o/pubhtml'
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'rift-scout-data-script'}), timeout=60).read().decode('utf-8', 'ignore')


def table(page):
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', page, flags=re.S):
        c = [html.unescape(re.sub(r'<[^>]+>', '', x)).replace('\xa0', ' ').strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', tr, flags=re.S)]
        if any(c): out.append(c)
    return out


def parse_date(s):
    s = re.sub(r'(\d)(st|nd|rd|th)', r'\1', s.strip())
    for f in ('%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%m/%d/%Y', '%Y/%m/%d', '%Y-%m-%d', '%d %B %Y'):
        try: return dt.datetime.strptime(s, f).date().isoformat()
        except ValueError: pass
    return None


def main():
    index = get(DOC)
    tabs = re.findall(r'name: "([^"]+)", pageUrl: "[^"]+", gid: "(\d+)"', index)
    rows, updated = [], {}
    for name, gid in tabs:
        if name == 'INFO': continue
        t = table(get(f'{DOC}/sheet?headers=false&gid={gid}'))
        head = next((r for r in t if r and r[0] == 'League'), None)
        if not head: print('onglet ignoré (pas d\'en-tête) :', name); continue
        col = {k: next((i for i, h in enumerate(head) if re.search(p, h, re.I)), None)
               for k, p in (('team', r'^team$'), ('name', r'summoner'), ('role', r'role|position'), ('end', r'end'), ('status', r'^status$'))}
        up = next((r[1] for r in t if r and 'UPDATE' in r[0].upper() and len(r) > 1), '')
        updated[name] = up
        n = 0
        for r in t:
            if r is head or len(r) <= max(v for v in col.values() if v is not None): continue
            end = parse_date(r[col['end']])
            if not end or not r[col['name']]: continue
            rows.append({'tab': name, 'league': r[0], 'team': r[col['team']], 'name': r[col['name']],
                         'role': r[col['role']] if col['role'] is not None else '', 'end': end,
                         'status': r[col['status']] if col['status'] is not None else ''})
            n += 1
        print(name, n, 'contrats, mis à jour :', up)
    json.dump({'source': DOC, 'fetched': dt.date.today().isoformat(), 'updated': updated, 'contracts': rows},
              open(os.path.join(HERE, 'contracts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('écrit pipeline/contracts.json :', len(rows), 'contrats')


if __name__ == '__main__':
    main()
