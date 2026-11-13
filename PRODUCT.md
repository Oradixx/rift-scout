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
- **Qui afficher et sur quoi noter sont deux choix séparés.** Niveau, région, ligue et événement choisissent les joueurs (ligue actuelle, ou participation à l'événement). Le sélecteur « Noter les joueurs sur » choisit la note : toute la saison, ou la ligue / l'événement seulement. Par défaut : toute la saison pour une ligue, l'événement seulement pour un événement. À filtres égaux, une note de saison ne doit jamais changer à cause de l'interface.
- **Chronologies Leaguepedia** (11 146 parties en 2026 et 11 491 en 2025, tout sauf la LPL) : morts inutiles (moitié de « Survie »), présence individuelle sur les objectifs (moitié de « Objectifs »), weakside/strongside d'après le temps que le jungler passe près du joueur, et trois dimensions de style. Effet mesuré sur les notes : 0,1 point en médiane, 1,1 au plus. Ces mesures sont toujours un plus, jamais une condition : une partie sans chronologie se calcule comme avant.
- **Joueurs à plusieurs équipes.** Chaque partie compte avec son équipe et sa ligue. Équipe et ligue affichées = celles des dernières parties de ligue de la saison (pas d'une coupe d'intersaison : en 2025, Viper reste à Hanwha Life en LCK, avec la mention de son passage à Bilibili Gaming). La fiche montre le parcours et une note par équipe. Un joueur enregistré sous deux identifiants (même pseudo, équipe et poste) est réuni.
- **Échelle fixe.** La conversion points → note (`SCALE_A`, `SCALE_B` dans `build.py`) ne bouge plus à chaque mise à jour ; `build.py` affiche l'écart avec l'échelle recalculée. À recaler à la main en début de saison.
- **Écart interne de la LCK et de la LPL élargi** (`SD_TEAM_BY_LEAGUE`, 250 au lieu de 160). Sur des parties cachées au modèle, le haut du classement battait le bas 3 à 4 points plus souvent qu'annoncé ; corrigé pour l'essentiel, sans dégrader les autres ligues. Les équipes du bas de ces ligues baissent, celles du haut montent.
- **Ligues sans segment dans les données** (LFL, Nexus League, LJL, Circuito Desafiante…) : découpées aux pauses de plus de 3 semaines et nommées par leurs mois (« LFL, avril à juin »).
- **Groupes de niveau en LPL et en LCK : vérifié, pas de correction propre aux groupes.** La LPL se joue toute l'année en groupes isolés (474 parties en 2026), la LCK en fin de saison (98). Trois tests : (1) le niveau des équipes est bien calibré hors échantillon (favoris nets annoncés à 72 %, gagnants à 71 % en LCK et LPL) ; (2) à écart de niveau égal, les groupes faibles n'ont pas de stats gonflées de façon régulière ; (3) comparer chaque joueur à son seul groupe remonterait les joueurs des groupes faibles au lieu de les baisser. Le réglage existe (`GROUP_CONTEXT`) mais reste désactivé.
- **Écart individuel plus haut dans les équipes du bas de tableau**, dans toutes les ligues majeures, groupes ou non (LEC comprise). C'est l'envers du constat sur G2 et Karmine Corp : une équipe qui gagne plus que ses stats ne l'annoncent a un niveau d'équipe haut et des écarts individuels négatifs, et inversement. La note totale (équipe + individuel) reste cohérente ; c'est le partage entre les deux qui est flou.
- **Niveaux de ligue de départ** repris du projet LoL Ratings 3.0, seul élément hérité de l'ancien modèle.

## Limites connues

- Labrov et Busio (LEC 2026) sortent sous le ressenti général. L'hypothèse « sous-notés parce qu'ils initient » a été testée avec les chronologies et n'est pas confirmée : 49 % des morts de Labrov sont inutiles (37 % pour Keria), et Busio n'est présent que sur 27 % des objectifs de son équipe. Ce qui reste hors de portée des stats : appels, placement, rôle dans l'équipe.
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs.
- Les positions ne sont connues qu'une fois par minute : la proximité du jungler est une bonne mesure, pas un suivi continu. Les joueurs de LPL n'ont ni morts inutiles, ni présence sur les objectifs, ni proximité du jungler.
- Une fin de contrat proche ne dit pas si le joueur a prolongé ou signé ailleurs. La base de Riot couvre les ligues majeures et les principales ligues régionales ; ses onglets ne sont pas mis à jour au même rythme.

- La simulation avant et après suppose que chaque joueur joue dans sa nouvelle équipe comme il a joué cette saison : ni entente, ni langue, ni adaptation à une autre ligue.

## Sources

- Matchs : Oracle's Elixir (fichiers annuels). Reste la source des notes.
- Leaguepedia (compte requis) : âge, pays, résidence, contrats en complément. Il donne aussi, pour chaque partie hors LPL, le fichier complet de Riot et la chronologie (kills avec position, position de chaque joueur toutes les minutes). Couverture mesurée sur 2026 : 11 377 parties sur 12 405, soit tout sauf la LPL et quelques coupes chinoises (0 %).
- Contrats : base publique des contrats reconnus par Riot.

## Suite envisagée

- G2 et Karmine Corp gardent un écart individuel négatif sur leurs cinq joueurs : ces équipes gagnent plus que leurs stats ne le laissent attendre. À comprendre.
- Capter la forme au fil de la saison (une équipe qui monte en puissance n'est pas distinguée d'une équipe qui décline à bilan égal).
- Nouvelle saison : voir la liste des ajouts manuels dans `CLAUDE.md`.
