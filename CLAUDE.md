# Rift Scout

Notes de 1 à 100 pour les joueurs professionnels de League of Legends, fiches joueurs et outil de scouting. Une seule page statique, publiée par GitHub Pages depuis `docs/`. Lire `PRODUCT.md` avant tout changement de méthode ou d'interface.

## Structure

- `pipeline/build.py` : tout le calcul. Lit les CSV d'Oracle's Elixir, écrit `app/data.json`. Les réglages (poids des facettes par poste, régularisation, échelle) sont en tête du fichier.
- `pipeline/fetch_data.py` : télécharge les CSV de matchs dans `data/raw/`.
- `pipeline/fetch_contracts.py` : télécharge la base publique de contrats de Riot, écrit `pipeline/contracts.json`.
- `pipeline/leaguepedia.py`, `pipeline/fetch_leaguepedia.py` : connexion à Leaguepedia et récupération des fiches joueurs (`pipeline/lp_players.json` : âge, pays, résidence, contrat) et de la couverture des données détaillées (`pipeline/lp_coverage.json`). Demandent `LEAGUEPEDIA_USER` et `LEAGUEPEDIA_PASSWORD`, présents seulement dans les secrets GitHub : ces scripts se lancent par le workflow « Leaguepedia », pas en local.
- `pipeline/fetch_timelines.py` : chronologies des parties hors LPL, réduites à quelques mesures par joueur (morts inutiles, objectifs, proximité du jungler) dans `pipeline/lp_timeline_<année>.csv.gz`. Se lance par le workflow « Chronologies Leaguepedia », reprend où il s'est arrêté. Utilisé par `build.py` quand le fichier de la saison existe (morts inutiles dans « Survie », présence dans « Objectifs », weakside/strongside, style) ; sans lui, ou pour une partie de LPL, le calcul retombe sur les stats de base avec les mêmes proportions. La clé `gameid` + `pid` correspond à `gameid` + `participantid` d'Oracle's Elixir.
- `pipeline/leagues.json` : niveau de départ, région et noms des ligues.
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

`.github/workflows/update.yml` relance tout chaque mardi à 05:17 UTC (ou à la demande depuis l'onglet Actions) et committe `docs/index.html` et `pipeline/contracts.json`. `pipeline/check.py` bloque la publication si le résultat est manifestement cassé. Si Google Drive refuse le téléchargement, la mise à jour est reportée sans erreur.

À chaque nouvelle saison, il faut ajouter à la main : l'identifiant du fichier dans `pipeline/fetch_data.py`, l'année dans `SEASONS` (`pipeline/build.py`) et les niveaux de ligue de départ dans `pipeline/leagues.json`.

## Règles

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
