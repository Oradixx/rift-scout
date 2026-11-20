/* Rift Scout — classement, fiche joueur, scouting. Données : window.DATA (voir pipeline/build.py). */
(function () {
  'use strict';
  const D = window.DATA;
  const ROLES = ['Top', 'Jungle', 'Mid', 'ADC', 'Support'];
  const FAC = D.facets;
  const FLABEL = { lane: 'Phase de lane', early: 'Début de partie', fight: 'Teamfight', carry: 'Dégâts', eco: 'Farm et or', vision: 'Vision', safe: 'Survie', obj: 'Objectifs' };
  /* un jungler n'a pas de lane : pour lui, la même mesure (or, XP et camps face à son vis-à-vis) porte un autre nom */
  const JG = { label: 'Avance à 15 min', say: 'prend l\'avance sur le jungler adverse (or, XP et camps à 15 min)', low: 'en retard sur le jungler adverse à 15 min' };
  const fLabel = (f, role) => (f === 'lane' && role === 'Jungle' ? JG.label : FLABEL[f]);
  const fSay = (f, role) => (f === 'lane' && role === 'Jungle' ? JG.say : FSAY[f]);
  const fLow = (f, role) => (f === 'lane' && role === 'Jungle' ? JG.low : FLOW[f]);
  const FSHORT = { lane: 'Lane', early: 'Début', fight: 'TF', carry: 'Dég.', eco: 'Or', vision: 'Vis.', safe: 'Surv.', obj: 'Obj.' };
  const FSAY = {
    lane: 'gagne sa lane (or, XP et sbires à 15 min)', early: 'pèse dans les 15 premières minutes', fight: 'présent et efficace dans les combats',
    carry: 'gros dégâts pour son poste', eco: 'farm et revenus élevés', vision: 'contrôle de la vision', safe: 'meurt peu', obj: 'son équipe prend les objectifs neutres'
  };
  const FLOW = {
    lane: 'souvent en retard à 15 min', early: 'peu d\'impact en début de partie', fight: 'moins présent dans les combats', carry: 'peu de dégâts pour son poste',
    eco: 'farm et revenus en retrait', vision: 'vision en retrait', safe: 'meurt beaucoup', obj: 'son équipe cède les objectifs neutres'
  };
  const TIERS = D.tiers;
  const ROLE_PL = { Top: 'tops', Jungle: 'junglers', Mid: 'mids', ADC: 'ADC', Support: 'supports' };
  const TIER_OF = ['de ligue majeure', 'de deuxième niveau', 'de troisième niveau'];
  const $ = (s, el) => (el || document).querySelector(s);
  const h = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (x, d) => (x == null ? '–' : Number(x).toLocaleString('fr-FR', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }));
  const pctTxt = (x) => (x == null ? '–' : fmt(x * 100, 0) + ' %');
  const lgName = (l) => D.pretty[l] || l;
  const nInt = (x) => Math.round(x);
  /* contrats : seulement pour la saison à laquelle la base de Riot correspond */
  const CT = D.contracts || null;
  const hasCT = () => !!CT && state.season === CT.season;
  const isFree = (p) => !!p.c && p.c <= CT.free_until;
  const cDate = (d, long) => new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', long ? { day: 'numeric', month: 'long', year: 'numeric' } : { month: 'short', year: 'numeric' });
  const cShort = (p) => (!hasCT() || !p.c ? '' : isFree(p) ? `<em class="free">fin de contrat ${cDate(p.c)}</em>` : `<em class="signed">contrat ${cDate(p.c)}</em>`);
  /* âge, pays, résidence (Leaguepedia) : même règle, seulement pour la saison correspondante */
  const hasMeta = () => !!D.meta && state.season === D.meta.season;
  const PAYS = { 'South Korea': 'Corée du Sud', 'China': 'Chine', 'Brazil': 'Brésil', 'United States': 'États-Unis', 'Poland': 'Pologne', 'Germany': 'Allemagne', 'France': 'France', 'Vietnam': 'Vietnam', 'Turkey': 'Turquie', 'Spain': 'Espagne',
    'Czech Republic': 'Tchéquie', 'Taiwan': 'Taïwan', 'Argentina': 'Argentine', 'Greece': 'Grèce', 'Netherlands': 'Pays-Bas', 'Canada': 'Canada', 'Italy': 'Italie', 'Mexico': 'Mexique', 'Portugal': 'Portugal', 'Sweden': 'Suède', 'Denmark': 'Danemark',
    'Japan': 'Japon', 'Chile': 'Chili', 'United Kingdom': 'Royaume-Uni', 'Belgium': 'Belgique', 'Colombia': 'Colombie', 'Finland': 'Finlande', 'Peru': 'Pérou', 'Romania': 'Roumanie', 'Serbia': 'Serbie', 'Australia': 'Australie', 'Bulgaria': 'Bulgarie',
    'Egypt': 'Égypte', 'Slovakia': 'Slovaquie', 'Norway': 'Norvège', 'Russia': 'Russie', 'Tunisia': 'Tunisie', 'Hungary': 'Hongrie', 'Hong Kong': 'Hong Kong', 'Venezuela': 'Venezuela', 'Austria': 'Autriche', 'Croatia': 'Croatie',
    'Philippines': 'Philippines', 'Switzerland': 'Suisse', 'Thailand': 'Thaïlande', 'Slovenia': 'Slovénie', 'Ukraine': 'Ukraine', 'Lithuania': 'Lituanie', 'Morocco': 'Maroc', 'Algeria': 'Algérie', 'Saudi Arabia': 'Arabie saoudite', 'Ireland': 'Irlande', 'Israel': 'Israël', 'Latvia': 'Lettonie', 'Estonia': 'Estonie', 'New Zealand': 'Nouvelle-Zélande', 'Uruguay': 'Uruguay', 'Ecuador': 'Équateur', 'Iceland': 'Islande', 'Lebanon': 'Liban', 'Jordan': 'Jordanie', 'Malaysia': 'Malaisie', 'Singapore': 'Singapour', 'Indonesia': 'Indonésie' };
  const RESID = { 'EMEA': 'EMEA', 'North America': 'Amérique du Nord', 'Brazil': 'Brésil', 'Asia Pacific': 'Asie-Pacifique', 'Korea': 'Corée', 'China': 'Chine', 'Vietnam': 'Vietnam', 'Latin America': 'Amérique latine' };
  const pays = (c) => PAYS[c] || c, resid = (r) => RESID[r] || r;
  const hasAge = () => S.players.some((p) => p.age);
  const ageTxt = (p) => (p.age ? `, ${p.age} ans` : '');
  const cMatch = (p, v) => !v || !hasCT() || (v === 'free' ? isFree(p) : v === 'signed' ? !!p.c && !isFree(p) : !p.c);

  const TIER_IN = ['ligue majeure', 'deuxième niveau', 'troisième niveau'];
  const state = { pw: { tier: '0', region: '', league: '', shown: 100, basis: 'season' }, tr: { league: '' }, calc: 'rift', season: Object.keys(D.seasons).sort().pop(), view: 'rank', role: '', tier: '0', region: '', league: '', event: '', contract: '', basis: 'season', minG: 15, q: '', shown: 100,
    sc: { plan: {}, contract: '', maxAge: 0, res: '', tid: null, role: 'Mid', tier: '', region: '', league: '', minNote: 0, minG: 20, sort: 'score', shown: 60, ref: null, reach: true, mode: 'team',
      cr: { role: '', maxAge: 22, region: '', deep: false, minG: 15, contract: '', fresh: false, all: false, noAge: false, shown: 60 } } };
  let S, byId, med;

  /* note affichée : Rift Scout, mixte (moitié Rift Scout, moitié LoL Ratings) ou unifiée (un seul modèle, champ nu). La note de
     saison et les notes par événement changent ; les notes de ligue, de niveau et de période récente restent celles de Rift Scout. */
  function invNote(n) { const x = n <= 88 ? n : 88 + 11 * Math.atanh(Math.min((n - 88) / 11, 0.999)); return (x - D.scale.a) / D.scale.b; }
  function applyCalc() {
    const mix = state.calc === 'mix', uni = state.calc === 'uni';
    for (const y in D.seasons) {
      const P = D.seasons[y].players;
      for (const p of P) {
        if (p.note0 === undefined) { p.note0 = p.note; p.pts0 = p.pts; }
        const m = mix && p.nm != null, u = uni && p.nu != null;
        const alt = m ? p.nm : u ? p.nu : null;
        p.note = alt != null ? alt : p.note0; p.pts = alt != null ? invNote(alt) : p.pts0;
        for (const e of p.ev) {   // notes par événement : même calcul que la note de saison quand il existe pour cet événement
          if (e.note0 === undefined) e.note0 = e.note;
          const ea = mix && e.nm != null ? e.nm : uni && e.nu != null ? e.nu : null;
          e.note = ea != null ? ea : e.note0;
        }
      }
      P.sort((a, b) => b.note - a.note);
    }
    document.documentElement.dataset.calc = state.calc;
    document.querySelectorAll('#calc button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.calc === state.calc));
  }
  function load() {
    S = D.seasons[state.season];
    byId = new Map(S.players.map((p) => [p.id, p]));
    med = {};
    for (const p of S.players) { const k = p.role + p.tier; (med[k] = med[k] || []).push(p); }
    for (const k in med) {
      const arr = med[k]; const m = FAC.map((_, i) => median(arr.map((p) => p.f[i]).filter((v) => v != null)));
      med[k] = { f: m, note: median(arr.map((p) => p.note)) };
    }
  }
  function median(a) { if (!a.length) return null; a = a.slice().sort((x, y) => x - y); const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; }

  /* couleur d'une note : du gris au cobalt, or au-dessus de 90 */
  function noteVar(n) { return n >= 90 ? 'var(--n4)' : n >= 82 ? 'var(--n3)' : n >= 72 ? 'var(--n2)' : n >= 60 ? 'var(--n1)' : 'var(--n0)'; }
  function noteCls(n) { return n >= 90 ? 't-gold' : n >= 80 ? 't-cob' : n >= 60 ? 't-mid' : 't-low'; }
  function strip(p) {
    return '<span class="strip" aria-hidden="true">' + p.f.map((v, i) => {
      if (v == null) return '<i style="height:3px;background:var(--line)"></i>';
      const hgt = Math.max(16, Math.min(100, 58 + (v - p.note) * 5.5)); // hauteur : écart à sa propre note, pour lire la forme du profil
      return `<i title="${fLabel(FAC[i], p.role)} : ${nInt(v)}" style="height:${hgt}%;background:${noteVar(v)}"></i>`;
    }).join('') + '</span>';
  }
  function evNote(p, ev) { const e = p.ev.find((x) => x.e === ev); return e || null; }

  /* ------------------------------------------------------------ style de jeu */
  // indices du vecteur s : 0 or, 1 dégâts, 2 part des kills, 3 kills+assists à 15, 4 participation à 15, 5 morts, 6 dégâts subis, 7 vision, 8 farm, 9 champions carry, 10 champions tank
  const ARCH = {
    Top: [['Carry de side lane', [0, 1, 9], []], ['Tank de première ligne', [6, 10], [1]], ['Weakside solide', [], [0, 5, 4]], ['Bagarreur de début de partie', [3, 4, 2], []]],
    Jungle: [['Jungler carry', [0, 1, 8], []], ['Facilitateur', [7, 4], [0]], ['Agresseur précoce', [3, 2], []], ['Jungler de première ligne', [6, 10], [1]]],
    Mid: [['Carry principal', [0, 1, 2], []], ['Contrôle et farm', [8], [5, 3]], ['Faiseur de jeu', [3, 4], [8]], ['Mid utilitaire', [7], [0, 1]]],
    ADC: [['Hypercarry', [0, 1, 8], []], ['Agressif en lane', [3, 2, 4], []], ['Sûr, tourné vers la fin de partie', [8], [5, 3]], ['ADC utilitaire', [7], [0, 1]]],
    Support: [['Engage, première ligne', [6, 10], []], ['Protecteur', [], [6, 10, 5]], ['Faiseur de jeu', [3, 4], []], ['Contrôle de vision', [7], [3]]]
  };
  function archetype(p) {
    if (!p.s) return null;
    let best = null, bv = 0.45;
    for (const [name, plus, minus] of ARCH[p.role]) {
      const v = (plus.reduce((a, i) => a + p.s[i], 0) - minus.reduce((a, i) => a + p.s[i], 0)) / (plus.length + minus.length);
      if (v > bv) { bv = v; best = name; }
    }
    return best || 'Profil équilibré';
  }
  function styleDist2(a, b) { let d = 0; for (let i = 0; i < a.s.length; i++) { const x = a.s[i] - b.s[i]; d += x * x; } return d; }
  function similarity(a, b) { if (!a.s || !b.s) return null; return 100 * Math.exp(-styleDist2(a, b) / 18); }

  /* ------------------------------------------------------------ forces / faiblesses */
  function insights(p) {
    const plus = [], minus = [], w = D.weights[p.role];
    const grp = ROLE_PL[p.role] + ' ' + TIER_OF[p.tier];
    // Forces et points faibles : lus sur la seule part individuelle de chaque facette (fi), à niveau d'équipe égal.
    // Les notes de facette, elles, contiennent le niveau de l'équipe : chez Gen.G, toutes seraient des forces.
    const fi = p.fi || p.fp;
    const idx = FAC.map((f, i) => i).filter((i) => fi[i] != null && (w[FAC[i]] > 0 || FAC[i] === 'obj'));
    idx.slice().sort((a, b) => fi[b] - fi[a]).slice(0, 3).forEach((i) => {
      if (fi[i] >= 0.7) plus.push(`<b>${fLabel(FAC[i], p.role)}</b> : ${fSay(FAC[i], p.role)} (${topTxt(fi[i])} des ${grp}, à niveau d'équipe égal)`);
    });
    idx.slice().sort((a, b) => fi[a] - fi[b]).slice(0, 2).forEach((i) => {
      if (fi[i] <= 0.3) minus.push(`<b>${fLabel(FAC[i], p.role)}</b> : ${fLow(FAC[i], p.role)} (${Math.max(1, Math.round(fi[i] * 100))}e centile des ${grp}, à niveau d'équipe égal)`);
    });
    // weakside / strongside : seulement avec les chronologies (sans elles, en LPL, la mesure ne se retrouve pas d'une saison à l'autre)
    if (p.wi != null && p.si != null && p.st && p.st.tl >= 10) {
      if (p.wi >= 0.8 && p.wi >= p.si) plus.push(`<b>Weakside</b> : tient sa lane quand son jungler joue ailleurs (${topTxt(p.wi)}, à niveau d'équipe égal)`);
      if (p.si >= 0.8 && p.si > p.wi) plus.push(`<b>Strongside</b> : convertit l'aide reçue en avance et en dégâts (${topTxt(p.si)}, à niveau d'équipe égal)`);
      if (p.wi <= 0.2) minus.push('<b>Weakside</b> : souffre quand son jungler joue ailleurs');
      if (p.si <= 0.2) minus.push('<b>Strongside</b> : convertit peu l\'aide reçue');
    }
    // « grands matchs » (playoffs et international contre saison régulière) n'est plus présenté comme une force ou un point
    // faible : l'écart ne se retrouve pas d'une saison à l'autre (corrélation -0,01 et -0,08), c'est du bruit.
    if (p.reg != null && p.reg >= 0.8) plus.push('<b>Régularité</b> : niveau très stable d\'une partie à l\'autre');
    if (p.reg != null && p.reg <= 0.15) minus.push('<b>Régularité</b> : niveau très variable d\'une partie à l\'autre');
    if (p.pool != null && p.pool >= 0.85) plus.push(`<b>Pool de champions</b> : large (${p.pool_n} champions joués)`);
    if (p.pool != null && p.pool <= 0.12) minus.push(`<b>Pool de champions</b> : étroit (${p.pool_n} champions joués)`);
    return { plus, minus };
  }
  function topTxt(pc) { const t = Math.max(1, Math.round((1 - pc) * 100)); return t <= 50 ? `top ${t} %` : `${t}e centile`; }

  /* ------------------------------------------------------------ classement */
  /* Trois façons de noter, jamais mélangées :
       - par défaut, la note de toute la saison ; les filtres (niveau, région, ligue) ne font que choisir les joueurs,
         d'après leur ligue actuelle, sans rien changer à leur note ;
       - ligue choisie + « parties de la ligue seulement » : la note sur ces seules parties, pour tous ceux qui y ont joué ;
       - événement choisi : la note de l'événement, pour les joueurs retenus par les autres filtres. */
  function filtered(ignoreRole) {
    const q = state.q.trim().toLowerCase();
    const only = state.basis === 'only';
    const lgOnly = !!state.league && !state.event && only;
    // niveau de ligue choisi : on ajoute ceux qui y ont joué sans que ce soit leur niveau principal, notés sur ces seules parties
    const pass = !q && state.tier !== '' && !state.league && !state.event && state.basis === 'season';
    const trOf = (p) => { const v = pass && p.tier !== +state.tier && p.tr && p.tr[state.tier]; return v && v[1] >= state.minG && (!state.region || D.region[v[3]] === state.region) ? v : null; };
    let L = S.players.filter((p) =>
      (ignoreRole || !state.role || p.role === state.role) && (trOf(p) ? cMatch(p, state.contract) :
      (q || state.tier === '' || p.tier === +state.tier) &&
      (!state.region || p.region === state.region) &&
      (!state.league || p.league === state.league || !!p.lg[state.league]) && cMatch(p, state.contract) &&
      (q || (lgOnly ? (p.lg[state.league] || [0, 0])[1] : p.n) >= state.minG) &&
      (!q || p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q))));
    if (pass && L.some(trOf)) L = L.map((p) => { const v = trOf(p); return v ? Object.assign({ _e: { note: v[0], n: v[1], team: v[2], lg: v[3], tierOnly: true } }, p) : p; }).sort((a, b) => (b._e ? b._e.note : b.note) - (a._e ? a._e.note : a.note));
    if (state.event) {
      L = L.map((p) => ({ p, e: evNote(p, state.event) })).filter((x) => x.e);
      if (!only) return L.map((x) => x.p);                 // les participants, avec leur note de toute la saison
      return L.sort((a, b) => b.e.note - a.e.note).map((x) => Object.assign({ _e: x.e }, x.p));
    }
    if (lgOnly) {
      L = L.filter((p) => p.lg[state.league]).map((p) => { const v = p.lg[state.league]; return Object.assign({ _e: { note: v[0], n: v[1], team: v[2], w: v[3] } }, p); });
      return L.sort((a, b) => b._e.note - a._e.note);
    }
    // période récente : dernier split de ligue de chaque joueur et tout ce qu'il a joué ensuite
    if (state.basis === 'recent') return L.filter((p) => p.rc).map((p) => Object.assign({ _e: { note: p.rc[0], n: p.rc[1], recent: true } }, p)).sort((a, b) => b._e.note - a._e.note);
    return L;
  }
  /* équipe à montrer sur une ligne de la liste, et mention d'un changement d'équipe en cours de saison */
  function teamLine(p) {
    if (p._e && p._e.tierOnly) return `${h(p._e.team)}, ${h(lgName(p._e.lg))}<span class="moved">, noté sur ses seules parties de ${TIER_IN[+state.tier]} ; aussi ${h(p.team)} (${h(lgName(p.league))})</span>`;
    if (p._e && p._e.team && !p._e.recent) return h(p._e.team) + ', ' + h(state.event || lgName(state.league));
    const inLg = state.league && p.lg[state.league];
    if (inLg && p.league !== state.league) return `${h(inLg[2])}, ${h(lgName(state.league))}<span class="moved">, puis ${h(p.team)} (${h(lgName(p.league))})</span>`;
    let txt = `${h(p.team)}, ${h(lgName(p.league))}`;
    if (p.tm && p.tm.length > 1) { const i = p.tm.findIndex((t) => t[0] === p.team); if (i > 0) txt = `${txt}<span class="moved">, avant ${h(p.tm[i - 1][0])}</span>`; }   // parcours trié par date de début
    if (p.now) txt += `<span class="moved">, puis ${h(p.now)}</span>`;
    return txt;
  }
  function scopeLabel() {
    const parts = [];
    if (state.basis === 'recent') parts.push((state.event ? `joueurs de ${state.event}` : state.league ? lgName(state.league) : '') + (state.event || state.league ? ', ' : '') + 'période récente');
    else if (state.event) parts.push(state.basis === 'only' ? state.event : `joueurs de ${state.event}, sur toute la saison`);
    else if (state.league) parts.push(state.basis === 'only' ? `${lgName(state.league)}, parties de ${lgName(state.league)} seulement` : lgName(state.league));
    else if (state.region) parts.push(state.region);
    else if (state.tier !== '') parts.push(['ligues majeures', 'deuxième niveau', 'troisième niveau'][+state.tier]);
    else parts.push('toutes ligues');
    return parts.join(', ');
  }
  function renderFive() {
    const L = filtered(true);
    const el = $('#five'); let html = '';
    for (const r of ROLES) {
      const p = L.find((x) => x.role === r);
      if (!p) { html += `<button disabled><span class="role">${r}</span><span class="empty">Aucun joueur</span></button>`; continue; }
      const n = p._e ? p._e.note : p.note;
      html += `<button data-p="${p.id}"><span class="role">${r}</span><span class="name">${h(p.name)}</span><span class="num note ${noteCls(n)}">${nInt(n)}</span><span class="team">${h(p._e ? p._e.team : p.team)}</span></button>`;
    }
    el.innerHTML = html;
    $('#five-title').textContent = 'Le meilleur cinq, ' + scopeLabel();
    $('#five-sub').textContent = `Saison ${state.season} : ${fmt(S.games)} parties, du ${frDate(S.from)} au ${frDate(S.to)}. Chaque joueur est noté de 1 à 100 sur la même échelle, quelle que soit sa ligue.`;
  }
  function frDate(d) { return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }); }
  function renderRank() {
    renderFive();
    const L = filtered(false);
    const el = $('#rows');
    const who = state.event ? ` ayant joué ${state.event}` : state.league ? ` ayant joué en ${lgName(state.league)} cette saison` : '';
    const on = state.basis === 'recent' ? 'leur dernier split et ce qui a suivi' : state.basis === 'only' && state.event ? state.event : state.basis === 'only' && state.league ? 'leurs seules parties de ' + lgName(state.league) : 'toute la saison';
    const nPass = L.filter((p) => p._e && p._e.tierOnly).length;
    $('#count').textContent = L.length ? `${fmt(L.length)} joueur${L.length > 1 ? 's' : ''}${who}, notés sur ${on}` + (nPass ? `, dont ${nPass} de passage, noté${nPass > 1 ? 's' : ''} sur ${nPass > 1 ? 'leurs' : 'ses'} seules parties de ce niveau` : '') : '';
    if (!L.length) { el.innerHTML = '<p class="none">Aucun joueur ne correspond à ces filtres. Élargissez le niveau de ligue ou baissez le nombre minimum de parties.</p>'; return; }
    let html = '';
    L.slice(0, state.shown).forEach((p, i) => {
      const n = p._e ? p._e.note : p.note;
      // tendance : période récente (dernier split et la suite) par rapport à la saison. La forme sur 15 parties n'est plus
      // affichée ici : elle prédit la suite moins bien que la note de saison (log-loss +0,037 sur août-novembre 2026).
      const d = p._e ? p._e.note - p.note : p.rc ? p.rc[0] - p.note : 0;
      const tc = d >= 1.5 ? 'up' : d <= -1.5 ? 'down' : 'flat';
      html += `<button class="row" data-p="${p.id}"><span class="rank">${i + 1}</span><span class="num note ${noteCls(n)}">${nInt(n)}</span>
        <span class="who"><b>${h(p.name)}</b><small>${teamLine(p)}${ageTxt(p)} ${cShort(p)}</small></span>
        <span class="pos">${p.role}</span>${strip(p)}
        <span class="trend ${tc} r trend-cell" title="${p._e ? 'Écart avec sa note sur toute la saison' : 'Période récente (dernier split et ce qui a suivi) par rapport à la saison'}">${!p._e && !p.rc ? '–' : (d > 0 ? '+' : '') + fmt(d, 1)}</span>
        <span class="r games">${p._e ? p._e.n : p.n}</span></button>`;
    });
    if (L.length > state.shown) html += `<button class="more" id="more">Afficher 100 joueurs de plus</button>`;
    el.innerHTML = html;
    $('#f-contract').disabled = !hasCT(); $('#f-contract').value = hasCT() ? state.contract : '';
    $('#th-trend').textContent = state.basis === 'recent' || ((state.event || state.league) && state.basis === 'only') ? 'Écart saison' : 'Récent';
    const box = $('#lg-mode'), only = $('#lg-mode-only');
    only.hidden = !state.league && !state.event;
    if (!only.hidden) only.textContent = (state.event || lgName(state.league)) + ' seulement';
    box.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.lgmode === state.basis));
  }
  function fillSelects() {
    const leagues = {}, regions = new Set(), events = {};
    for (const p of S.players) {
      leagues[p.league] = p.tier; regions.add(p.region);
      for (const e of p.ev) events[e.e] = (events[e.e] || { n: 0, sc: e.sc, d: e.d }), events[e.e].n++, events[e.e].d = e.d > events[e.e].d ? e.d : events[e.e].d;
    }
    const lgOpts = (sel) => '<option value="">Toutes</option>' + [0, 1, 2].map((t) => `<optgroup label="${TIERS[t]}">` +
      Object.keys(leagues).filter((l) => leagues[l] === t).sort((a, b) => (S.leagues[b] || 0) - (S.leagues[a] || 0))
        .map((l) => `<option value="${h(l)}"${l === sel ? ' selected' : ''}>${h(lgName(l))}${D.desc[l] && lgName(l) === l ? ' (' + h(D.desc[l]) + ')' : ''}</option>`).join('') + '</optgroup>').join('');
    const rgOpts = (sel) => '<option value="">Toutes</option>' + [...regions].sort().map((r) => `<option${r === sel ? ' selected' : ''}>${h(r)}</option>`).join('');
    $('#f-league').innerHTML = lgOpts(state.league); $('#f-region').innerHTML = rgOpts(state.region);
    $('#p-league').innerHTML = lgOpts(state.pw.league); $('#p-region').innerHTML = rgOpts(state.pw.region);
    $('#s-league').innerHTML = lgOpts(state.sc.league); $('#s-region').innerHTML = rgOpts(state.sc.region);
    const rs = {}; for (const p of S.players) if (p.res) rs[p.res] = (rs[p.res] || 0) + 1;
    $('#s-res').innerHTML = '<option value="">Toutes</option>' + Object.keys(rs).sort((a, b) => rs[b] - rs[a]).map((r) => `<option value="${h(r)}"${r === state.sc.res ? ' selected' : ''}>${h(resid(r))}</option>`).join('');
    const evs = Object.keys(events).filter((e) => events[e].n >= 20);
    const grp = (sc) => evs.filter((e) => events[e].sc === sc).sort((a, b) => (sc === 'monde' ? events[b].n - events[a].n : sc === 'ligue' ? (a.split(',')[0].split(' ')[0].localeCompare(b.split(',')[0].split(' ')[0]) || events[a].d.localeCompare(events[b].d)) : a.localeCompare(b)));
    const og = (label, sc) => { const L = grp(sc); return L.length ? `<optgroup label="${label}">` + L.map((e) => `<option${e === state.event ? ' selected' : ''}>${h(e)}</option>`).join('') + '</optgroup>' : ''; };
    $('#f-event').innerHTML = '<option value="">Saison entière</option>' + og('Tournois internationaux', 'monde') + og('Tournois entre ligues d\'une même région', 'region') + og('Coupes et qualifications régionales', 'coupe') + og('Ligues, par segment', 'ligue');
    if (state.event && !events[state.event]) state.event = '';
  }

  /* ------------------------------------------------------------ fiche joueur */
  function rail(label, v, pc, ref, cmp) {
    if (v == null) return '';
    const x = (n) => Math.max(0, Math.min(100, (n - 30) / 69 * 100));
    return `<div class="rail"><span>${label}</span><span class="bar"><i style="width:${x(v)}%;background:${noteVar(v)}"></i>${ref != null ? `<u style="left:${x(ref)}%"></u>` : ''}${cmp != null ? `<s style="left:${x(cmp)}%"></s>` : ''}</span><b class="${noteCls(v)}">${nInt(v)}</b><small>${pc != null ? topTxt(pc) : ''}</small></div>`;
  }
  function openSheet(id, cmpId) {
    const p = byId.get(id); if (!p) return;
    const cmp = cmpId && cmpId !== id ? byId.get(cmpId) : null;
    const m = med[p.role + p.tier]; const ins = insights(p); const arch = archetype(p);
    const grp = ROLE_PL[p.role] + ' ' + TIER_OF[p.tier];
    const rankIn = S.players.filter((x) => x.role === p.role && x.tier === p.tier && x.n >= 15 && x.note > p.note).length + 1;
    const d = p.rc ? p.rc[0] - p.note : 0;
    let html = `<header><span class="num note ${noteCls(p.note)}">${nInt(p.note)}</span><div><h2 id="sheet-name">${h(p.name)}</h2>
      <p class="meta">${p.role}, ${h(p.team)}, ${h(lgName(p.league))} (${h(p.region)})<br>${(p.age || p.cty) ? [p.age ? p.age + ' ans' : null, p.cty ? h(pays(p.cty)) : null, p.res ? 'résidence ' + h(resid(p.res)) : null].filter(Boolean).join(', ') + '<br>' : ''}${rankIn}<sup>${rankIn === 1 ? 'er' : 'e'}</sup> des ${grp}, saison ${state.season}${(p.nm != null || p.nu != null) ? '<br>' + ['Note Rift Scout ' + nInt(p.note0), p.nm != null ? 'note mixte ' + nInt(p.nm) : null, p.nu != null ? 'note unifiée ' + nInt(p.nu) + (p.nue != null ? ' (± ' + nInt(p.nue) + ')' : '') : null].filter(Boolean).join(', ') : ''}${p.now ? `<br>A ensuite joué pour ${h(p.now)} (tournoi ou intersaison)` : ''}${hasCT() ? '<br>' + (p.c ? (isFree(p) ? `<b class="down">Fin de contrat le ${cDate(p.c, true)}</b>` : `Sous contrat jusqu'au ${cDate(p.c, true)}`) : 'Contrat non renseigné dans la base de Riot') : ''}</p></div><div class="hbtns"><button class="close" data-card>Télécharger l'image</button><button class="close" data-close>Fermer</button></div></header>`;
    html += `<section><div class="split">
      <div><small>Niveau de son équipe${p.tse ? ', à ± ' + fmt(p.tse, 1) + ' près' : ''}</small><span class="num">${nInt(p.team_lvl)}</span></div>
      <div><small>Écart individuel</small><span class="num ${p.ind >= 0 ? 'up' : 'down'}">${p.ind >= 0 ? '+' : ''}${fmt(p.note - p.team_lvl, 1)}</span></div>
      <div><small>Période récente${p.rc ? ', ' + p.rc[1] + ' parties' : ''}</small><span class="num ${d >= 1.5 ? 'up' : d <= -1.5 ? 'down' : ''}">${p.rc ? nInt(p.rc[0]) : '–'}</span></div>
      <div><small>Parties jouées, ${pctTxt(p.st.win)} de victoires</small><span class="num">${p.n}</span></div></div>
      <p class="legend" style="margin-top:10px">${p.rc ? `Période récente : ${h(p.rc[3])} et ce qui a suivi, depuis le ${frDate(p.rc[2])}. ` : ''}Sur ses 15 dernières parties : ${nInt(p.form)} (indicatif : sur 15 parties, la note varie beaucoup et prédit la suite moins bien que la note de saison).</p>
      ${p.tr && Object.keys(p.tr).length > 1 ? `<p class="legend" style="margin-top:10px">Par niveau de ligue : ${Object.keys(p.tr).sort().map((k) => `${TIER_IN[k]} <b class="${noteCls(p.tr[k][0])}">${nInt(p.tr[k][0])}</b> (${p.tr[k][1]} parties, ${h(p.tr[k][2])})`).join(' ; ')}</p>` : ''}
      <div class="tags">${arch ? `<span class="tag gold">${arch}</span>` : ''}${styleTags(p).map((t) => `<span class="tag">${t}</span>`).join('')}</div></section>`;
    if (ins.plus.length || ins.minus.length) html += `<section><div class="two"><div><h3>Forces</h3>${ins.plus.length ? `<ul class="say">${ins.plus.map((x) => `<li>${x}</li>`).join('')}</ul>` : '<p class="legend">Rien qui ressorte nettement par rapport à son poste.</p>'}</div>
      <div><h3>Points faibles</h3>${ins.minus.length ? `<ul class="say minus">${ins.minus.map((x) => `<li>${x}</li>`).join('')}</ul>` : '<p class="legend">Aucun point faible marqué par rapport à son poste.</p>'}</div></div></section>`;
    html += `<section><h3>Profil par facette</h3>` + FAC.map((f, i) => rail(fLabel(f, p.role), p.f[i], p.fp[i], m.f[i], cmp && cmp.role === p.role ? cmp.f[i] : null)).join('') +
      (p.weak != null ? rail('Weakside', p.weak, p.weak_pc, null, cmp ? cmp.weak : null) : '') + (p.strong != null ? rail('Strongside', p.strong, p.strong_pc, null, cmp ? cmp.strong : null) : '') +
      `<p class="legend">Trait noir : médiane des ${grp}. ${cmp && cmp.role === p.role ? `Cadre rouge : ${h(cmp.name)} (${nInt(cmp.note)}). ` : ''}Le classement à droite compare aux ${grp}.</p></section>`;
    if (p.tm) html += `<section><h3>Parcours cette saison</h3><div class="events">` + p.tm.map((t) =>
      `<div class="ev"><span>${h(t[0])}${t[1] ? ` <small style="text-align:left">${h(t[1].split(', ').map(lgName).join(', et quelques parties de '))}</small>` : ' <small style="text-align:left">tournois seulement</small>'}</span><span class="rail" style="display:block;padding:0"><span class="bar" style="display:block"><i style="width:${Math.max(0, (t[3] - 30) / 69 * 100)}%;background:${noteVar(t[3])}"></i><u style="left:${(p.note - 30) / 69 * 100}%"></u></span></span><b class="num ${noteCls(t[3])}" style="font-size:22px;text-align:right">${nInt(t[3])}</b><small>${t[2]} parties, ${frDate(t[4])} au ${frDate(t[5])}</small></div>`).join('') +
      `</div><p class="legend">Note du joueur avec chaque équipe, toutes compétitions confondues. Trait noir : sa note sur la saison.</p></section>`;
    if (p.ev.length) html += `<section><h3>Note par événement</h3><div class="events">` + p.ev.map((e) =>
      `<div class="ev"><span>${h(e.e)}</span><span class="rail" style="display:block;padding:0"><span class="bar" style="display:block"><i style="width:${Math.max(0, (e.note - 30) / 69 * 100)}%;background:${noteVar(e.note)}"></i><u style="left:${(p.note - 30) / 69 * 100}%"></u></span></span><b class="num ${noteCls(e.note)}" style="font-size:22px;text-align:right">${nInt(e.note)}</b><small>${e.n} parties, ${pctTxt(e.w)} vict.</small></div>`).join('') +
      `</div><p class="legend">Trait noir : sa note sur la saison. Avec peu de parties, la note d'un événement reste incertaine.</p></section>`;
    const st = p.st;
    html += `<section><h3>Statistiques moyennes</h3><div class="stats">
      <div><small>KDA</small><b>${fmt(st.kda, 2)}</b></div><div><small>Participation aux kills</small><b>${pctTxt(st.kp)}</b></div>
      <div><small>Dégâts par minute</small><b>${fmt(st.dpm)}</b></div><div><small>Part des dégâts</small><b>${pctTxt(st.dsh)}</b></div>
      <div><small>Écart d'or à 15 min</small><b>${st.gd15 > 0 ? '+' : ''}${fmt(st.gd15)}</b></div><div><small>Écart de sbires à 15 min</small><b>${st.cd15 > 0 ? '+' : ''}${fmt(st.cd15, 1)}</b></div>
      <div><small>Écart d'XP à 15 min</small><b>${st.xd15 > 0 ? '+' : ''}${fmt(st.xd15)}</b></div><div><small>Part de l'or</small><b>${pctTxt(st.gsh)}</b></div>
      <div><small>Sbires par minute</small><b>${fmt(st.cspm, 1)}</b></div><div><small>Vision par minute</small><b>${fmt(st.vspm, 2)}</b></div>
      <div><small>Morts par partie</small><b>${fmt(st.dpg, 1)}</b></div><div><small>Premier sang (kill ou assist)</small><b>${pctTxt(st.fb)}</b></div>
      ${st.wd != null ? `<div><small>Morts inutiles</small><b>${pctTxt(st.wd)}</b></div>` : ''}${st.objp != null ? `<div><small>Présence sur les objectifs</small><b>${pctTxt(st.objp)}</b></div>` : ''}${st.jgp != null && p.role !== 'Jungle' ? `<div><small>Temps près de son jungler</small><b>${pctTxt(st.jgp)}</b></div>` : ''}</div>
      ${p.off ? `<p class="legend">Dont ${p.off} partie${p.off > 1 ? 's' : ''} jouée${p.off > 1 ? 's' : ''} à un autre poste : ${p.off > 1 ? 'elles comptent' : 'elle compte'} dans la note, comparée${p.off > 1 ? 's' : ''} aux joueurs de ce poste. Les statistiques ci-dessus ne portent que sur son poste principal.</p>` : ''}
      ${st.wd == null ? '<p class="legend">Morts inutiles, présence sur les objectifs et proximité du jungler ne sont pas disponibles pour ce joueur (parties de LPL, ou saison sans chronologie).</p>' : ''}</section>`;
    if (p.ch.length) html += `<section><h3>Champions les plus joués</h3><div class="champs">${p.ch.map((c) => `<span>${h(c[0])} <small>${c[1]} parties, ${pctTxt(c[2])}</small></span>`).join('')}</div></section>`;
    if (p.s) {
      const sims = S.players.filter((x) => x.role === p.role && x.id !== p.id && x.s && x.n >= 15 && x.note >= p.note - 20).map((x) => [similarity(p, x), x]).sort((a, b) => b[0] - a[0]).slice(0, 6);
      html += `<section><h3>Joueurs au style le plus proche</h3><div class="simlist">${sims.map(([s, x]) => `<button data-p="${x.id}"><span class="num ${noteCls(x.note)}">${nInt(x.note)}</span><span>${h(x.name)} <small>${h(x.team)}, ${h(lgName(x.league))}</small></span><small>${fmt(s)} % de similarité</small></button>`).join('')}</div>
        <p style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">${tryBtn(p)}<button class="cta" data-scout="${p.id}">Chercher un remplaçant à ${h(p.name)}</button></p></section>`;
    }
    showSheet(html, { kind: 'player', p, rankIn, grp, m, season: state.season, file: cardFile(p.name, state.season) });
  }
  let card = null;   // données de la carte image de la fiche ouverte (voir « carte image »)
  function showSheet(html, c) {
    card = c || null;
    $('#sheet').innerHTML = html; $('#sheet').scrollTop = 0;
    $('#sheet-wrap').classList.add('open'); $('#sheet').focus();
  }
  function tryBtn(p) {
    const t = state.view === 'scout' && state.sc.tid ? team(state.sc.tid) : null;
    if (!t || p.tid === t.tid) return '';
    return `<button class="cta" data-try="${p.id}" data-close>${state.sc.plan[p.role] === p.id ? 'Retirer de' : 'Essayer dans'} ${h(t.name)}</button>`;
  }
  function styleTags(p) {
    if (!p.s) return [];
    const T = [[0, 'Beaucoup de ressources', 'Peu de ressources'], [3, 'Actif avant 15 min', 'Discret avant 15 min'], [5, 'Prend des risques', 'Joue la sécurité'],
      [7, 'Investit dans la vision', null], [8, 'Gros farmeur', null], [6, 'Encaisse pour l\'équipe', null]];
    const out = [];
    for (const [i, hi, lo] of T) { if (p.s[i] >= 1 && hi) out.push(hi); else if (p.s[i] <= -1 && lo) out.push(lo); }
    // mesures tirées des chronologies (indices 11 à 15 du vecteur de style) : absentes pour la LPL, où elles valent 0
    if (p.s.length > 15) {
      if (p.role === 'Jungle') { const k = [13, 14, 15].reduce((a, i) => (p.s[i] > p.s[a] ? i : a), 13); if (p.s[k] >= 0.8) out.unshift('Joue autour du ' + { 13: 'top', 14: 'mid', 15: 'bot' }[k]); }
      else if (p.role === 'Support') { if (p.s[12] >= 1) out.unshift('Quitte souvent son ADC'); else if (p.s[12] <= -1) out.unshift('Reste avec son ADC'); }
      else if (p.s[11] >= 1) out.unshift('Souvent accompagné de son jungler'); else if (p.s[11] <= -1) out.unshift('Joue seul sur sa lane');
    }
    return out.slice(0, 4);
  }
  /* Transferts : les joueurs sont ceux de la dernière saison. Si une saison plus ancienne est choisie, la fiche s'ouvre sur la dernière,
     puis la saison choisie est rétablie à la fermeture. */
  let savedSeason = null;
  function openLast(id) {
    if (state.season !== LAST) { if (!savedSeason) savedSeason = state.season; state.season = LAST; load(); }
    openSheet(id);
  }
  function closeSheet() {
    $('#sheet-wrap').classList.remove('open');
    if (savedSeason) { state.season = savedSeason; savedSeason = null; load(); }
  }

  /* ------------------------------------------------------------ scouting */
  function team(tid) { return S.teams.find((t) => t.tid === tid); }
  function setTeam(tid) { state.sc.tid = tid; state.sc.ref = null; state.sc.plan = {}; const t = team(tid); if (t && !t.roster[state.sc.role]) state.sc.role = ROLES.find((r) => t.roster[r]) || 'Mid'; state.sc.shown = 60; renderScout(); }
  /* effectif simulé : l'effectif réel, avec les joueurs essayés à la place des titulaires */
  function lineupOf(t, plan) { const o = {}; ROLES.forEach((r) => { const id = (plan && plan[r]) || t.roster[r]; if (id && byId.get(id)) o[r] = id; }); return o; }
  function toNote(pts) { let x = D.scale.a + D.scale.b * pts; if (x > 88) x = 88 + 11 * Math.tanh((x - 88) / 11); return Math.max(1, Math.min(99, x)); }
  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : null);
  function squad(ros) {
    const P = ROLES.map((r) => byId.get(ros[r])).filter(Boolean);
    if (P.length < 3) return null;
    return { P, pts: mean(P.map((p) => p.pts)), fac: FAC.map((_, i) => mean(P.map((p) => p.f[i]).filter((v) => v != null))),
      gold: P.reduce((a, p) => a + (p.s ? p.s[0] : 0), 0), early: mean(P.map((p) => (p.s ? p.s[3] : 0))), risk: mean(P.map((p) => (p.s ? p.s[5] : 0))), vision: mean(P.map((p) => (p.s ? p.s[7] : 0))) };
  }
  let lgCache = {};
  function leagueRef(lg) {
    if (lgCache[lg]) return lgCache[lg];
    const T = S.teams.filter((t) => t.league === lg).map((t) => ({ t, q: squad(lineupOf(t)) })).filter((x) => x.q);
    return (lgCache[lg] = { T, pts: mean(T.map((x) => x.q.pts)), fac: FAC.map((_, i) => median(T.map((x) => x.q.fac[i]).filter((v) => v != null))) });
  }
  const ord = (n) => (n === 1 ? '1<sup>er</sup>' : n + '<sup>e</sup>');
  function renderCompare(t) {
    const el = $('#compare'); if (!t) { el.hidden = true; el.innerHTML = ''; return; }
    const plan = state.sc.plan, changes = ROLES.filter((r) => plan[r] && plan[r] !== t.roster[r]);
    const A = squad(lineupOf(t)), B = changes.length ? squad(lineupOf(t, plan)) : null, ref = leagueRef(t.league);
    if (!A) { el.hidden = true; return; }
    el.hidden = false;
    const win = (q) => 1 / (1 + Math.exp(-(q.pts - ref.pts) / 200));
    const rank = (q) => ref.T.filter((x) => x.t.tid !== t.tid && x.q.pts > q.pts).length + 1;
    const arrow = (a, b, f) => (b == null ? `<b class="num">${f(a)}</b>` : `<span class="was">${f(a)}</span><b class="num">${f(b)}</b>`);
    const dl = (d, unit) => (d == null ? '' : `<em class="${d > 0.05 ? 'up' : d < -0.05 ? 'down' : 'flat'}">${d > 0 ? '+' : ''}${fmt(d, 1)}${unit}</em>`);
    const nA = toNote(A.pts), nB = B ? toNote(B.pts) : null;
    let html = `<div class="cmp-kpis">
      <div><small>Niveau de l'effectif</small><p>${arrow(nA, nB, (v) => fmt(v, 1))} ${dl(B ? nB - nA : null, '')}</p></div>
      <div><small>Victoire contre une équipe moyenne de ${h(lgName(t.league))}</small><p>${arrow(win(A), B ? win(B) : null, (v) => fmt(v * 100) + ' %')} ${dl(B ? (win(B) - win(A)) * 100 : null, ' pts')}</p></div>
      <div><small>Rang estimé en ${h(lgName(t.league))}, sur ${ref.T.length} équipes</small><p>${arrow(rank(A), B ? rank(B) : null, ord)}</p></div></div>`;
    // profil par facette : une ligne par facette, même axe pour toutes
    const vals = [].concat(A.fac, B ? B.fac : [], ref.fac).filter((v) => v != null);
    const lo = Math.floor(Math.min.apply(null, vals) - 2), hi = Math.ceil(Math.max.apply(null, vals) + 2), x = (v) => (v - lo) / (hi - lo) * 100;
    html += `<div class="cmp-body"><div><h3>Profil de l'équipe${B ? ', avant et après' : ''}</h3>
      <p class="cmp-legend">${B ? '<span><i class="dot hollow"></i>Avant</span><span><i class="dot"></i>Après</span>' : '<span><i class="dot"></i>Effectif actuel</span>'}<span><i class="tick"></i>Équipe médiane de ${h(lgName(t.league))}</span></p>` +
      FAC.map((f, i) => {
        const a = A.fac[i], b = B ? B.fac[i] : null, m = ref.fac[i]; if (a == null) return '';
        const d = b != null ? b - a : null;
        return `<div class="cmp-row"><span>${FLABEL[f]}</span><span class="track">${m != null ? `<u style="left:${x(m)}%" title="Équipe médiane : ${fmt(m, 1)}"></u>` : ''}` +
          (b != null ? `<i class="link ${d >= 0 ? 'gain' : 'loss'}" style="left:${x(Math.min(a, b))}%;width:${Math.abs(x(b) - x(a))}%"></i><i class="dot hollow" style="left:${x(a)}%" title="Avant : ${fmt(a, 1)}"></i><i class="dot" style="left:${x(b)}%" title="Après : ${fmt(b, 1)}"></i>`
            : `<i class="dot" style="left:${x(a)}%" title="${FLABEL[f]} : ${fmt(a, 1)}"></i>`) +
          `</span><b>${fmt(b != null ? b : a, 1)}</b>${b != null ? dl(d, '') : '<em></em>'}</div>`;
      }).join('') + `<div class="cmp-row axis"><span></span><span class="track"><small>${lo}</small><small>${hi}</small></span><b></b><em></em></div></div><div>`;
    if (!B) html += `<h3>Simuler un changement</h3><p class="legend" style="margin:0">Cliquez sur « Essayer » à côté d'un candidat pour le placer dans l'équipe. Le niveau de l'effectif, ses chances de victoire et son profil sont recalculés avec lui. Vous pouvez changer plusieurs postes.</p>`;
    else {
      html += '<h3>Changements essayés</h3><div class="swaps">' + changes.map((r) => {
        const o = byId.get(t.roster[r]), n = byId.get(plan[r]);
        return `<div class="swap"><span class="role">${r}</span><span>${o ? `${h(o.name)} <b>${nInt(o.note)}</b>` : 'Poste vacant'}, remplacé par <b>${h(n.name)} ${nInt(n.note)}</b>${o ? ' ' + dl(n.note - o.note, '') : ''}<small>${h(n.team)}, ${h(lgName(n.league))}${ageTxt(n)}${hasCT() ? (n.c ? (isFree(n) ? `, en fin de contrat (${cDate(n.c)})` : `, sous contrat jusqu'en ${cDate(n.c)} : transfert à négocier`) : ', contrat non renseigné') : ''}</small></span><button class="reset" data-untry="${r}">Retirer</button></div>`;
      }).join('') + `</div>${changes.length > 1 ? '<button class="reset" data-untry="all">Annuler tous les changements</button>' : ''}`;
      const say = [];
      const word = (d, more, less) => (d >= 0.15 ? more : d <= -0.15 ? less : null);
      [[B.early - A.early, 'Plus d\'activité avant 15 minutes.', 'Moins d\'activité avant 15 minutes.'], [B.risk - A.risk, 'Un effectif qui prend plus de risques (plus de morts).', 'Un effectif plus prudent (moins de morts).'],
        [B.vision - A.vision, 'Plus d\'investissement dans la vision.', 'Moins d\'investissement dans la vision.']].forEach(([d, a, b]) => { const w = word(d, a, b); if (w) say.push(w); });
      const hungry = (q) => q.P.filter((p) => p.s && p.s[0] >= 0.7).length;
      if (hungry(B) >= 3 && hungry(B) > hungry(A)) say.push(`${hungry(B)} joueurs demandent beaucoup d'or : il faudra choisir qui est servi.`);
      else if (B.gold - A.gold <= -1) say.push('Moins de joueurs gourmands en or : plus de ressources pour les carrys en place.');
      const best = FAC.map((f, i) => [B.fac[i] - A.fac[i], f]).filter((v) => FAC.indexOf(v[1]) >= 0 && !isNaN(v[0])).sort((a, b) => b[0] - a[0]);
      if (best.length && best[0][0] >= 0.5) say.unshift(`Gain le plus net : ${FLABEL[best[0][1]].toLowerCase()} (${dl(best[0][0], '').replace(/<[^>]+>/g, '')}).`);
      const worst = best[best.length - 1]; if (worst && worst[0] <= -0.5) say.push(`Recul le plus net : ${FLABEL[worst[1]].toLowerCase()} (${fmt(worst[0], 1)}).`);
      if (say.length) html += `<h3 style="margin-top:16px">Ce que ça change</h3><ul class="say plain">${say.map((x) => `<li>${x}</li>`).join('')}</ul>`;
      html += '<p class="legend">Estimation à partir des notes de la saison : l\'entente entre joueurs, la langue et l\'adaptation à une nouvelle ligue ne sont pas mesurées.</p>';
    }
    el.innerHTML = html + '</div></div>';
  }
  function teamNeeds(ros, role) {
    const others = ROLES.filter((r) => r !== role).map((r) => byId.get(ros[r])).filter(Boolean);
    if (!others.length) return null;
    const avgNote = others.reduce((a, p) => a + p.note, 0) / others.length;
    const fac = FAC.map((f, i) => { const v = others.map((p) => p.f[i]).filter((x) => x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : avgNote; });
    const gap = fac.map((v, i) => (FAC[i] === 'obj' ? 0 : Math.max(0, avgNote - v)));
    const gold = others.reduce((a, p) => a + (p.s ? p.s[0] : 0), 0);
    return { others, avgNote, fac, gap, gold };
  }
  function complement(c, needs, role) {
    if (!needs || !c.s) return null;
    const w = D.weights[role];
    let num = 0, den = 0;
    FAC.forEach((f, i) => { if (c.f[i] == null) return; const k = needs.gap[i] + 0.5 * (w[f] > 0 ? 1 : 0); num += k * (c.f[i] - c.note); den += k; });
    const gain = den ? num / den : 0;                       // forces relatives du candidat là où l'équipe est en retrait
    const res = Math.exp(-Math.pow(c.s[0] + needs.gold, 2) / (2 * 1.6 * 1.6)); // équilibre des ressources (or)
    return 100 * (0.5 * res + 0.5 / (1 + Math.exp(-gain / 1.8)));
  }
  function renderScout() {
    const sc = state.sc; const t = sc.tid ? team(sc.tid) : null;
    $('#scout-mode').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.scmode === sc.mode));
    $('#scout-team').hidden = sc.mode !== 'team'; $('#scout-cracks').hidden = sc.mode !== 'cracks';
    if (sc.mode === 'cracks') return renderCracks();
    const lineup = $('#lineup'), brief = $('#brief'), rows = $('#scout-rows');
    $('#s-roles').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.role === sc.role));
    let inc = null, needs = null;
    if (t) {
      $('#team-input').value = t.name;
      const eff = lineupOf(t, sc.plan);
      lineup.innerHTML = ROLES.map((r) => {
        const p = byId.get(eff[r]), o = byId.get(t.roster[r]), sw = p && eff[r] !== t.roster[r];
        return `<button data-role="${r}" aria-pressed="${r === sc.role}" class="${sw ? 'swapped' : ''}"><span class="role">${r}${sw ? ', essai' : ''}</span><span class="name">${p ? h(p.name) : 'Poste vacant'}</span><span class="num ${p ? noteCls(p.note) : 't-low'}">${p ? nInt(p.note) : '–'}</span><small>${sw ? (o ? 'à la place de ' + h(o.name) : 'poste vacant jusqu\'ici') : p ? archetype(p) || '' : 'aucun titulaire récent'}</small></button>`;
      }).join('');
      lineup.hidden = false;
      inc = byId.get(t.roster[sc.role]) || null; needs = teamNeeds(eff, sc.role);
    } else { lineup.hidden = true; lineup.innerHTML = ''; }
    if (sc.ref) inc = byId.get(sc.ref) || inc;
    renderCompare(t);
    // texte de cadrage
    let txt = '';
    if (t && needs) {
      const weakest = needs.gap.map((g, i) => [g, i]).filter((x) => x[0] >= 1.5).sort((a, b) => b[0] - a[0]).slice(0, 2).map((x) => FLABEL[FAC[x[1]]].toLowerCase());
      const res = needs.gold >= 1 ? 'Les quatre autres joueurs consomment beaucoup d\'or : un profil peu gourmand s\'intègre mieux.' : needs.gold <= -1 ? 'Les quatre autres joueurs consomment peu d\'or : il y a de la place pour un carry.' : 'Les ressources sont réparties de façon classique entre les quatre autres joueurs.';
      txt = `<b>${h(t.name)}</b> (${h(lgName(t.league))}, niveau ${nInt(t.lvl)}${t.se ? ' ± ' + fmt(t.se, 1) : ''}) cherche un <b>${sc.role}</b>${inc ? `, à la place de ${h(inc.name)} (${nInt(inc.note)}, ${(archetype(inc) || '').toLowerCase()})` : ''}. ` +
        (weakest.length ? `Le reste de l'équipe est en retrait sur : <b>${weakest.join('</b> et <b>')}</b>. ` : 'Le reste de l\'équipe n\'a pas de facette nettement en retrait. ') + res;
    } else if (inc) txt = `Joueurs au poste de <b>${sc.role}</b> comparés à <b>${h(inc.name)}</b> (${nInt(inc.note)}, ${(archetype(inc) || '').toLowerCase()}).`;
    else txt = `Choisissez une équipe pour chercher un renfort adapté à son effectif, ou parcourez directement les meilleurs <b>${ROLE_PL[sc.role]}</b>.`;
    brief.innerHTML = txt;
    // candidats
    // niveau de ligue choisi : un joueur qui y a joué sans que ce soit son niveau principal est proposé avec sa note sur ces seules parties
    const stint = (p) => { if (sc.tier === '' || sc.league || p.tier === +sc.tier) return p; const v = p.tr && p.tr[sc.tier]; return v ? Object.assign({}, p, { note: v[0], n: v[1], team: v[2], league: v[3], region: D.region[v[3]] || p.region, tier: +sc.tier, _tr: true }) : p; };
    let C = S.players.map(stint).filter((p) => p.role === sc.role && p.n >= sc.minG && p.note >= sc.minNote && (!t || p.tid !== t.tid) && (!inc || p.id !== inc.id) && (!t || !sc.reach || p.team_lvl <= t.lvl + 1) && cMatch(p, sc.contract) &&
      (!sc.maxAge || !hasAge() || (p.age && p.age <= sc.maxAge)) && (!hasMeta() || !sc.res || p.res === sc.res) &&
      (sc.tier === '' || p.tier === +sc.tier) && (!sc.region || p.region === sc.region) && (!sc.league || p.league === sc.league));
    C = C.map((p) => {
      const sim = inc ? similarity(p, inc) : null, comp = complement(p, needs, sc.role);
      const score = p.note + (comp != null ? (comp - 50) / 10 : 0) + (sim != null ? (sim - 40) / 25 : 0);
      return { p, sim, comp, score, delta: inc ? p.note - inc.note : null };
    });
    const key = { end: (x) => (x.p.c ? -Date.parse(x.p.c) / 864e5 : -1e9) + x.p.note / 1000, score: (x) => x.score, note: (x) => x.p.note, sim: (x) => x.sim || 0, comp: (x) => x.comp || 0 }[sc.sort];
    C.sort((a, b) => key(b) - key(a));
    if (!hasCT() && sc.sort === 'end') sc.sort = 'score';
    $('#s-contract').value = hasCT() ? sc.contract : ''; $('#s-contract').disabled = !hasCT(); $('#s-sort').querySelector('[value=end]').disabled = !hasCT();
    $('#s-age').disabled = !hasAge(); $('#s-res').disabled = !hasMeta(); $('#s-age').value = sc.maxAge || ''; $('#s-res').value = hasMeta() ? sc.res : '';
    $('#s-sort').value = sc.sort; $('#s-reach').checked = sc.reach; $('#s-reach').disabled = !t;
    $('#scout-count').textContent = `${fmt(C.length)} candidat${C.length > 1 ? 's' : ''}`;
    if (!C.length) { rows.innerHTML = '<p class="none">Aucun candidat avec ces critères. Baissez la note minimale ou élargissez les ligues.</p>'; return; }
    rows.innerHTML = C.slice(0, sc.shown).map((x, i) => {
      const p = x.p, ins = insights(p).plus.slice(0, 2).map((s) => s.replace(/<b>(.*?)<\/b>.*/, '$1'));
      const dl = x.delta == null ? '' : `<span class="trend ${x.delta >= 1 ? 'up' : x.delta <= -1 ? 'down' : 'flat'}">${x.delta > 0 ? '+' : ''}${fmt(x.delta, 1)}</span>`;
      const meter = (v) => v == null ? '<span class="meter"><span></span><b>–</b></span>' : `<span class="meter"><span class="bar"><i style="width:${v}%"></i></span><b>${fmt(v)}</b></span>`;
      const tried = t && sc.plan[sc.role] === p.id;
      return `<div class="row" role="button" tabindex="0" data-p="${p.id}" data-cmp="${inc ? inc.id : ''}"><span class="rank">${i + 1}</span><span class="num note ${noteCls(p.note)}">${nInt(p.note)}</span>
        <span class="who"><b>${h(p.name)}</b><small>${h(p.team)}, ${h(lgName(p.league))}${p._tr ? `<span class="moved">, noté sur ses seules parties de ${TIER_IN[p.tier]}</span>` : ''}${ageTxt(p)} ${cShort(p)}</small></span><span class="pos r">${dl}</span>
        <span class="m-sim">${meter(x.sim)}</span><span class="m-sim">${meter(x.comp)}</span><span class="pos games"><small>${archetype(p) || ''}${ins.length ? '<br>' + ins.join(', ') : ''}</small></span>
        ${t ? `<button class="try" data-try="${p.id}" aria-pressed="${tried}">${tried ? 'Retirer' : 'Essayer'}</button>` : '<span></span>'}</div>`;
    }).join('') + (C.length > sc.shown ? '<button class="more" id="scout-more">Afficher 60 candidats de plus</button>' : '');
  }
  /* cracks : jeunes joueurs des ligues inférieures, notés sur leurs seules parties de ce niveau, comparés aux titulaires de la ligue majeure de leur région */
  function majorRef(region, role) {
    const cnt = {}; for (const t of S.teams) if (t.tier === 0 && D.region[t.league] === region) cnt[t.league] = (cnt[t.league] || 0) + 1;
    const lg = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0];
    const of = (T) => T.map((t) => byId.get(t.roster[role])).filter(Boolean);
    return { lg, own: lg ? of(S.teams.filter((t) => t.league === lg)) : [], all: of(S.teams.filter((t) => t.tier === 0)) };
  }
  function cracks(over) {
    const c = Object.assign({}, state.sc.cr, over), refs = {};
    const out = [];
    for (const p of S.players) {
      if ((p.age ? p.age > c.maxAge : !c.noAge) || (c.role && p.role !== c.role) || !p.tr || !cMatch(p, c.contract)) continue;
      const cand = ['1', '2'].filter((k) => (k === '1' || c.deep) && p.tr[k] && p.tr[k][1] >= c.minG).map((k) => [k, p.tr[k]]).sort((a, b) => b[1][1] - a[1][1])[0];
      if (!cand) continue;
      const v = cand[1], region = D.region[v[3]] || p.region, maj = p.tr['0'];
      if ((c.region && region !== c.region) || (c.fresh && maj)) continue;
      const key = region + p.role, ref = refs[key] || (refs[key] = majorRef(region, p.role));
      // titulaires de la ligue majeure de sa région, puis de toutes les ligues majeures (lui-même exclu s'il y est devenu titulaire)
      // note estimée en ligue majeure (droite ajustée sur les joueurs des deux niveaux la même saison) ; le troisième niveau n'a pas de projection
      let est = cand[0] === '1' && D.proj ? D.proj.a + D.proj.b * v[0] : v[0];
      // parties déjà jouées en ligue majeure cette saison : mélangées à l'estimation, partie pour partie (le meilleur poids sur la saison suivante)
      if (maj) est = (est * v[1] + maj[0] * maj[1]) / (v[1] + maj[1]);
      const cmp = (L) => { L = L.filter((x) => x.id !== p.id); const a = L.filter((x) => x.note < est).length; return { a, N: L.length, share: L.length ? a / L.length : 0 }; };
      const own = cmp(ref.own), all = cmp(ref.all);
      const verdict = own.share >= 0.5 ? 2 : own.share >= 0.25 ? 1 : 0;
      if (!c.all && !verdict) continue;
      out.push({ p, note: v[0], est, n: v[1], team: v[2], lg: v[3], tier: +cand[0], region, maj, lgRef: ref.lg, own, all, verdict });
    }
    return out.sort((a, b) => b.est - a.est);
  }
  function renderCracks() {
    const c = state.sc.cr, rows = $('#crack-rows');
    $('#c-roles').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.role === c.role));
    $('#c-age').value = c.maxAge; $('#c-min').value = c.minG; $('#c-deep').checked = c.deep; $('#c-fresh').checked = c.fresh; $('#c-all').checked = c.all; $('#c-noage').checked = c.noAge;
    $('#c-contract').disabled = !hasCT(); $('#c-contract').value = hasCT() ? c.contract : '';
    const regions = [...new Set(S.players.filter((p) => p.tier > 0).map((p) => p.region))].sort();
    $('#c-region').innerHTML = '<option value="">Toutes</option>' + regions.map((r) => `<option${r === c.region ? ' selected' : ''}>${h(r)}</option>`).join('');
    if (!hasAge()) { $('#crack-count').textContent = ''; rows.innerHTML = '<p class="none">Les âges ne sont pas disponibles pour cette saison : la recherche de jeunes joueurs ne peut pas se faire.</p>'; return; }
    const L = cracks();
    const hidden = c.noAge ? 0 : cracks({ noAge: true }).filter((x) => !x.p.age).length;
    $('#crack-count').textContent = `${fmt(L.length)} joueur${L.length > 1 ? 's' : ''} de ${c.maxAge} ans ou moins${c.noAge ? ' ou d\'âge inconnu' : ''}` + (hidden ? `. ${hidden} autre${hidden > 1 ? 's' : ''} d'âge inconnu, à afficher avec la case plus bas.` : '');
    if (!L.length) { rows.innerHTML = '<p class="none">Aucun joueur avec ces critères. Relevez l\'âge maximum ou affichez aussi ceux qui sont encore loin du niveau.</p>'; return; }
    rows.innerHTML = L.slice(0, c.shown).map((x, i) => {
      const p = x.p, N = x.own.N, ins = insights(p).plus.slice(0, 2).map((s) => s.replace(/<b>(.*?)<\/b>.*/, '$1'));
      const where = h(lgName(x.lgRef || ''));
      const face = (x.tier === 1 ? `Estimé à <b>${nInt(x.est)}</b> en ligue majeure : ` : 'Pas d\'estimation depuis le troisième niveau : ') + (!N ? '' : x.own.a === 0 ? `derrière les ${N} titulaires de ${where}` : x.own.a === N ? `devant les ${N} titulaires de ${where}` : `devant ${x.own.a} des ${N} titulaires de ${where}`) +
        (x.all.N ? `${N ? ', et ' : ''}${x.all.a} des ${x.all.N} de toutes les ligues majeures` : '');
      const tag = x.verdict === 2 ? '<span class="tag gold">Niveau titulaire</span>' : x.verdict === 1 ? '<span class="tag">Mérite un essai</span>' : '<span class="tag mute">À suivre</span>';
      return `<button class="row" data-p="${p.id}"><span class="rank">${i + 1}</span><span class="num note ${noteCls(x.note)}">${nInt(x.note)}</span>
        <span class="who"><b>${h(p.name)}</b><small>${h(x.team)}, ${h(lgName(x.lg))}, ${p.age ? p.age + ' ans' : 'âge inconnu'} ${cShort(p)}${x.maj ? `<span class="moved"><br>Déjà ${x.maj[1]} parties en ${h(lgName(x.maj[3]))}, note ${nInt(x.maj[0])}</span>` : ''}</small></span>
        <span class="pos">${p.role}</span><span class="face">${tag}<small>${face}</small></span>
        <span class="pos games"><small>${archetype(p) || ''}${ins.length ? '<br>' + ins.join(', ') : ''}</small></span><span class="r games">${x.n}</span></button>`;
    }).join('') + (L.length > c.shown ? '<button class="more" id="crack-more">Afficher 60 joueurs de plus</button>' : '');
  }

  function suggest(q) {
    const box = $('#suggest'); q = q.trim().toLowerCase();
    if (!q) { box.hidden = true; return; }
    const T = S.teams.filter((t) => t.name.toLowerCase().includes(q)).sort((a, b) => b.lvl - a.lvl).slice(0, 12);
    box.innerHTML = T.length ? T.map((t) => `<button data-tid="${h(t.tid)}"><span>${h(t.name)}</span><small>${h(lgName(t.league))}</small></button>`).join('') : '<p class="none" style="padding:10px">Aucune équipe à ce nom cette saison.</p>';
    box.hidden = false;
  }

  /* ------------------------------------------------------------ power ranking */
  /* Niveau d'équipe de la saison choisie (modèle de victoire, le même que « niveau de l'équipe » de la fiche) : il ne dépend pas
     du bouton Rift Scout / Mixte / Unifiée. */
  function renderPower() {
    const f = state.pw, endB = f.basis === 'end';
    $('#p-tier').value = f.tier; $('#p-region').value = f.region; $('#p-league').value = f.league;
    document.querySelectorAll('#p-basis button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.pbasis === f.basis));
    const lvOf = (t) => (endB ? (t.rc ? t.rc[0] : null) : t.lvl);
    const Lall = S.teams.filter((t) => (f.tier === '' || t.tier === +f.tier) && (!f.region || t.region === f.region) && (!f.league || t.league === f.league));
    const L = Lall.filter((t) => t.end !== false && lvOf(t) != null).sort((a, b) => lvOf(b) - lvOf(a));   // présentes au dernier segment de leur ligue
    const gone = Lall.filter((t) => t.end === false).length, few = Lall.filter((t) => t.end !== false && lvOf(t) == null).length;
    const inLg = {}; for (const t of S.teams) if (t.end !== false && lvOf(t) != null) (inLg[t.league] = inLg[t.league] || []).push(lvOf(t));
    $('#p-sub').textContent = endB
      ? `Niveau réestimé sur les parties jouées depuis le début du dernier split de chaque ligue (playoffs, qualifications et tournois qui ont suivi compris), le niveau de saison ne servant que de point de départ. C'est l'état des équipes en fin d'année, sur moins de parties : plus réactif, plus incertain, et il ne prédit pas mieux la suite que le niveau de saison. Ne dépend pas du choix Rift Scout, Mixte ou Unifiée.`
      : `Le niveau d'une équipe vient du modèle de victoire de la saison ${state.season}, le même que le « niveau de l'équipe » de la fiche d'un joueur. Il est commun à toutes les ligues et ne dépend pas du choix Rift Scout, Mixte ou Unifiée.`;
    $('#p-count').textContent = `${fmt(L.length)} équipe${L.length > 1 ? 's' : ''}, saison ${state.season}${gone ? `. ${fmt(gone)} autre${gone > 1 ? 's' : ''} absente${gone > 1 ? 's' : ''} du dernier segment de sa ligue (invitée ou partie en cours d'année), non classée${gone > 1 ? 's' : ''}` : ''}${few ? `. ${fmt(few)} avec moins de 8 parties en fin de saison, non classée${few > 1 ? 's' : ''}` : ''}. « Situé par sa ligue » : aucun match contre une équipe d'une autre ligue cette saison, son niveau face au reste du monde passe par celui de sa ligue.`;
    const el = $('#p-rows');
    if (!L.length) { el.innerHTML = '<p class="none">Aucune équipe ne correspond à ces filtres.</p>'; return; }
    const late = Date.parse(S.to) - 180 * 864e5;
    el.innerHTML = L.slice(0, f.shown).map((t, i) => {
      const lu = ROLES.map((r) => { const p = byId.get(t.roster[r]); return p ? `<button class="pl" data-p="${p.id}" title="${r}, note ${nInt(p.note)}"><small>${r}</small>${h(p.name)}</button>` : `<span class="pl"><small>${r}</small>–</span>`; }).join('');
      const v = lvOf(t), rk = inLg[t.league].filter((x) => x > v).length + 1;
      const extra = endB ? `${fmt(t.rc[1])} parties depuis le ${frDate(t.rc[2])}, saison ${nInt(t.lvl)}` : `${fmt(t.n)} parties, ${pctTxt(t.win)} de victoires${Date.parse(t.last) < late ? `, dernière partie le ${frDate(t.last)}` : ''}`;
      return `<div class="prow"><span class="rank">${i + 1}</span>
        <span class="lvl"><span class="num note ${noteCls(v)}">${nInt(v)}</span>${!endB && t.se ? `<small>± ${fmt(t.se, 1)}</small>` : ''}</span>
        <span class="who"><b>${h(t.name)}</b><small>${h(lgName(t.league))}${f.league ? '' : ', ' + ord(rk) + ' en ' + h(lgName(t.league))}${t.nx === 0 ? ', <span class="tag-lg" title="Aucun match contre une équipe d\'une autre ligue cette saison">situé par sa ligue</span>' : ''}</small>
          <small>${extra}</small></span>
        <span class="lu">${lu}</span></div>`;
    }).join('') + (L.length > f.shown ? '<button class="more" id="p-more">Afficher 100 équipes de plus</button>' : '');
  }

  /* ------------------------------------------------------------ transferts */
  const LAST = Object.keys(D.seasons).sort().pop();
  /* 0,106 par point de moyenne des notes de saison (pente réglée par tools/bench_transfers.py sur les matchs de la saison suivante, 0,102 en 2024 → 2025 et 0,111 en 2025 → 2026), soit 0,147 par point de note attendue (droite des joueurs de ligue majeure, pente 0,722) */
  const WIN_SLOPE = 0.147;
  /* note attendue en ligue majeure la saison suivante (droites D.next.lines : déjà en ligue majeure, ou montée d'un niveau
     inférieur ; elles tiennent compte du retour vers la moyenne) ; suit le bouton de calcul */
  const tvalue = (p) => { const l = D.next.lines ? D.next.lines[p.tier === 0 ? 'maj' : 'low'] : null; return l ? l.a + l.b * p.note : p.note; };
  function quantile(a, q) { a = a.slice().sort((x, y) => x - y); const i = (a.length - 1) * q, lo = Math.floor(i); return a[lo] + (a[Math.min(lo + 1, a.length - 1)] - a[lo]) * (i - lo); }
  const rankOf = (v, all) => all.filter((x) => x > v).length + 1;
  const dCls = (d) => (d > 0.05 ? 'up' : d < -0.05 ? 'down' : 'flat');
  const sgn = (d) => (d > 0.05 ? '+' : d < -0.05 ? '−' : '') + fmt(Math.abs(d), 1);
  function nextLeagues() {
    const tier = {}, cnt = {};
    for (const t of D.next.teams) { tier[t.league] = t.tier; cnt[t.league] = (cnt[t.league] || 0) + 1; }
    return Object.keys(tier).sort((a, b) => tier[a] - tier[b] || cnt[b] - cnt[a] || lgName(a).localeCompare(lgName(b)));
  }
  /* Calcul d'une ligue de l'onglet, partagé avec la fiche d'équipe : mêmes valeurs, même valeur par défaut, mêmes rangs. */
  function transferModel(lg) {
    const N = D.next, LP = new Map(D.seasons[LAST].players.map((p) => [p.id, p]));
    const T = N.teams.filter((t) => t.league === lg);
    // titulaires actuels de la ligue, par poste, avec leur valeur
    const starters = {}; for (const r of ROLES) starters[r] = T.map((t) => ({ t, p: LP.get(t.cur[r]) })).filter((s) => s.p).map((s) => ({ t: s.t, id: s.p.id, v: tvalue(s.p) }));
    // valeur par défaut : 25e centile des valeurs des titulaires actuels de la ligue
    const known = ROLES.flatMap((r) => starters[r].map((s) => s.v));
    const def = known.length ? quantile(known, 0.25) : 0;
    const slot = (x) => { const p = typeof x === 'string' ? LP.get(x) : null; return p ? tvalue(p) : def; };
    const level = (ros) => mean(ROLES.map((r) => slot(ros[r])));
    const X = T.map((t) => {
      const cur = t.tid ? level(t.cur) : null, nAnn = t.nxt ? ROLES.filter((r) => t.nxt[r]).length : 0;
      return { t, cur, exp: t.nxt ? level(t.nxt) : cur, nAnn, state: !t.nxt || !nAnn ? 'pas annoncé' : nAnn === 5 ? 'annoncé' : `partiel (${nAnn} poste${nAnn > 1 ? 's' : ''})` };
    }).sort((a, b) => b.exp - a.exp);
    const curs = X.filter((x) => x.cur != null).map((x) => x.cur), exps = X.map((x) => x.exp);
    X.forEach((x) => { x.rc = x.cur != null ? rankOf(x.cur, curs) : null; x.re = rankOf(x.exp, exps); x.d = x.cur != null ? x.exp - x.cur : null; });
    return { LP, T, X, def, slot, level, starters };
  }
  function renderTransfers() {
    const N = D.next;
    const lgs = nextLeagues();
    if (!lgs.includes(state.tr.league)) state.tr.league = lgs.includes('LEC') ? 'LEC' : lgs[0];
    const lg = state.tr.league, tierOf = {}; N.teams.forEach((t) => { tierOf[t.league] = t.tier; });
    $('#t-league').innerHTML = [0, 1, 2].map((k) => { const ls = lgs.filter((l) => tierOf[l] === k); return ls.length ? `<optgroup label="${TIERS[k]}">` + ls.map((l) => `<option value="${h(l)}"${l === lg ? ' selected' : ''}>${h(lgName(l))}${D.desc[l] && lgName(l) === l ? ' (' + h(D.desc[l]) + ')' : ''}</option>`).join('') + '</optgroup>' : ''; }).join('');
    $('#t-src').innerHTML = `Effectifs annoncés : ${h(N.source)}. Effectif actuel : 12 dernières parties de chaque équipe.`;
    const warn = $('#t-warn'); warn.hidden = state.season === LAST;
    warn.textContent = state.season === LAST ? '' : `Cet onglet porte toujours sur la dernière saison (${LAST}), quelle que soit la saison choisie en haut de la page : ${LAST} pour l'effectif actuel, ${N.season} pour l'effectif annoncé.`;
    const { LP, X, def } = transferModel(lg);
    $('#t-sub').textContent = `Effectif actuel et effectif annoncé pour la saison ${N.season}, ${lgName(lg)}. Le niveau d'un effectif est la moyenne des valeurs de ses cinq joueurs.`;
    $('#t-count').innerHTML = `${X.length} équipes. Le chiffre à côté de chaque joueur est sa valeur attendue en ligue majeure la saison suivante, celle qui entre dans la moyenne ; sa note de saison est indiquée à côté (un joueur qui monte d'un niveau inférieur n'en garde qu'un peu plus de la moitié de l'écart à la moyenne). Joueur sans note ou poste pas encore annoncé : ${fmt(def, 1)}, le 25<sup>e</sup> centile des titulaires actuels de ${h(lgName(lg))}.`;
    $('#t-rank').innerHTML = X.map((x) => {
      const t = x.t, mv = x.rc == null ? '<span class="flat">nouvelle dans la ligue</span>' : `<span class="${x.re < x.rc ? 'up' : x.re > x.rc ? 'down' : 'flat'}">${ord(x.rc)} → ${ord(x.re)}</span>`;
      return `<div class="trow"><span class="rank">${x.re}</span><span class="who"><b><button class="pl2 tm" data-tm="${N.teams.indexOf(t)}">${h(t.name)}</button></b></span>
        <span class="num note ${noteCls(x.exp)}">${fmt(x.exp, 1)}</span><span class="trend r ${x.d == null ? 'flat' : dCls(x.d)}">${x.d == null ? '–' : sgn(x.d)}</span>
        <span class="mv">${mv}</span><span class="st">${x.state}${t.nxt ? '' : '<small>effectif actuel conservé</small>'}</span></div>`;
    }).join('');
    const who = (x, cur, same) => {
      const p = typeof x === 'string' ? LP.get(x) : null, strong = !same && x ? ' in' : '';
      if (p) { const v = tvalue(p); return `<button class="pl2${strong}" data-p="${p.id}">${h(p.name)}</button> <span class="pn ${noteCls(v)}" title="Valeur comptée dans le niveau de l'effectif">${fmt(v, 1)}</span> <small>note ${state.season === LAST ? '' : LAST + ' '}${nInt(p.note)}${p.tier > 0 ? ', ' + TIER_IN[p.tier] : ''}</small>`; }
      if (x && x.name) return `<span class="${strong.trim()}">${h(x.name)}</span> <small>sans note</small>`;
      if (typeof x === 'string') return '<small>joueur introuvable</small>';
      return cur ? '<span class="tbd">–</span>' : '<span class="tbd">pas encore annoncé</span>';
    };
    $('#t-cards').innerHTML = X.map((x) => {
      const t = x.t;
      return `<section class="tcard"><header><h3><button class="pl2 tm" data-tm="${N.teams.indexOf(t)}">${h(t.name)}</button></h3><span class="tlvl">${x.cur != null ? fmt(x.cur, 1) + ' → ' : ''}<b class="${noteCls(x.exp)}">${fmt(x.exp, 1)}</b>${x.d != null ? ` <em class="${dCls(x.d)}">${sgn(x.d)}</em>` : ''}</span></header>
        <p class="legend">${t.tid ? (t.nxt ? x.state : 'effectif pas encore annoncé') : 'nouvelle dans la ligue'}</p>
        ${ROLES.map((r) => {
          const c = t.cur[r], n = t.nxt ? t.nxt[r] : c, same = !t.nxt || (typeof n === 'string' && n === c);
          return `<div class="tline"><span class="role">${r}</span><span>${c ? who(c, true, true) : '<span class="tbd">–</span>'}</span><span class="arrow" aria-hidden="true">→</span><span>${who(n, !t.nxt, same)}</span></div>`;
        }).join('')}</section>`;
    }).join('');
  }

  /* ------------------------------------------------------------ fiche d'équipe (onglet Transferts) */
  const winProb = (a, b) => 1 / (1 + Math.exp(-WIN_SLOPE * (a - b)));
  const de = (n) => (/^[AEIOUYÉ]/.test(n) ? "d'" : 'de ') + n;
  const places = (from, to) => {   // from : rang actuel, to : rang attendu
    const n = from - to;
    return n === 0 ? ['même rang', 'flat'] : n > 0 ? [`${n} place${n > 1 ? 's' : ''} de mieux`, 'up'] : [`${-n} place${n < -1 ? 's' : ''} de moins`, 'down'];
  };
  const ordTxt = (n) => (n === 1 ? '1er' : n + 'e');
  const pctPt = (x) => fmt(x * 100, 1) + ' %';
  const pts = (d) => (d > 0.0005 ? '+' : d < -0.0005 ? '−' : '') + fmt(Math.abs(d) * 100, 1) + (Math.abs(d) * 100 >= 1.95 ? ' points' : ' point');
  function openTeamSheet(i) {
    const N = D.next, t = N.teams[i]; if (!t) return;
    const m = transferModel(t.league), x = m.X.find((y) => y.t === t), LG = lgName(t.league);
    const pseudo = (v) => { const p = typeof v === 'string' ? m.LP.get(v) : null; return p ? p.name : v && v.name ? v.name : '?'; };
    // fiche d'un poste : valeur, et rang parmi les titulaires actuels du poste
    const info = (r, v, rank) => {
      const p = typeof v === 'string' ? m.LP.get(v) : null, val = m.slot(v);
      if (p) return { id: p.id, p, val, nm: p.name, html: `<button class="pl2" data-p="${p.id}">${h(p.name)}</button>`, sub: rank != null ? `${ord(rank)} des ${ROLE_PL[r]} ${de(h(LG))}` : '', subTxt: rank != null ? `${ordTxt(rank)} des ${ROLE_PL[r]} ${de(LG)}` : '' };
      if (v && v.name) return { val, nm: v.name, html: h(v.name), sub: 'sans note', subTxt: 'sans note' };
      if (typeof v === 'string') return { val, nm: 'joueur introuvable', gone: true, html: '<span class="tbd">joueur introuvable</span>', sub: '', subTxt: '' };
      return null;
    };
    const cardRows = [];
    const rows = ROLES.map((r) => {
      const c = t.cur[r], keep = !t.nxt, n = keep ? c : t.nxt[r];
      const cv = typeof c === 'string' ? m.LP.get(c) : null;
      const cInfo = c ? info(r, c, cv ? rankOf(tvalue(cv), m.starters[r].map((s) => s.v)) : null) : null;
      const np = typeof n === 'string' ? m.LP.get(n) : null;
      const others = np ? m.starters[r].filter((s) => s.t !== t && s.id !== np.id).map((s) => s.v) : null;
      const nInfo = n ? info(r, n, np ? rankOf(tvalue(np), others) : null) : null;
      const same = typeof n === 'string' && n === c;
      const cell = (o, empty, extra) => o ? `<span class="pc${extra || ''}">${o.html}<small>${o.sub}</small></span><b class="pn pv ${noteCls(o.val)}">${fmt(o.val, 1)}</b>` : `<span class="pc tbd">${empty}</span><b class="pv tbd">${empty === '–' ? '' : fmt(m.def, 1)}</b>`;
      const dv = !cInfo || !nInfo || same ? null : nInfo.val - cInfo.val;
      const chg = dv == null ? '<span class="flat">—</span>' : `<span class="${dCls(dv)}">${sgn(dv)}</span>`;
      cardRows.push({ r, cInfo, nInfo, same, dv });
      return `<div class="chg"><span class="role">${r}</span>${cell(cInfo, '–')}${cell(nInfo, 'pas encore annoncé', same ? '' : ' in')}<span class="cg">${chg}</span></div>`;
    }).join('');
    // rang parmi les équipes des ligues majeures : niveaux actuels pour le rang actuel, niveaux attendus pour le rang attendu
    const tierOf = (l) => N.teams.find((y) => y.league === l).tier;
    const maj = nextLeagues().filter((l) => tierOf(l) === 0).flatMap((l) => transferModel(l).X);
    const mc = maj.filter((y) => y.cur != null).map((y) => y.cur), me = maj.map((y) => y.exp);
    const inMaj = t.tier === 0, gc = x.cur != null ? rankOf(x.cur, mc) : null, ge = rankOf(x.exp, me);
    const pair = (l1, a, l2, b, cls) => `<div class="tk-pair"><div><small>${l1}</small><span class="num">${a}</span></div><span class="arrow" aria-hidden="true">→</span><div><small>${l2}</small><span class="num ${cls || ''}">${b}</span></div></div>`;
    const mv = (from, to) => { if (from == null) return '<p class="tk-d flat">nouvelle dans la ligue</p>'; const [txt, cls] = places(from, to); return `<p class="tk-d ${cls}">${txt}</p>`; };
    // adversaires : les trois meilleures autres équipes de la ligue en niveau attendu (les trois suivantes si elle est dans le top 3)
    const opp = m.X.filter((y) => y !== x).slice(0, 3);
    const wins = opp.map((o) => ({ o, p26: x.cur != null ? winProb(x.cur, o.exp) : null, p27: winProb(x.exp, o.exp) }));
    const chances = wins.map(({ o, p26, p27 }) => {
      return `<div class="win"><span class="pc"><b>${h(o.t.name)}</b><small>niveau attendu ${fmt(o.exp, 1)}</small></span><span class="wv">${p26 != null ? pctPt(p26) : '–'}</span><span class="wv"><b>${pctPt(p27)}</b></span><span class="wv ${p26 != null ? dCls((p27 - p26) * 100) : 'flat'}">${p26 != null ? pts(p27 - p26) : '–'}</span></div>`;
    }).join('');
    const [pl, pc] = gc != null ? places(gc, ge) : [null, 'flat'];
    const stateTxt = !t.tid ? 'nouvelle dans la ligue' : 'effectif ' + x.state;
    const mention = `Une partie, côté neutre, force des effectifs seulement : ni forme, ni entente, ni draft. Adversaires avec leur effectif ${N.season} annoncé (actuel s'il ne l'est pas). Rangs par poste parmi les titulaires actuels de la ligue.`;
    showSheet(`<header class="tm-head"><div><h2 id="sheet-name">${h(t.name)}</h2>
      <p class="meta">${h(LG)} (${h(t.region)}), ${stateTxt}<br>Effectif ${N.season} : ${ROLES.map((r) => h(t.nxt ? pseudo(t.nxt[r]) : '?')).join(' · ')}</p></div><div class="hbtns"><button class="close" data-card>Télécharger l'image</button><button class="close" data-close>Fermer</button></div></header>
      <section><div class="split tk">
        <div>${pair(`Rang en ${h(LG)} ${LAST}`, x.rc != null ? ord(x.rc) : '–', `Rang attendu en ${N.season}`, ord(x.re))}${mv(x.rc, x.re)}</div>
        <div>${pair('Niveau actuel', x.cur != null ? fmt(x.cur, 1) : '–', 'Niveau attendu', fmt(x.exp, 1), noteCls(x.exp))}${x.d != null ? `<p class="tk-d ${dCls(x.d)}">${sgn(x.d)} point${Math.abs(x.d) >= 1.95 ? 's' : ''}</p>` : '<p class="tk-d flat">–</p>'}</div></div></section>
      <section><h3>Changements de joueurs</h3>
        <div class="chg chg-h"><span class="role">Poste</span><span class="pc">Joueur actuel</span><span class="pv">Valeur</span><span class="pc">Joueur attendu</span><span class="pv">Valeur</span><span class="cg">Changement</span></div>${rows}
        <p class="legend">La valeur est la note attendue en ligue majeure la saison suivante, celle qui entre dans le niveau de l'effectif. Joueur sans note ou poste pas annoncé : ${fmt(m.def, 1)}, le 25<sup>e</sup> centile des titulaires actuels de ${h(LG)}.${t.nxt ? '' : ' Effectif ' + N.season + ' pas annoncé : l\'effectif actuel est conservé pour le calcul.'}</p></section>
      <section><h3>Rang parmi les équipes des ligues majeures</h3>
        <div class="split tk tk1"><div>${pair('Rang actuel', gc != null ? ord(gc) : '–', `Rang attendu en ${N.season}`, ord(ge))}${gc != null ? mv(gc, ge) : mv(null)}</div></div>
        <p class="legend">${inMaj ? '' : `${h(LG)} n'est pas une ligue majeure : le rang est celui qu'aurait l'équipe parmi les ${fmt(maj.length)} équipes de ligue majeure. `}Parmi ${fmt(maj.length)} équipes de ligue majeure : niveaux actuels pour le rang actuel, niveaux attendus pour le rang attendu, chaque ligue avec sa propre valeur par défaut. Les niveaux sont sur l'échelle commune à toutes les ligues.</p></section>
      <section><h3>Chances de gagner une partie</h3>
        <div class="win win-h"><span class="pc">Contre</span><span class="wv">Effectif ${LAST}</span><span class="wv">Effectif ${N.season}</span><span class="wv">Écart</span></div>${chances}
        <p class="legend">Contre les trois meilleures autres équipes de ${h(LG)} en niveau attendu ${N.season}${x.re <= 3 ? ' (l\'équipe est dans le top 3 : la quatrième équipe complète la liste)' : ''}. « Effectif ${LAST} » : niveau actuel de l'équipe contre le niveau attendu de l'adversaire ; « effectif ${N.season} » : niveau attendu contre niveau attendu.</p></section>
      <section><p class="legend" style="margin-top:0">${mention} Effectifs annoncés : ${h(N.source)}.</p></section>`,
      { kind: 'team', t, x, N, LG, LAST, stateTxt, cardRows, def: m.def, wins, gc, ge, nMaj: maj.length, inMaj, mention, pseudo, file: cardFile(t.name, N.season) });
  }

  /* ------------------------------------------------------------ carte image (bouton « Télécharger l'image » des fiches)
     La carte est dessinée à la main dans un <canvas> (API Canvas 2D), jamais copiée depuis la page : pas de capture, pas de SVG
     foreignObject (canvas souillé sous Safari). Chaque fiche passe ses valeurs à showSheet : la carte reprend les mêmes nombres. */
  const CARD_W = 1080, CARD_PAD = 56, CARD_SCALE = 2;
  const CALC_NAME = { rift: 'Rift Scout', mix: 'Mixte', uni: 'Unifiée' };
  const SITE = 'Rift Scout · oradixx.github.io/rift-scout';
  const cardFile = (who, season) => 'rift-scout-' + (who + '-' + season).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '.png';
  const cardNoteC = (n) => ({ 't-gold': 'gold', 't-cob': 'cobalt', 't-mid': 'ink', 't-low': 'ink-3' }[noteCls(n)]);
  const cardDeltaC = (cls) => ({ up: 'teal', down: 'rose', flat: 'ink-3' }[cls]);
  /* couleurs lues au moment du clic : thème clair ou sombre et teinte du calcul actif */
  function cardPalette() {
    const cs = getComputedStyle(document.documentElement), C = {};
    ['fog', 'paper', 'ink', 'ink-2', 'ink-3', 'line', 'line-2', 'cobalt', 'cobalt-soft', 'gold', 'rose', 'teal', 'n0', 'n1', 'n2', 'n3', 'n4', 'display', 'text'].forEach((k) => { C[k] = cs.getPropertyValue('--' + k).trim(); });
    return C;
  }
  async function cardFonts() {
    try {
      await document.fonts.ready;
      await Promise.all(['900 40px "Big Shoulders Display"', '800 40px "Big Shoulders Display"', '400 20px "Hanken Grotesk"', '600 20px "Hanken Grotesk"', '700 20px "Hanken Grotesk"'].map((f) => document.fonts.load(f)));
    } catch (e) { /* polices indisponibles : la pile de repli de --display et --text prend le relais */ }
  }
  function fitText(ctx, s, max) {   // texte tronqué à une largeur, avec « … »
    s = String(s);
    if (ctx.measureText(s).width <= max) return s;
    while (s.length > 1 && ctx.measureText(s + '…').width > max) s = s.slice(0, -1);
    return s.trimEnd() + '…';
  }
  function wrapLines(ctx, s, max, maxLines) {   // retour à la ligne aux espaces ; la dernière ligne permise est tronquée
    const lines = []; let cur = '';
    for (const w of String(s).split(' ')) {
      const t = cur ? cur + ' ' + w : w;
      if (cur && ctx.measureText(t).width > max) { lines.push(cur); cur = w; } else cur = t;
    }
    if (cur) lines.push(cur);
    return maxLines && lines.length > maxLines ? lines.slice(0, maxLines - 1).concat(fitText(ctx, lines.slice(maxLines - 1).join(' '), max)) : lines;
  }
  /* o : { px, w (graisse), disp (police des chiffres), c (clé de couleur ou couleur CSS), align, max (largeur de troncature) } */
  function cardPen(ctx, C, H) {
    const set = (o) => { ctx.font = `${o.w || 400} ${o.px || 24}px ${o.disp ? C.display : C.text}`; ctx.fillStyle = C[o.c || 'ink'] || o.c; ctx.textAlign = o.align || 'left'; ctx.textBaseline = 'alphabetic'; };
    const P = {
      ctx, C,
      rect(x, y, w, h, c) { ctx.fillStyle = C[c] || c; ctx.fillRect(x, y, w, h); },
      panel(x, y, w, h) {   // rectangle arrondi, fond papier, filet
        const r = 10; ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
        ctx.fillStyle = C.paper; ctx.fill(); ctx.strokeStyle = C.line; ctx.lineWidth = 1; ctx.stroke();
      },
      text(s, x, y, o) { set(o); const t = o.max ? fitText(ctx, s, o.max) : String(s); ctx.fillText(t, x, y); return ctx.measureText(t).width; },
      lines(s, max, o, n) { set(o); return wrapLines(ctx, s, max, n); },
      para(s, x, y, max, o, lh, n) { const L = P.lines(s, max, o, n); L.forEach((l, i) => P.text(l, x, y + i * lh, o)); return y + L.length * lh; },   // rend la ligne suivante
      width(s, o) { set(o); return ctx.measureText(s).width; },
      /* grand chiffre en police d'affichage, réduit pour tenir dans max ; suf : exposant (er, e) */
      big(s, x, y, max, px, c, suf) {
        let size = px; const o = () => ({ px: size, w: 800, disp: 1, c });
        while (size > 36 && P.width(s, o()) + (suf ? size * 0.5 : 0) > max) size -= 4;
        const w = P.text(s, x, y, o());
        if (suf) P.text(suf, x + w + 2, y - size * 0.4, { px: size * 0.42, w: 800, disp: 1, c });
        return size;
      },
      arrow(x, y, w, c) { ctx.strokeStyle = C[c]; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w, y); ctx.moveTo(x + w - 9, y - 9); ctx.lineTo(x + w, y); ctx.lineTo(x + w - 9, y + 9); ctx.stroke(); },
      /* barre horizontale de note (échelle 30 à 99 comme la page), avec un repère vertical facultatif */
      bar(x, y, w, n, ref) {
        const f = (v) => Math.max(0, Math.min(1, (v - 30) / 69));
        P.rect(x, y, w, 16, 'line-2'); P.rect(x, y, Math.max(2, w * f(n)), 16, C['n' + noteVar(n).slice(-2, -1)]);
        if (ref != null) P.rect(x + w * f(ref) - 1.5, y - 5, 3, 26, 'ink');
      },
      fill() { P.rect(0, 0, CARD_W, H || 0, 'fog'); }
    };
    return P;
  }
  /* deux valeurs reliées par une flèche, dans un cadre ; a et b : { label, num, suf, c }, foot : { txt, c } */
  function cardPair(P, x, y, w, a, b, foot) {
    const col = (w - 48 - 52) / 2, BIG = 96;
    P.panel(x, y, w, 236);
    [[a, x + 24], [b, x + 24 + col + 52]].forEach(([v, vx]) => {
      P.lines(v.label, col, { px: 19, c: 'ink-3' }, 2).forEach((l, i) => P.text(l, vx, y + 40 + i * 24, { px: 19, c: 'ink-3' }));
      P.big(v.num, vx, y + 160, col - 4, BIG, v.c, v.suf);
    });
    P.arrow(x + 24 + col + 12, y + 160 - BIG * 0.35, 28, 'ink-3');
    P.text(foot.txt, x + 24, y + 208, { px: 26, w: 700, c: foot.c, max: w - 48 });
  }
  const cardMove = (from, to) => { if (from == null) return { txt: 'nouvelle dans la ligue', c: 'ink-3' }; const [txt, cls] = places(from, to); return { txt, c: cardDeltaC(cls) }; };
  /* bas de carte : mention, source, calcul utilisé et signature ; rend la hauteur totale de la carte */
  function cardFoot(P, y, texts, calcTxt) {
    const L = CARD_PAD, IW = CARD_W - 2 * L;
    P.rect(L, y, IW, 1, 'line'); y += 36;
    texts.forEach((t) => { y = P.para(t, L, y, IW, { px: 20, c: 'ink-2' }, 28) + 4; });
    y += 14;
    const sw = P.text(SITE, CARD_W - L, y, { px: 22, w: 700, c: 'cobalt', align: 'right' });
    P.text(calcTxt, L, y, { px: 22, w: 600, c: 'ink-2', max: IW - sw - 24 });
    return y + 48;
  }
  const cardStripe = (P) => P.rect(0, 0, CARD_W, 10, 'cobalt');

  function drawTeamCard(P, M) {
    const L = CARD_PAD, IW = CARD_W - 2 * L, { t, x, N, LG } = M, to = D.seasons[M.LAST].to;
    P.fill();
    // en-tête : nom, ligue, effectif annoncé, date des données
    const MET = { px: 26, c: 'ink-2' };
    const eff = P.lines(`Effectif ${N.season} : ${ROLES.map((r) => (t.nxt ? M.pseudo(t.nxt[r]) : '?')).join(' · ')}`, IW, MET, 2);
    const head = [`${LG} (${t.region}), ${M.stateTxt}`, ...eff, `Données au ${cDate(to, true)}`];
    const bandH = 10 + 36 + 70 + 18 + head.length * 36 + 26;
    P.rect(0, 0, CARD_W, bandH, 'paper'); P.rect(0, bandH - 1, CARD_W, 1, 'line'); cardStripe(P);
    P.text(t.name, L, 10 + 36 + 66, { px: 84, w: 900, disp: 1, max: IW });
    head.forEach((l, i) => P.text(l, L, 10 + 36 + 70 + 18 + 26 + i * 36, i === head.length - 1 ? { px: 22, c: 'ink-3' } : MET));
    let y = bandH;
    const title = (s) => { y += 56; P.text(s, L, y, { px: 30, w: 700 }); y += 22; };
    // rangs et niveaux
    y += 32;
    const pw = (IW - 24) / 2, mv = cardMove(x.rc, x.re), gap = x.d == null ? { txt: '–', c: 'ink-3' } : { txt: `${sgn(x.d)} point${Math.abs(x.d) >= 1.95 ? 's' : ''}`, c: cardDeltaC(dCls(x.d)) };
    cardPair(P, L, y, pw, { label: `Rang en ${LG} ${M.LAST}`, num: x.rc != null ? String(x.rc) : '–', suf: x.rc != null ? (x.rc === 1 ? 'er' : 'e') : '', c: 'ink' },
      { label: `Rang attendu en ${N.season}`, num: String(x.re), suf: x.re === 1 ? 'er' : 'e', c: 'ink' }, mv);
    cardPair(P, L + pw + 24, y, pw, { label: 'Niveau actuel', num: x.cur != null ? fmt(x.cur, 1) : '–', c: 'ink' },
      { label: 'Niveau attendu', num: fmt(x.exp, 1), c: cardNoteC(x.exp) }, gap);
    y += 236;
    // changements par poste
    title('Changements de joueurs');
    const W = [84, 262, 64, 262, 64, 116], gp = (IW - W.reduce((a, b) => a + b, 0)) / 5, cx = [];
    W.reduce((px, w, i) => { cx[i] = px; return px + w + gp; }, L);
    const H3 = { px: 19, w: 600, c: 'ink-3' }, right = (i) => cx[i] + W[i];
    [['Poste', 0], ['Joueur actuel', 1], ['Valeur', 2, 1], ['Joueur attendu', 3], ['Valeur', 4, 1], ['Changement', 5, 1]].forEach(([s, i, r]) => P.text(s, r ? right(i) : cx[i], y + 4, r ? { ...H3, align: 'right' } : H3));
    y += 22;
    const cell = (o, i, yy, isNew, empty) => {
      if (o) {
        P.text(o.nm, cx[i], yy + 34, { px: 27, w: isNew ? 700 : 400, c: o.gone ? 'ink-3' : 'ink', max: W[i] });
        if (o.subTxt) P.text(o.subTxt, cx[i], yy + 62, { px: 20, c: 'ink-3', max: W[i] });
        P.text(fmt(o.val, 1), right(i + 1), yy + 36, { px: 34, w: 800, disp: 1, c: cardNoteC(o.val), align: 'right' });
      } else {
        P.text(empty, cx[i], yy + 34, { px: 27, c: 'ink-3', max: W[i] });
        if (empty !== '–') P.text(fmt(M.def, 1), right(i + 1), yy + 36, { px: 34, w: 800, disp: 1, c: 'ink-3', align: 'right' });
      }
    };
    M.cardRows.forEach((r) => {
      P.rect(L, y, IW, 1, 'line-2');
      P.text(r.r, cx[0], y + 34, { px: 21, w: 600, c: 'ink-3' });
      cell(r.cInfo, 1, y, false, '–'); cell(r.nInfo, 3, y, !r.same, 'pas encore annoncé');
      P.text(r.dv == null ? '—' : sgn(r.dv), right(5), y + 36, { px: 28, w: 700, c: r.dv == null ? 'ink-3' : cardDeltaC(dCls(r.dv)), align: 'right' });
      y += 84;
    });
    // rang parmi les équipes des ligues majeures
    title('Rang parmi les équipes des ligues majeures');
    cardPair(P, L, y, pw, { label: 'Rang actuel', num: M.gc != null ? String(M.gc) : '–', suf: M.gc != null ? (M.gc === 1 ? 'er' : 'e') : '', c: 'ink' },
      { label: `Rang attendu en ${N.season}`, num: String(M.ge), suf: M.ge === 1 ? 'er' : 'e', c: 'ink' }, cardMove(M.gc, M.ge));
    P.para(`${M.inMaj ? '' : `${LG} n'est pas une ligue majeure : le rang est celui qu'aurait l'équipe parmi les ${fmt(M.nMaj)} équipes de ligue majeure. `}Parmi ${fmt(M.nMaj)} équipes de ligue majeure : niveaux actuels pour le rang actuel, niveaux attendus pour le rang attendu.`, L + pw + 24, y + 34, pw, { px: 20, c: 'ink-2' }, 28, 6);
    y += 236;
    // chances de gagner une partie
    if (M.wins.length) {
      title('Chances de gagner une partie');
      const VR = [CARD_W - L - 340, CARD_W - L - 190, CARD_W - L], vr = (k) => VR[k];   // bords droits des trois colonnes de chiffres
      P.text('Contre', L, y + 4, H3);
      [`Effectif ${M.LAST}`, `Effectif ${N.season}`, 'Écart'].forEach((s, k) => P.text(s, vr(k), y + 4, { ...H3, align: 'right' }));
      y += 22;
      M.wins.forEach(({ o, p26, p27 }) => {
        P.rect(L, y, IW, 1, 'line-2');
        P.text(o.t.name, L, y + 34, { px: 27, w: 700, max: VR[0] - 120 - L });
        P.text(`niveau attendu ${fmt(o.exp, 1)}`, L, y + 60, { px: 20, c: 'ink-3' });
        P.text(p26 != null ? pctPt(p26) : '–', vr(0), y + 38, { px: 28, c: 'ink-2', align: 'right' });
        P.text(pctPt(p27), vr(1), y + 38, { px: 28, w: 700, align: 'right' });
        P.text(p26 != null ? pts(p27 - p26) : '–', vr(2), y + 38, { px: 28, w: 700, c: p26 != null ? cardDeltaC(dCls((p27 - p26) * 100)) : 'ink-3', align: 'right' });
        y += 76;
      });
      y += 4;
      P.para(`Contre les trois meilleures autres équipes de ${LG} en niveau attendu ${N.season}${x.re <= 3 ? ' (l\'équipe est dans le top 3 : la quatrième équipe complète la liste)' : ''}.`, L, y + 26, IW, { px: 20, c: 'ink-3' }, 28);
      y += 54;
    }
    y += 24;
    return cardFoot(P, y, [M.mention, `Effectifs annoncés : ${N.source}.`], `Calcul : ${CALC_NAME[state.calc]}`);
  }

  function drawPlayerCard(P, M) {
    const L = CARD_PAD, IW = CARD_W - 2 * L, { p, m } = M, to = D.seasons[M.season].to;
    P.fill();
    // en-tête : note en très gros, puis nom, poste, équipe, ligue, rang
    const NOTE = 220, nc = cardNoteC(p.note), ns = nInt(p.note) + '';
    const nw = P.width(ns, { px: NOTE, w: 900, disp: 1 }), tx = L + nw + 44;
    const info = [`${p.role}, ${p.team}`, `${lgName(p.league)} (${p.region}), saison ${M.season}`, `${ordTxt(M.rankIn)} des ${M.grp}`];
    const bandH = 10 + 44 + Math.max(NOTE * 0.74, 80 + 18 + info.length * 36) + 40;
    P.rect(0, 0, CARD_W, bandH, 'paper'); P.rect(0, bandH - 1, CARD_W, 1, 'line'); cardStripe(P);
    P.text(ns, L, 10 + 44 + NOTE * 0.72, { px: NOTE, w: 900, disp: 1, c: nc });
    P.text(p.name, tx, 10 + 44 + 66, { px: 84, w: 900, disp: 1, max: CARD_W - L - tx });
    info.forEach((l, i) => P.text(l, tx, 10 + 44 + 66 + 18 + 26 + i * 36, { px: 26, c: i === 2 ? 'ink' : 'ink-2', w: i === 2 ? 600 : 400, max: CARD_W - L - tx }));
    let y = bandH;
    const title = (s) => { y += 56; P.text(s, L, y, { px: 30, w: 700 }); y += 22; };
    // niveau de l'équipe, écart individuel, parties, victoires
    y += 32;
    const cw = IW / 4, cells = [['Niveau de son équipe', nInt(p.team_lvl) + '', 'ink'], ['Écart individuel', (p.ind >= 0 ? '+' : '') + fmt(p.note - p.team_lvl, 1), p.ind >= 0 ? 'teal' : 'rose'],
      ['Parties jouées', p.n + '', 'ink'], ['Part de victoires', pctTxt(p.st.win), 'ink']];
    P.panel(L, y, IW, 190);
    cells.forEach(([lab, v, c], i) => {
      const cxx = L + i * cw + 24;
      if (i) P.rect(L + i * cw, y + 20, 1, 150, 'line-2');
      P.lines(lab, cw - 40, { px: 20, c: 'ink-3' }, 2).forEach((l, k) => P.text(l, cxx, y + 42 + k * 25, { px: 20, c: 'ink-3' }));
      P.big(v, cxx, y + 150, cw - 40, 92, c);
    });
    y += 190;
    // facettes
    title('Profil par facette');
    const lx = L, bx = L + 250, bw = 560, nx = CARD_W - L;
    FAC.forEach((f, i) => {
      const v = p.f[i]; if (v == null) return;
      P.text(fLabel(f, p.role), lx, y + 32, { px: 24, max: 236 });
      P.bar(bx, y + 17, bw, v, m.f[i]);
      P.text(nInt(v) + '', nx, y + 40, { px: 38, w: 800, disp: 1, c: cardNoteC(v), align: 'right' });
      y += 52;
    });
    y = P.para(`Trait : médiane des ${M.grp}.`, L, y + 28, IW, { px: 20, c: 'ink-3' }, 28);
    // événements entre ligues
    const evs = p.ev.filter((e) => e.sc === 'monde' || e.sc === 'region').slice(0, 6);
    if (evs.length) {
      title('Notes des événements entre ligues');
      evs.forEach((e) => {
        P.text(e.e, lx, y + 30, { px: 24, w: 600, max: 236 });
        P.text(`${e.n} parties, ${pctTxt(e.w)} vict.`, lx, y + 54, { px: 19, c: 'ink-3', max: 236 });
        P.bar(bx, y + 22, bw, e.note, p.note);
        P.text(nInt(e.note) + '', nx, y + 46, { px: 38, w: 800, disp: 1, c: cardNoteC(e.note), align: 'right' });
        y += 66;
      });
      y = P.para('Trait : sa note sur la saison. Avec peu de parties, la note d\'un événement reste incertaine.', L, y + 28, IW, { px: 20, c: 'ink-3' }, 28);
    }
    y += 24;
    return cardFoot(P, y, [], `Calcul : ${CALC_NAME[state.calc]} · données au ${cDate(to, true)}`);
  }

  function saveCanvas(cv, file) {
    const fallback = () => {   // pas de toBlob, ou échec : l'image s'ouvre dans un nouvel onglet
      const w = window.open('', '_blank'); if (!w) return;
      const im = w.document.createElement('img'); im.src = cv.toDataURL('image/png'); im.alt = file; im.style.maxWidth = '100%';
      w.document.title = file; w.document.body.style.margin = '0'; w.document.body.appendChild(im);
    };
    if (!cv.toBlob) return fallback();
    try {
      cv.toBlob((blob) => {
        if (!blob) return fallback();
        const url = URL.createObjectURL(blob), a = document.createElement('a');
        a.href = url; a.download = file; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
      }, 'image/png');
    } catch (e) { fallback(); }
  }
  async function downloadCard(btn) {
    const c = card; if (!c || btn.disabled) return;
    btn.disabled = true;
    try {
      await cardFonts();
      const C = cardPalette(), draw = c.kind === 'team' ? drawTeamCard : drawPlayerCard;
      const H = Math.ceil(draw(cardPen(document.createElement('canvas').getContext('2d'), C), c));   // première passe : mesure la hauteur
      const cv = document.createElement('canvas'); cv.width = CARD_W * CARD_SCALE; cv.height = H * CARD_SCALE;
      const ctx = cv.getContext('2d'); ctx.scale(CARD_SCALE, CARD_SCALE);
      draw(cardPen(ctx, C, H), c);
      saveCanvas(cv, c.file);
    } finally { btn.disabled = false; }
  }

  /* ------------------------------------------------------------ méthode */
  function renderMethod() {
    const w = D.weights;
    $('#wtable').innerHTML = '<tr><th>Facette</th>' + ROLES.map((r) => `<th>${r}</th>`).join('') + '</tr>' +
      FAC.map((f) => `<tr><td>${FLABEL[f]}${f === 'lane' ? ' (jungle : avance à 15 min)' : ''}</td>${ROLES.map((r) => `<td>${w[r][f] ? fmt(w[r][f] * 100) + ' %' : '–'}</td>`).join('')}</tr>`).join('');
    const L = Object.entries(S.leagues).filter(([l]) => S.players.some((p) => p.league === l)).sort((a, b) => b[1] - a[1]);
    $('#lgs').innerHTML = L.map(([l, v]) => `<div class="lg"><span>${h(l)}</span><span class="bar"><i style="width:${Math.max(2, (v - 30) / 69 * 100)}%;background:${noteVar(v)}"></i></span><b>${nInt(v)}</b></div>`).join('');
    $('#m-season').textContent = state.season;
    $('#m-meta').textContent = D.meta ? `${D.meta.matched} joueurs de la saison ${D.meta.season} y sont reliés.` : '';
    $('#m-contracts').textContent = CT ? `${CT.matched} joueurs de la saison ${CT.season} y sont reliés (relevé du ${cDate(CT.fetched, true)}). Un contrat qui se termine avant le ${cDate(CT.free_until, true)} est compté comme une fin de contrat.` : '';
  }

  /* ------------------------------------------------------------ événements d'interface */
  function render() {
    document.querySelectorAll('.tabs button').forEach((b) => b.setAttribute('aria-selected', b.dataset.view === state.view));
    document.querySelectorAll('.view').forEach((v) => (v.hidden = v.id !== 'view-' + state.view));
    document.querySelectorAll('#season button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.season === state.season));
    if (state.view === 'rank') renderRank(); else if (state.view === 'scout') renderScout(); else if (state.view === 'power') renderPower(); else if (state.view === 'transfers') renderTransfers(); else renderMethod();
  }
  function init() {
    $('#season').innerHTML = Object.keys(D.seasons).sort().map((y) => `<button data-season="${y}">${y}</button>`).join('');
    try { const c = localStorage.getItem('rs-calc'); if (c === 'mix' || c === 'rift' || c === 'uni') state.calc = c; } catch (e) { /* stockage indisponible */ }
    applyCalc();
    load(); fillSelects();
    document.addEventListener('click', (e) => {
      const b = e.target.closest('button,[data-p]'); if (!b) { if (e.target.classList.contains('scrim')) closeSheet(); return; }
      if (b.dataset.try) { const p = byId.get(b.dataset.try), pl = state.sc.plan; if (pl[p.role] === p.id) delete pl[p.role]; else pl[p.role] = p.id; state.sc.role = p.role; closeSheet(); renderScout(); return; }
      if (b.dataset.untry) { if (b.dataset.untry === 'all') state.sc.plan = {}; else delete state.sc.plan[b.dataset.untry]; renderScout(); return; }
      if (b.dataset.view) { state.view = b.dataset.view; render(); window.scrollTo(0, 0); }
      else if (b.dataset.calc) { state.calc = b.dataset.calc; try { localStorage.setItem('rs-calc', state.calc); } catch (e) { /* stockage indisponible */ } applyCalc(); load(); render(); }
      else if (b.dataset.season) { state.season = b.dataset.season; lgCache = {}; state.sc.plan = {}; state.sc.tid = null; state.sc.ref = null; $('#team-input').value = ''; load(); fillSelects(); render(); }
      else if (b.dataset.scout) { if (savedSeason) { savedSeason = null; lgCache = {}; fillSelects(); } const p = byId.get(b.dataset.scout); closeSheet(); state.view = 'scout'; state.sc.plan = {}; state.sc.role = p.role; state.sc.ref = p.id; const t = S.teams.find((x) => x.roster[p.role] === p.id); state.sc.tid = t ? t.tid : null; if (!t) $('#team-input').value = ''; render(); window.scrollTo(0, 0); }
      else if (b.dataset.card !== undefined) downloadCard(b);
      else if (b.dataset.tm !== undefined) openTeamSheet(+b.dataset.tm);
      else if (b.dataset.p) { if (state.view === 'transfers') openLast(b.dataset.p); else openSheet(b.dataset.p, b.dataset.cmp); }
      else if (b.hasAttribute('data-close')) closeSheet();
      else if (b.dataset.tid) { $('#suggest').hidden = true; setTeam(b.dataset.tid); }
      else if (b.dataset.scmode) { state.sc.mode = b.dataset.scmode; renderScout(); }
      else if (b.id === 'crack-more') { state.sc.cr.shown += 60; renderScout(); }
      else if (b.closest('#c-roles')) { state.sc.cr.role = b.dataset.role; state.sc.cr.shown = 60; renderScout(); }
      else if (b.dataset.lgmode) { state.basis = b.dataset.lgmode; state.shown = 100; renderRank(); }
      else if (b.id === 'p-more') { state.pw.shown += 100; renderPower(); }
      else if (b.dataset.pbasis) { state.pw.basis = b.dataset.pbasis; state.pw.shown = 100; renderPower(); }
      else if (b.id === 'more') { state.shown += 100; renderRank(); }
      else if (b.id === 'scout-more') { state.sc.shown += 60; renderScout(); }
      else if (b.id === 'reset') { Object.assign(state, { role: '', tier: '0', region: '', league: '', event: '', contract: '', basis: 'season', minG: 15, q: '', shown: 100 }); syncFilters(); fillSelects(); renderRank(); }
      else if (b.id === 'clear-team') { state.sc.plan = {}; state.sc.tid = null; state.sc.ref = null; $('#team-input').value = ''; renderScout(); }
      else if (b.closest('#f-roles')) { state.role = b.dataset.role; state.shown = 100; syncFilters(); renderRank(); }
      else if (b.closest('#s-roles') || b.closest('#lineup')) { state.sc.role = b.dataset.role; state.sc.ref = null; state.sc.shown = 60; renderScout(); }
    });
    const bind = (id, fn) => $(id).addEventListener('input', (e) => { fn(e.target.value); state.shown = 100; state.sc.shown = 60; state.view === 'rank' ? renderRank() : renderScout(); });
    bind('#f-tier', (v) => { state.tier = v; }); bind('#f-region', (v) => { state.region = v; if (v) { state.league = ''; $('#f-league').value = ''; } });
    bind('#f-league', (v) => { state.league = v; if (!state.event && state.basis === 'only') state.basis = 'season'; if (v) { state.tier = ''; state.region = ''; syncFilters(); } });
    bind('#f-event', (v) => { state.event = v; if (state.basis !== 'recent' || !v) state.basis = v ? 'only' : (state.basis === 'recent' ? 'recent' : 'season'); if (v) { state.tier = ''; state.minG = 0; syncFilters(); } else { state.minG = 15; state.tier = '0'; syncFilters(); } });
    bind('#f-contract', (v) => { state.contract = v; }); bind('#s-contract', (v) => { state.sc.contract = v; });
    bind('#s-age', (v) => { state.sc.maxAge = +v || 0; }); bind('#s-res', (v) => { state.sc.res = v; });
    bind('#f-min', (v) => { state.minG = +v || 0; }); bind('#f-q', (v) => { state.q = v; });
    bind('#s-tier', (v) => { state.sc.tier = v; }); bind('#s-region', (v) => { state.sc.region = v; }); bind('#s-league', (v) => { state.sc.league = v; });
    bind('#s-sort', (v) => { state.sc.sort = v; }); $('#s-reach').addEventListener('change', (e) => { state.sc.reach = e.target.checked; state.sc.shown = 60; renderScout(); });
    bind('#s-note', (v) => { state.sc.minNote = +v || 0; }); bind('#s-min', (v) => { state.sc.minG = +v || 0; });
    const pwBind = (id, fn) => $(id).addEventListener('input', (e) => { fn(e.target.value); state.pw.shown = 100; renderPower(); });
    pwBind('#p-tier', (v) => { state.pw.tier = v; state.pw.league = ''; }); pwBind('#p-region', (v) => { state.pw.region = v; state.pw.league = ''; });
    pwBind('#p-league', (v) => { state.pw.league = v; if (v) { state.pw.tier = ''; state.pw.region = ''; } });
    $('#t-league').addEventListener('input', (e) => { state.tr.league = e.target.value; renderTransfers(); });
    const cr = state.sc.cr;
    bind('#c-age', (v) => { cr.maxAge = +v || 22; }); bind('#c-region', (v) => { cr.region = v; }); bind('#c-min', (v) => { cr.minG = +v || 0; }); bind('#c-contract', (v) => { cr.contract = v; });
    [['#c-deep', 'deep'], ['#c-fresh', 'fresh'], ['#c-all', 'all'], ['#c-noage', 'noAge']].forEach(([id, k]) => $(id).addEventListener('change', (e) => { cr[k] = e.target.checked; cr.shown = 60; renderScout(); }));
    $('#team-input').addEventListener('input', (e) => suggest(e.target.value));
    $('#team-input').addEventListener('focus', (e) => { e.target.select(); });
    document.addEventListener('keydown', (e) => { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('div.row[data-p]')) { e.preventDefault(); openSheet(e.target.dataset.p, e.target.dataset.cmp); }
      if (e.key === 'Escape') { closeSheet(); $('#suggest').hidden = true; } });
    syncFilters(); render();
  }
  function syncFilters() {
    $('#f-tier').value = state.tier; $('#f-region').value = state.region; $('#f-league').value = state.league; $('#f-min').value = state.minG; $('#f-q').value = state.q; $('#f-event').value = state.event;
    $('#f-roles').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.role === state.role));
  }
  init();
})();
