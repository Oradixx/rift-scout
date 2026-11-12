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
- **Avant et après** (dans le scouting) : on essaie un ou plusieurs joueurs dans une équipe ; niveau de l'effectif, chances de victoire contre une équipe moyenne de la ligue, rang estimé et profil par facette sont recalculés et comparés à l'effectif actuel.
- **Méthode** : le calcul expliqué simplement, avec ses limites.

## Choix de méthode et raisons

- **Note = niveau de l'équipe + écart individuel.** Des stats brutes surnotent les joueurs qui dominent une petite ligue. Le niveau d'équipe (modèle de victoire sur toute la saison, ligues situées entre elles par les tournois internationaux) place tout le monde sur une échelle commune ; les stats ne servent qu'à départager par rapport à ce qu'on attend dans ce contexte.
- **Stats comparées au même poste, dans la même compétition, corrigées du champion.** Chaque ligue a son rythme (plus de combats en LPL, plus de vision en LCK) et un tank n'a pas à être jugé sur les dégâts d'un carry.
- **Poids de l'écart individuel calé sur les données** (environ 100 points par écart-type), pas choisi à la main.
- **Échelle** : 80 = joueur médian des ligues majeures, plafond tassé vers 97 pour que 99 reste hors d'atteinte.
- **Style séparé du niveau.** Le vecteur de style (ressources, activité avant 15 minutes, risque, vision, type de champions) sert à comparer des profils, jamais à noter.
- **Stats attendues estimées par niveau de ligue**, affinées par compétition et plafonnées pour les gros écarts de niveau. Estimées globalement, elles pénalisaient les joueurs des équipes qui dominent une ligue majeure (G2, Karmine Corp) et gonflaient ceux des équipes faibles.
- **Note par événement = niveau d'équipe réestimé sur l'événement.** Le même modèle de victoire est relancé sur les seules parties de l'événement, toutes équipes ensemble, avec le niveau de saison comme point de départ faible (équivalent de deux à trois parties). Auparavant la note restait collée au niveau de saison quand l'équipe jouait peu de parties : à l'EWC 2026, Anyone's Legend (4 parties, battu 2-0 par Karmine Corp) restait devant. Les qualifications régionales d'un tournoi (parties entre équipes d'une même région, jouées plus de 21 jours avant) sont notées à part, une par région, et leurs stats sont comparées à la ligue de la région (qualifications EMEA de l'EWC = LEC). Les événements sont classés d'après les équipes présentes : international, entre ligues d'une même région, ou coupe d'une seule ligue.
- **Niveaux de ligue de départ** repris du projet LoL Ratings 3.0, seul élément hérité de l'ancien modèle.

## Limites connues

- Les supports à style engage dans les équipes dominantes sont sous-notés : ils meurent plus et posent moins de wards, et leur impact (appels, placement) ne laisse pas de trace statistique. Exemple constaté : Labrov et Busio en LEC 2026.
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs.
- Weakside et strongside sont approchés par la participation aux kills avant 15 minutes ; les données ne disent pas où passe le jungler.
- Une fin de contrat proche ne dit pas si le joueur a prolongé ou signé ailleurs. La base de Riot couvre les ligues majeures et les principales ligues régionales ; ses onglets ne sont pas mis à jour au même rythme.

- La simulation avant et après suppose que chaque joueur joue dans sa nouvelle équipe comme il a joué cette saison : ni entente, ni langue, ni adaptation à une autre ligue.

## Sources

- Matchs : Oracle's Elixir (fichiers annuels). Reste la source des notes.
- Leaguepedia (compte requis) : âge, pays, résidence, contrats en complément. Il donne aussi, pour chaque partie hors LPL, le fichier complet de Riot et la chronologie (kills avec position, position de chaque joueur toutes les minutes). Couverture mesurée sur 2026 : 11 377 parties sur 12 405, soit tout sauf la LPL et quelques coupes chinoises (0 %).
- Contrats : base publique des contrats reconnus par Riot.

## Suite envisagée

- À partir des chronologies Leaguepedia : morts inutiles et objectifs disputés (mieux créditer ceux qui initient), proximité du jungler (vrai weakside et strongside). La LPL n'étant pas couverte, ces mesures devront rester facultatives par joueur.
- Il reste un écart individuel négatif chez G2 et Karmine Corp après correction : à réexaminer avec ces nouvelles mesures.
