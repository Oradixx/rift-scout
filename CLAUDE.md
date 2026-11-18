# Rift Scout

Notes de 1 à 100 pour les joueurs professionnels de League of Legends, fiches joueurs et outil de scouting. Une seule page statique, publiée par GitHub Pages depuis `docs/`. Lire `PRODUCT.md` avant tout changement de méthode ou d'interface.

## Structure

- `pipeline/build.py` : tout le calcul. Lit les CSV d'Oracle's Elixir, écrit `app/data.json`. Les réglages sont en tête du fichier : poids des facettes par poste (`WEIGHTS_HAND` choisis à la main, puis `WEIGHTS` = dégâts et vision ×2, survie ×0,5, validé sur les transferts), écart d'or dans le niveau d'équipe (`GOLD_WEIGHT`, marge d'incertitude `R_se` exportée), régularisation (`K_SHRINK`, `SD_TEAM`, `SD_TEAM_BY_LEAGUE` pour la LCK et la LPL, `SD_LEAGUE`, `SD_EVENT`), échelle fixe (`SCALE_A`, `SCALE_B`), seuil de découpage des tournois et des ligues (`QUALIF_GAP_DAYS`), période récente prudente (`SD_RECENT`, `K_RECENT_IND`), équipes remaniées (`ROSTER_MIN_STARTERS`), comparaison par groupe de niveau (`GROUP_CONTEXT`, désactivée). Chaque réglage non évident a un commentaire qui dit comment il a été choisi.
- Notes sur une partie des parties d'un joueur (forme sur 15 parties, période récente, note par équipe, par ligue, par événement) : toutes passent par les mêmes fonctions de `build.py` (`window_notes`, `event_table`, `league_table`, `tier_table`, `stint_table`) ; en ajouter une passe par là, pas par un calcul à part.
- Identités dans `build.py` : `load()` réunit une équipe enregistrée sous deux identifiants (même nom, même ligue) ; `season()` réunit un joueur sous deux identifiants et sépare les équipes remaniées, dont l'identifiant porte le suffixe `REMANIEE` (`#remaniee`). Ce suffixe ne doit jamais apparaître sur la page : la liste des équipes l'exclut, le parcours d'un joueur et la mention « puis … » le retirent. Tout nouvel usage de `tid` côté affichage doit faire de même.
- `tools/bench_team_levels.py` : banc d'essai des variantes du niveau d'équipe (validation croisée, playoffs cachés, matchs entre ligues majeures cachés). L'utiliser avant de changer le modèle de niveau d'équipe.
- `tools/bench_transfers.py` : le test des transferts (notes d'une saison, matchs de la saison suivante des effectifs remaniés ; protocole en tête du fichier). Juge tout changement du partage équipe / individuel ou de la note. Paires 2024 → 2025 et 2025 → 2026 pour régler ; 2023 → 2024 seulement en contrôle final, réglage figé. Calcule 2023 et 2024 avec leurs propres niveaux de ligue de départ (moyenne des points LoL Ratings par ligue) et leurs ligues majeures de l'époque : il lit pour cela `results/ratings_<année>.csv` et `src/leagues.py` du dépôt LoL-ratings cloné à côté (ou dans la variable `LOL_RATINGS`). Une méthode = une fonction (saison calculée, année) -> note par joueur.
- `pipeline/unified.py` : note unifiée (`nu`, marge `nue`), troisième calcul du bouton. Un seul modèle joueur par joueur : victoire et écart d'or de chaque partie = somme des niveaux des dix joueurs + côté ; niveau de départ tiré des statistiques (indice `Z` de `season()`), corrigé par les résultats. Réglages dans `DEFAULT` (`KAPPA`, `TAU`, réglés sur `tools/bench_transfers.py`) ; options essayées et éteintes : jeu collectif (`omega`), duels de lane (`lane_weight`), demi-vie (`half_life`). Marge affichée (`nue`) = bruit de mesure `NOISE_C` / √parties, mesuré et vérifié d'une saison à l'autre par `tools/check_margins.py` ; l'écart-type a posteriori (`se`) n'est pas affiché.
- `pipeline/fetch_data.py` : télécharge les CSV de matchs dans `data/raw/`.
- `pipeline/fetch_contracts.py` : télécharge la base publique de contrats de Riot, écrit `pipeline/contracts.json`.
- `pipeline/leaguepedia.py`, `pipeline/fetch_leaguepedia.py` : connexion à Leaguepedia et récupération des fiches joueurs (`pipeline/lp_players.json` : âge, pays, résidence, contrat) et de la couverture des données détaillées (`pipeline/lp_coverage.json`). Demandent `LEAGUEPEDIA_USER` et `LEAGUEPEDIA_PASSWORD`, présents seulement dans les secrets GitHub : ces scripts se lancent par le workflow « Leaguepedia », pas en local.
- `pipeline/fetch_timelines.py` : chronologies des parties hors LPL, réduites à quelques mesures par joueur (morts inutiles, objectifs, proximité du jungler) dans `pipeline/lp_timeline_<année>.csv.gz` (2025 et 2026 complets). Se lance par le workflow « Chronologies Leaguepedia », reprend où il s'est arrêté. Utilisé par `build.py` quand le fichier de la saison existe (morts inutiles dans « Survie », présence dans « Objectifs », weakside/strongside, style) ; sans lui, ou pour une partie de LPL, le calcul retombe sur les stats de base avec les mêmes proportions. La clé `gameid` + `pid` correspond à `gameid` + `participantid` d'Oracle's Elixir.
- `pipeline/fetch_lp_games.py` : parties absentes d'Oracle's Elixir (petites ligues de clubs, parties trop récentes), récupérées sur Leaguepedia (fichier de stats Riot et chronologie) et converties au format d'Oracle's Elixir dans `pipeline/lp_games_<année>.csv.gz`. Workflow « Parties Leaguepedia » (manuel, avec `verification` : parties de LEC converties dans `lp_games_check_<année>.csv.gz`, à comparer avec `tools/check_lp_games.py`) et étape de la mise à jour hebdomadaire. Lu par `add_lp_games()` dans `build.py` : Oracle's Elixir prioritaire pour une même partie ; joueurs reliés par le pseudo, et pour une petite ligue seulement via une ligue voisine (`NEIGHBOR`) ; précisions « (… Team) » retirées des noms d'équipe ; or gagné recalculé. Pour ajouter une ligue : `LP_LEAGUES` (script), `leagues.json` (région, niveau de départ, `tier3`), `PRETTY` et `NEIGHBOR` (`build.py`).
- `pipeline/lr_ratings_<année>.csv` : points de saison de LoL Ratings (identifiant et points seulement, repris de `results/ratings_<année>.csv` du dépôt LoL-ratings ; la mise à jour hebdomadaire les retélécharge). Servent à la note mixte (`nm`) : moitié note Rift Scout, moitié LoL Ratings ramené à l'échelle de la note. Côté page, le bouton « Rift Scout / Mixte / Unifiée » (`applyCalc()` dans `app.js`, `nm` ou `nu`) remplace la note de saison (et `pts`) partout ; les autres notes restent Rift Scout ; la teinte passe du cobalt au vert sapin en mode mixte (`:root[data-calc="mix"]`) et au prune en mode unifié (`:root[data-calc="uni"]`), clair et sombre.
- `pipeline/rosters_next.json` : effectifs annoncés pour la saison suivante, relevés à la main sur Sheep Esports (le site refuse les scripts), par ligue puis par équipe (nom de la saison en cours), pseudos seulement ; `null` = poste pas encore annoncé. Lu par `next_rosters()` dans `build.py` (`D.next`), affiché dans l'onglet « Transferts » (`renderTransfers()`). Une équipe absente du fichier garde son effectif actuel, signalée non annoncée. Ne sont comptées que les équipes du dernier segment de leur ligue (`end` sur chaque équipe : Los Ratones, invitée en LEC Winter 2026 seulement, n'y est pas) ; le même drapeau filtre l'onglet « Power ranking » (`renderPower()`).
- `tools/bench_rosters.py` : validation du power ranking attendu (effectifs d'ouverture de N+1 jugés avec les notes de N). Règle retenue, reprise dans `app.js` : moyenne des cinq notes, note de deuxième ou troisième niveau convertie par la droite `proj`, joueur sans note ou poste non annoncé au 25e centile des titulaires de la ligue.
- `pipeline/leagues.json` : niveau de départ, région et noms des ligues.
- `pipeline/check.py` : garde-fou avant publication, compare aussi au `docs/index.html` déjà publié.
- `app/` : sources de la page (`index.template.html`, `style.css`, `app.js`). Le scouting a deux onglets : « Renforcer une équipe » et « Cracks à essayer » (`cracks()`, `renderCracks()` : jeunes des ligues inférieures, note de deuxième niveau convertie en note estimée en ligue majeure par la droite `proj` calculée dans `build.py`, mélangée partie pour partie aux parties déjà jouées en ligue majeure ; seuils sur les titulaires de la ligue majeure de la région). La note par niveau de ligue (`tr`, depuis `tier_table`) sert aussi au classement et au scouting quand un niveau est choisi : un joueur de passage y figure avec sa note sur ces seules parties, signalée sur la ligne.
- `build_page.py` : assemble `app/` et `app/data.json` en `docs/index.html`.

## Commandes

```bash
pip install -r requirements.txt        # pandas < 3 : pandas 3 casse build.py
python pipeline/fetch_data.py          # CSV de matchs -> data/raw/ (environ 80 Mo par saison)
python pipeline/fetch_contracts.py     # contrats -> pipeline/contracts.json
python pipeline/build.py data/raw      # -> app/data.json
python pipeline/check.py               # garde-fou sur le résultat
python build_page.py                   # -> docs/index.html
python tools/bench_transfers.py        # test des transferts, 2024 -> 2025 et 2025 -> 2026 (environ 1 minute)
```

Google Drive refuse souvent les téléchargements par script (quota). Les fichiers d'Oracle's Elixir 2022-2026 (relevé du 14 novembre 2026) sont aussi sur la branche `donnees-oe`, compressés :

```bash
mkdir -p data/raw
for f in 2023 2024 2025 2026; do
  curl -sL "https://raw.githubusercontent.com/Oradixx/rift-scout/donnees-oe/${f}_LoL_esports_match_data_from_OraclesElixir.csv.gz" | gunzip > "data/raw/${f}_LoL_esports_match_data_from_OraclesElixir.csv"
done
```

Avec ces fichiers, `build.py` doit afficher « 2026 : 1122 parties ajoutées depuis Leaguepedia » et « 2026 joueurs 2264 ».

## Mise à jour automatique

`.github/workflows/update.yml` relance tout chaque mardi à 05:17 UTC (ou à la demande depuis l'onglet Actions) et committe `docs/index.html`, `pipeline/contracts.json` et les fichiers Leaguepedia (fiches joueurs, chronologies des nouvelles parties). `pipeline/check.py` bloque la publication si le résultat est manifestement cassé, ou s'il s'écarte en bloc de la page déjà publiée (parties perdues, notes déplacées de plus de 2 points en médiane) : après un changement voulu du calcul, publier à la main. Si Google Drive refuse le téléchargement, la mise à jour est reportée sans erreur. État au 14 novembre 2026 : la mise à jour n'a jamais tourné de bout en bout (bloquée par le quota Google Drive au seul essai) ; le premier passage réussi est à surveiller. Le téléchargement passe l'identifiant du fichier à gdown sans `--fuzzy` (option supprimée dans gdown 6, qui cassait la mise à jour de LoL Ratings). Page publiée avec les données du 13 novembre 2026 (Worlds jusqu'aux demi-finales).

Les chronologies d'une saison complète se téléchargent avec le workflow « Chronologies Leaguepedia » (année, durée maximale ; environ 2 h 20 pour une saison, reprise automatique). La mise à jour hebdomadaire ne télécharge que celles des nouvelles parties.

À chaque nouvelle saison, il faut recaler l'échelle (`SCALE_A`, `SCALE_B` dans `pipeline/build.py`, d'après la ligne « échelle fixe » affichée par le calcul) et ajouter à la main : l'identifiant du fichier dans `pipeline/fetch_data.py`, l'année dans `SEASONS` (`pipeline/build.py`) et les niveaux de ligue de départ dans `pipeline/leagues.json`.

## Règles

- Lire « Ce qui a été testé et écarté » dans `PRODUCT.md` avant de changer le calcul : plusieurs ressentis (groupes de niveau, joueurs occidentaux, bas de la LCK, supports engage) ont déjà été testés sans justifier de correction.
- Un changement du calcul se valide sur des données qu'il n'a pas vues (validation croisée sur les parties, joueurs transférés avec `tools/bench_transfers.py`, matchs internationaux), pas seulement en regardant le classement.
- À filtres égaux, une note ne doit jamais changer à cause d'une modification de l'interface. Après un changement d'affichage, comparer la page à la version précédente (joueurs, notes, nombres de parties) sur plusieurs combinaisons de filtres.
- Annoncer à l'utilisateur toute variation de notes, avec son ampleur (médiane et maximum) et les joueurs qui bougent le plus.
- Une estimation qui n'est pas une note (comme celle de l'onglet Cracks) s'ajuste sur une saison et se valide sur une autre (joueurs montés l'année suivante), et s'affiche à part de la note, libellée comme une estimation.

