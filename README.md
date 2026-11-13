# Rift Scout

Les meilleurs joueurs professionnels de League of Legends, notés de 1 à 100 sur une échelle commune à toutes les ligues, et un outil de scouting par poste et par style de jeu.

La page est un seul fichier : `docs/index.html` (ouvrable directement dans un navigateur, publiable tel quel sur GitHub Pages).

## Ce que fait l'appli

- **Classement** : le meilleur cinq et le classement complet, filtrables par poste, niveau de ligue, région, ligue et événement (Worlds, MSI, un split…), saisons 2025 et 2026.
- **Fiche joueur** : note générale, niveau de l'équipe et écart individuel, forme récente, forces et points faibles rédigés, huit facettes (lane, début de partie, teamfight, dégâts, farm et or, vision, survie, objectifs), weakside et strongside, note par événement, champions, joueurs au style proche.
- **Scouting** : on choisit une équipe et un poste ; les candidats sont classés par note, par ressemblance de style avec le titulaire et par ce qu'ils apportent aux quatre autres joueurs.
- **Contrats** : date de fin de contrat sur chaque joueur, filtre « en fin de contrat » dans le classement et le scouting, tri par fin de contrat la plus proche. Source : la [base publique des contrats reconnus par Riot](https://docs.google.com/spreadsheets/d/1Y7k5kQ2AegbuyiGwEPsa62e883FYVtHqr6UVut9RC4o/pubhtml).
- **Avant et après** : dans le scouting, on essaie un ou plusieurs joueurs dans une équipe et on compare l'effectif obtenu à l'actuel (niveau, chances de victoire, rang estimé dans la ligue, profil par facette).
- **Âge, nationalité, résidence** : sur la fiche et en filtres dans le scouting (source : Leaguepedia).
- **Méthode** : le calcul expliqué, les poids par poste, le niveau des ligues.

## La note

`note = niveau de l'équipe + écart individuel`

1. **Niveau de l'équipe.** Un modèle de victoire (Bradley-Terry régularisé) sur toutes les parties de la saison. Chaque équipe part du niveau de sa ligue ; les tournois internationaux recalent les ligues entre elles.
2. **Stats par partie.** Chaque stat est comparée aux joueurs du même poste dans la même compétition, après correction du champion joué, puis regroupée en huit facettes.
3. **Écart individuel.** On retire de chaque facette ce que l'écart de niveau entre les deux équipes explique. Le reste, pondéré selon le poste, est l'écart individuel. Son poids face au niveau d'équipe est calé sur les données : un écart-type d'écart individuel vaut environ 100 points de niveau, ce que donne la relation mesurée entre stats et écart de niveau.
4. **Échelle.** 80 = joueur médian des ligues majeures ; les tout meilleurs approchent 97.

Les réglages (poids des facettes, régularisation) sont en tête de `pipeline/build.py`.

## Lancer

```bash
pip install -r requirements.txt
```

```bash
python pipeline/fetch_data.py
```

```bash
python pipeline/fetch_contracts.py
```

```bash
python pipeline/build.py data/raw
```

```bash
python build_page.py
```

`fetch_contracts.py` met à jour `pipeline/contracts.json` (ligue, équipe, pseudo, poste, date de fin ; ni noms civils ni contacts). `build.py` écrit `app/data.json` ; `build_page.py` assemble `app/` en `docs/index.html`.

## Mise à jour automatique

Un workflow GitHub Actions (`.github/workflows/update.yml`) retélécharge les matchs et les contrats chaque mardi, recalcule les notes et republie la page. Il peut aussi être lancé à la main depuis l'onglet Actions.

## Limites connues

- Une **fin de contrat** proche ne dit pas si le joueur a prolongé ou déjà signé ailleurs. Les joueurs absents de la base de Riot (surtout les ligues de deuxième et troisième niveau) apparaissent comme « non renseigné ».
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs ; seules les stats individuelles les départagent.
- Weakside et strongside reposent sur la position du jungler relevée une fois par minute (chronologies Leaguepedia) : une bonne mesure, pas un suivi continu. La LPL n'a pas de chronologie ; ses joueurs sont notés sans morts inutiles, sans présence sur les objectifs, et leur weakside est approché par les kills avant 15 minutes.
- Les niveaux de ligue de départ (`pipeline/leagues.json`) viennent de LoL Ratings 3.0 ; pour une nouvelle saison il faut les reconduire ou les recalculer.

Données : [Oracle's Elixir](https://oracleselixir.com/tools/downloads).
