# Rift Scout : le produit

## À quoi ça sert

Répondre à deux questions, pour quelqu'un qui suit la scène professionnelle ou qui construit un effectif :

1. Qui sont les meilleurs joueurs du monde, à chaque poste, dans chaque ligue, sur chaque événement ?
2. Quel joueur recruter à un poste donné, en tenant compte de son niveau, de son style et de son contrat ?

La note doit coller au ressenti d'un observateur averti. Une note que personne ne trouve crédible est un défaut, même si le calcul est défendable.

## Ce que l'appli propose

- **Classement** : meilleur cinq et liste complète ; filtres poste, niveau de ligue, région, ligue, événement, contrat ; saisons 2025 et 2026.
- **Fiche joueur** : note, niveau de l'équipe et écart individuel, forme récente, forces et points faibles rédigés, huit facettes, weakside et strongside, note par événement, statistiques, champions, joueurs au style proche, date de fin de contrat.
- **Scouting** : une équipe et un poste à pourvoir ; candidats classés par note, ressemblance de style avec le titulaire et apport aux quatre autres joueurs ; filtre et tri par fin de contrat.
- **Méthode** : le calcul expliqué simplement, avec ses limites.

## Choix de méthode et raisons

- **Note = niveau de l'équipe + écart individuel.** Des stats brutes surnotent les joueurs qui dominent une petite ligue. Le niveau d'équipe (modèle de victoire sur toute la saison, ligues situées entre elles par les tournois internationaux) place tout le monde sur une échelle commune ; les stats ne servent qu'à départager par rapport à ce qu'on attend dans ce contexte.
- **Stats comparées au même poste, dans la même compétition, corrigées du champion.** Chaque ligue a son rythme (plus de combats en LPL, plus de vision en LCK) et un tank n'a pas à être jugé sur les dégâts d'un carry.
- **Poids de l'écart individuel calé sur les données** (environ 100 points par écart-type), pas choisi à la main.
- **Échelle** : 80 = joueur médian des ligues majeures, plafond tassé vers 97 pour que 99 reste hors d'atteinte.
- **Style séparé du niveau.** Le vecteur de style (ressources, activité avant 15 minutes, risque, vision, type de champions) sert à comparer des profils, jamais à noter.
- **Niveaux de ligue de départ** repris du projet LoL Ratings 3.0, seul élément hérité de l'ancien modèle.

## Limites connues

- Les supports à style engage dans les équipes dominantes sont sous-notés : ils meurent plus et posent moins de wards, et leur impact (appels, placement) ne laisse pas de trace statistique. Exemple constaté : Labrov et Busio en LEC 2026.
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs.
- Weakside et strongside sont approchés par la participation aux kills avant 15 minutes ; les données ne disent pas où passe le jungler.
- Une fin de contrat proche ne dit pas si le joueur a prolongé ou signé ailleurs. La base de Riot couvre les ligues majeures et les principales ligues régionales ; ses onglets ne sont pas mis à jour au même rythme.

## Sources

- Matchs : Oracle's Elixir (fichiers annuels).
- Contrats : base publique des contrats reconnus par Riot.

## Suite envisagée

- Mise à jour hebdomadaire automatique des matchs et des contrats.
- Mieux créditer les supports et junglers dont le rôle est d'initier.
- Âge et nationalité des joueurs pour le scouting.