- Ne jamais modifier `docs/index.html` à la main : il est généré. Modifier `app/` ou le pipeline, puis reconstruire et committer le `docs/index.html` obtenu.
- `data/` et `app/data.json` ne sont pas versionnés (trop lourds, régénérables). Sans eux la page publiée fonctionne quand même : ses données sont incluses dans `docs/index.html`.
- Leaguepedia : ne jamais demander ni stocker les noms civils ; on garde la date de naissance dans `lp_players.json` mais la page n'affiche que l'âge.
- Sans compte, Leaguepedia refuse les requêtes sur ses tables (limite partagée entre tous les anonymes).
- Contrats : ne garder que ligue, équipe, pseudo, poste et date de fin. Jamais de noms civils ni de contacts d'équipe, bien que la source en contienne.
- Après un changement du calcul, vérifier le classement par poste des ligues majeures avant de committer : il doit rester crédible pour quelqu'un qui suit la scène.
- Après un changement d'interface, ouvrir la page dans un navigateur (bureau, mobile, mode sombre) et vérifier qu'il n'y a ni erreur console ni défilement horizontal.

## Interface

- Texte en français, phrases en casse normale, libellés en langage courant. Un bouton dit ce qu'il fait.
- Direction visuelle : feuille de match sportive. Notes en gros chiffres condensés (Big Shoulders Display), texte en Hanken Grotesk, fond brume, encre marine, cobalt pour l'interactif, or réservé aux notes de 90 et plus.
- Couleurs uniquement par les variables CSS de `:root` (thèmes clair et sombre définis au même endroit).
- Pas d'étiquettes en majuscules espacées, pas de police à chasse fixe pour les chiffres, pas de cartes décoratives. Une seule animation : l'ouverture de la fiche joueur.
- Pour tout travail d'interface, utiliser le skill `frontend-design` s'il est disponible.
- JavaScript sans dépendance ni étape de compilation.
