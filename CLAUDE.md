# Rift Scout

Notes de 1 à 100 pour les joueurs professionnels de League of Legends, fiches joueurs et outil de scouting. Une seule page statique, publiée par GitHub Pages depuis `docs/`. Lire `PRODUCT.md` avant tout changement de méthode ou d'interface.

## Structure

- `pipeline/build.py` : tout le calcul. Lit les CSV d'Oracle's Elixir, écrit `app/data.json`. Les réglages sont en tête du fichier : poids des facettes par poste, régularisation (`K_SHRINK`, `SD_TEAM`, `SD_TEAM_BY_LEAGUE` pour la LCK et la LPL, `SD_LEAGUE`, `SD_EVENT`), échelle fixe (`SCALE_A`, `SCALE_B`), seuil de découpage des tournois et des ligues (`QUALIF_GAP_DAYS`), période récente prudente (`SD_RECENT`, `K_RECENT_IND`), équipes remaniées (`ROSTER_MIN_STARTERS`), comparaison par groupe de niveau (`GROUP_CONTEXT`, désactivée). Chaque réglage non évident a un commentaire qui dit comment il a été choisi.
- Notes sur une partie des parties d'un joueur (forme sur 15 parties, période récente, note par équipe, par ligue, par événement) : toutes passent par les mêmes fonctions de `build.py` (`window_notes`, `event_table`, `league_table`, `stint_table`) ; en ajouter une passe par là, pas par un calcul à part.
- Identités dans `build.py` : `load()` réunit une équipe enregistrée sous deux identifiants (même nom, même ligue) ; `season()` réunit un joueur sous deux identifiants et sépare les équipes remaniées, dont l'identifiant porte le suffixe `REMANIEE` (`#remaniee`). Ce suffixe ne doit jamais apparaître sur la page : la liste des équipes l'exclut, le parcours d'un joueur et la mention « puis … » le retirent. Tout nouvel usage de `tid` côté affichage doit faire de même.
- `pipeline/fetch_data.py` : télécharge les CSV de matchs dans `data/raw/`.
- `pipeline/fetch_contracts.py` : télécharge la base publique de contrats de Riot, écrit `pipeline/contracts.json`.
- `pipeline/leaguepedia.py`, `pipeline/fetch_leaguepedia.py` : connexion à Leaguepedia et récupération des fiches joueurs (`pipeline/lp_players.json` : âge, pays, résidence, contrat) et de la couverture des données détaillées (`pipeline/lp_coverage.json`). Demandent `LEAGUEPEDIA_USER` et `LEAGUEPEDIA_PASSWORD`, présents seulement dans les secrets GitHub : ces scripts se lancent par le workflow « Leaguepedia », pas en local.
- `pipeline/fetch_timelines.py` : chronologies des parties hors LPL, réduites à quelques mesures par joueur (morts inutiles, objectifs, proximité du jungler) dans `pipeline/lp_timeline_<année>.csv.gz` (2025 et 2026 complets). Se lance par le workflow « Chronologies Leaguepedia », reprend où il s'est arrêté. Utilisé par `build.py` quand le fichier de la saison existe (morts inutiles dans « Survie », présence dans « Objectifs », weakside/strongside, style) ; sans lui, ou pour une partie de LPL, le calcul retombe sur les stats de base avec les mêmes proportions. La clé `gameid` + `pid` correspond à `gameid` + `participantid` d'Oracle's Elixir.
- `pipeline/leagues.json` : niveau de départ, région et noms des ligues.
- `pipeline/check.py` : garde-fou avant publication, compare aussi au `docs/index.html` déjà publié.
- `app/` : sources de la page (`index.template.html`, `style.css`, `app.js`).
- `build_page.py` : assemble `app/` et `app/data.json` en `docs/index.html`.

## Commandes

```bash
pip install -r requirements.txt
python pipeline/fetch_data.py          # CSV de matchs -> data/raw/ (environ 80 Mo par saison)
python pipeline/fetch_contracts.py     # contrats -> pipeline/contracts.json
python pipeline/build.py data/raw      # -> app/data.json
python pipeline/check.py               # garde-fou sur le résultat
python build_page.py                   # -> docs/index.html
```

## Mise à jour automatique

`.github/workflows/update.yml` relance tout chaque mardi à 05:17 UTC (ou à la demande depuis l'onglet Actions) et committe `docs/index.html`, `pipeline/contracts.json` et les fichiers Leaguepedia (fiches joueurs, chronologies des nouvelles parties). `pipeline/check.py` bloque la publication si le résultat est manifestement cassé, ou s'il s'écarte en bloc de la page déjà publiée (parties perdues, notes déplacées de plus de 2 points en médiane) : après un changement voulu du calcul, publier à la main. Si Google Drive refuse le téléchargement, la mise à jour est reportée sans erreur. État au 14 novembre 2026 : la mise à jour n'a jamais tourné de bout en bout (bloquée par le quota Google Drive au seul essai) ; le premier passage réussi est à surveiller.

Les chronologies d'une saison complète se téléchargent avec le workflow « Chronologies Leaguepedia » (année, durée maximale ; environ 2 h 20 pour une saison, reprise automatique). La mise à jour hebdomadaire ne télécharge que celles des nouvelles parties.

À chaque nouvelle saison, il faut recaler l'échelle (`SCALE_A`, `SCALE_B` dans `pipeline/build.py`, d'après la ligne « échelle fixe » affichée par le calcul) et ajouter à la main : l'identifiant du fichier dans `pipeline/fetch_data.py`, l'année dans `SEASONS` (`pipeline/build.py`) et les niveaux de ligue de départ dans `pipeline/leagues.json`.

## Règles

- Lire « Ce qui a été testé et écarté » dans `PRODUCT.md` avant de changer le calcul : plusieurs ressentis (groupes de niveau, joueurs occidentaux, bas de la LCK, supports engage) ont déjà été testés sans justifier de correction.
- Un changement du calcul se valide sur des données qu'il n'a pas vues (validation croisée sur les parties, joueurs transférés, matchs internationaux), pas seulement en regardant le classement.
- À filtres égaux, une note ne doit jamais changer à cause d'une modification de l'interface. Après un changement d'affichage, comparer la page à la version précédente (joueurs, notes, nombres de parties) sur plusieurs combinaisons de filtres.
- Annoncer à l'utilisateur toute variation de notes, avec son ampleur (médiane et maximum) et les joueurs qui bougent le plus.

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
