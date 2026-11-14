# Rift Scout : le produit

## À quoi ça sert

Répondre à deux questions, pour quelqu'un qui suit la scène professionnelle ou qui construit un effectif :

1. Qui sont les meilleurs joueurs du monde, à chaque poste, dans chaque ligue, sur chaque événement ?
2. Quel joueur recruter à un poste donné, en tenant compte de son niveau, de son style et de son contrat ?

La note doit coller au ressenti d'un observateur averti. Une note que personne ne trouve crédible est un défaut, même si le calcul est défendable. Mais quand le ressenti et les données divergent, on teste avant de corriger, et on ne corrige que si un test le justifie (voir « Ce qui a été testé et écarté »).

## Ce que l'appli propose

- **Classement** : meilleur cinq et liste complète ; filtres poste, niveau de ligue, région, ligue, événement, contrat ; saisons 2025 et 2026.
- **Période récente** : option « Période récente » du sélecteur « Noter les joueurs sur ». Pour chaque joueur, son dernier split de ligue (saison régulière et playoffs) et tout ce qu'il a joué ensuite (tournois, coupes), même calcul que les notes d'événement ; au moins 8 parties. Version prudente : le niveau de l'équipe s'écarte moins de sa saison que pour un événement, et l'écart individuel est complété par 15 parties de saison (`SD_RECENT`, `K_RECENT_IND`). En 2026, 45 joueurs de ligues majeures sur 324 s'écartent de plus de 5 points de leur note de saison (75 avant). Cas marquant, vérifié : DN SOOPers, 23 victoires sur 35 parties depuis fin juillet pour 15,5 attendues, après correction des équipes remaniées (Sharvel 83 sur la saison, 94 sur la période récente).
- **Qui afficher, et sur quoi noter** : les filtres choisissent les joueurs ; le sélecteur « Noter les joueurs sur » choisit la note (toute la saison, ou la ligue / l'événement choisi seulement). Région + événement donne par exemple les notes des Worlds des joueurs d'EMEA.
- **Fiche joueur** : note, niveau de l'équipe et écart individuel, forme récente, forces et points faibles rédigés, huit facettes, weakside et strongside, parcours de la saison (une note par équipe), note par événement, statistiques (dont morts inutiles, présence sur les objectifs, temps près de son jungler), champions, joueurs au style proche, âge, nationalité, résidence, fin de contrat.
- **Scouting** : une équipe et un poste à pourvoir ; candidats classés par note, ressemblance de style avec le titulaire et apport aux quatre autres joueurs ; filtres contrat, âge maximum, résidence ; tri par fin de contrat.
- **Avant et après** (dans le scouting) : on essaie un ou plusieurs joueurs dans une équipe ; niveau de l'effectif, chances de victoire contre une équipe moyenne de la ligue, rang estimé et profil par facette sont recalculés et comparés à l'effectif actuel.
- **Méthode** : le calcul expliqué simplement, avec ses limites.

## Le calcul

### La note

- **Note = niveau de l'équipe + écart individuel.** Des stats brutes surnotent les joueurs qui dominent une petite ligue. Le niveau d'équipe (modèle de victoire sur toute la saison, ligues situées entre elles par les tournois internationaux) place tout le monde sur une échelle commune ; les stats ne servent qu'à départager par rapport à ce qu'on attend dans ce contexte.
- **Stats comparées au même poste, dans la même compétition, corrigées du champion.** Chaque ligue a son rythme (plus de combats en LPL, plus de vision en LCK) et un tank n'a pas à être jugé sur les dégâts d'un carry.
- **Stats attendues selon l'écart de niveau entre les deux équipes**, estimées par niveau de ligue, affinées par compétition et plafonnées pour les gros écarts. Estimées globalement, elles pénalisaient les joueurs des équipes qui dominent une ligue majeure (G2, Karmine Corp) et gonflaient ceux des équipes faibles.
- **Poids de l'écart individuel calé sur les données** (environ 100 points par écart-type), pas choisi à la main.
- **Échelle fixe** : 80 = joueur médian des ligues majeures, plafond tassé vers 97. La conversion points → note (`SCALE_A`, `SCALE_B`) ne bouge plus d'une mise à jour à l'autre ; à recaler en début de saison.
- **Écart interne de la LCK et de la LPL plus large** que dans les autres ligues (`SD_TEAM_BY_LEAGUE`, 250 contre 160). Sur des parties cachées au modèle, le haut de ces ligues battait le bas 3 à 4 points plus souvent qu'annoncé ; cette dispersion plus large corrige l'essentiel sans dégrader les autres ligues ni les tournois internationaux. Effet : environ 0,5 point de note.
- **Chronologies Leaguepedia** (11 146 parties en 2026, 11 491 en 2025, tout sauf la LPL) : morts inutiles (moitié de « Survie »), présence individuelle sur les objectifs (moitié de « Objectifs »), weakside/strongside d'après le temps que le jungler passe près du joueur, trois dimensions de style. Toujours un plus, jamais une condition : une partie sans chronologie se calcule comme avant. Positions ignorées dans les rares parties où le jungler n'est pas à sa place habituelle dans le fichier.
- **Parties hors poste principal comptées**, comparées aux joueurs du poste réellement joué (96 joueurs concernés en 2026 ; leur note baisse le plus souvent, on joue moins bien hors de son poste). Style et statistiques affichées : poste principal seulement.
- **Style séparé du niveau.** Le vecteur de style sert à comparer des profils, jamais à noter.

### Joueurs, équipes, ligues

- **Chaque partie compte avec l'équipe et la ligue où elle a été jouée.** Équipe et ligue affichées = celles des dernières parties de ligue de la saison, pas d'une coupe d'intersaison ni d'une équipe de tournoi (Rekkles 2026 : Los Ratones en LEC, « puis Witchcraft » ; Viper 2025 : Hanwha Life, pas Bilibili Gaming).
- **Un filtre de ligue liste tous ceux qui y ont joué cette saison**, même partis depuis, avec leur équipe dans cette ligue et celle qu'ils ont rejointe (Looki : Karmine Corp Blue Stars en Nexus League, puis Karmine Corp Blue en LFL).
- **Un même joueur sous deux identifiants** (même pseudo, équipe et poste) est réuni, de même qu'une équipe enregistrée sous deux identifiants (même nom, même ligue : DeathMark E-Sports, Croatian Flair…).
- **Équipes remaniées.** Dans les coupes et les tournois, une équipe qui aligne au plus 2 de ses 5 titulaires habituels est traitée comme une équipe à part, avec son propre niveau (`ROSTER_MIN_STARTERS`). KeSPA Cup 2026 : T1 avec un tiers de ses titulaires en moyenne, Dplus Kia avec aucun ; Demacia Cup 2025 : la plupart des équipes chinoises sans titulaire. Avant, battre ces effectifs comptait comme battre l'équipe titulaire (DN SOOPers gonflé par sa KeSPA Cup). 306 matchs concernés en 2026, 350 en 2025 ; le haut de la LCK remonte de 0,5 point environ, les équipes qui avaient battu des réserves baissent.

### Événements

- **La note générale n'est pas une moyenne des notes par événement.** Elle est calculée directement sur toutes les parties de la saison (niveau d'équipe de toute la saison + écart individuel moyen) ; chaque note d'événement réestime le niveau de l'équipe sur les seules parties de l'événement. Les deux restent proches : la note générale s'écarte de la moyenne de ses événements pondérée par les parties de 0,9 point en médiane (2026).

- **Note par événement = niveau d'équipe réestimé sur l'événement**, toutes équipes ensemble, le niveau de saison ne servant que de point de départ faible. Battre une équipe compte selon ce qu'elle a fait dans ce même tournoi, pas selon sa ligue. La forme sur les 15 dernières parties suit la même logique.
- **Portée d'un événement d'après les équipes présentes** : international (plusieurs régions), entre ligues d'une même région, ou coupe d'une seule ligue. Une équipe invitée isolée ne suffit pas à rendre un tournoi international (KeSPA Cup = coupe).
- **Qualifications régionales** (parties entre équipes d'une même région, jouées plus de 3 semaines avant un tournoi international) : notées à part, une par région (« EWC, qualifications EMEA »), et leurs stats comparées à la ligue de la région (EMEA = LEC). La qualification chinoise des Worlds est distincte du dernier split de LPL (playoffs finis le 13 septembre, qualification du 17 au 19).
- **Éditions d'un même tournoi** nommées par leur segment (EMEA Masters Winter, Spring, Summer).
- **Ligues sans segment dans les données** (LFL et Nexus League 2026) : découpées aux pauses de plus de 3 semaines et nommées par leurs mois (« LFL, janvier à mars » = tournoi d'ouverture). Quand une partie seulement des matchs d'une ligue a un segment (LJL, Circuito Desafiante, NACL, NLC, fin de la LFL 2025), les autres (qualifications, ouvertures, barrages) rejoignent le segment le plus proche dans le temps.

## Ce qui a été testé et écarté

Ces pistes ont été vérifiées sur les données et n'ont pas conduit à une correction. Les relancer avant de changer le calcul dans le même sens.

- **Les joueurs des groupes faibles de LPL et de LCK sont-ils surnotés ?** La LPL se joue toute l'année en groupes isolés, la LCK en fin de saison. Le niveau des équipes est bien calibré hors échantillon ; à écart de niveau égal, les groupes faibles n'ont pas de stats gonflées de façon régulière ; comparer chaque joueur à son seul groupe remonterait ces joueurs au lieu de les baisser. Réglage disponible, désactivé (`GROUP_CONTEXT`).
- **Ordre « top LCK > top LEC > reste LCK > reste LEC » ?** Le modèle le donne déjà si « top LEC » = G2 et Karmine Corp : 2026, top 5 LCK 92,6 > G2 et KC 87,6 > reste LCK 86,4 > reste LEC 77,0 (2025 : 93,5 > 85,5 > 84,9 > 76,9). Avec le top 5 de la LEC (84,4), le reste de la LCK passe devant. BNK FEARX (88,6) reste au niveau de G2.
- **Le bas de la LCK est-il bien en dessous de G2 et KC ?** Le modèle met G2 (88) devant HANJIN BRION, DN SOOPers et Kiwoom DRX (86), Karmine Corp à leur niveau, et le bas de la LPL 6 à 8 points sous G2 et KC. Matchs directs Occident contre bas de LCK en 2026 : 7 parties, dont G2 3-0 FEARX (en faveur du ressenti) et des défaites de Vitality et NAVI, équipes moyennes de LEC (sans valeur de preuve). Trop peu pour corriger.
- **La part individuelle des joueurs d'équipes faibles est-elle un effet d'équipe ?** Chez les 619 joueurs qui ont changé d'équipe entre 2025 et 2026, la part de leurs stats commune à leur équipe les suit autant que leur part propre (0,27 dans les deux cas) : c'est du niveau réel. Les joueurs passés de Corée vers l'Occident gardent leur note (kyeahoo 84,5 à Kiwoom DRX en 2025 puis à Karmine Corp en 2026 ; Loki 82 à HANJIN BRION puis à Cloud9).
- **Fiabilité de l'écart individuel.** Mesurée par moitiés de parties : il faut l'équivalent de 22 à 30 parties pour que la moitié d'un écart soit fiable, contre 12 dans le réglage (`K_SHRINK`). Corriger ce réglage ne change presque rien aux joueurs avec beaucoup de parties (normalisation par poste) et a été laissé tel quel.
- **Les meilleurs occidentaux sont-ils sous-classés ?** En 2026, ils sont 7e (Caps) à 18e (Alvaro) de leur poste. Deux tests : (1) en face-à-face de lane contre la Corée et la Chine, l'or à 15 minutes réel correspond à celui que prévoit l'écart de note (LEC : −16 et −10 pièces d'or d'écart en 2026 et 2025, rien de mesurable ; LCS 2025 un peu en dessous) ; (2) en tournoi international, les joueurs de LEC font un peu moins bien que leur note de saison, comparés aux Coréens et aux Chinois (+0,3 et −1,1 point, contre +0,8 à +1,4). Les données ne justifient pas de les remonter.

## Limites connues

- **Partage équipe / individuel.** Une équipe qui gagne plus que ses stats ne l'annoncent (G2, Karmine Corp, T1) reçoit un niveau d'équipe haut et des écarts individuels négatifs ; une équipe qui perd malgré des stats correctes (bas de LCK, JD Gaming, LNG) reçoit l'inverse. La note totale reste cohérente ; c'est le partage entre « équipe » et « individuel » qui est flou, et qui fait que des joueurs d'équipes moyennes (DuDu, Aiming, Teddy) passent devant des joueurs occidentaux d'équipes plus fortes.
- **Ressentis non confirmés par les données**, à garder en tête : Labrov et Busio (morts inutiles et présence sur les objectifs faibles, l'hypothèse « ils initient » ne tient pas) ; Caliste 17e des ADC en 2026 (87, plombé par un MSI à 76 alors que son été LEC et son EWC sont à 91-92) ; les meilleurs occidentaux en général.
- **Ce que les stats ne voient pas** : appels, placement, draft, décisions de fin de partie. S'ils font gagner une équipe, ça se retrouve dans son niveau, pas dans les notes individuelles.
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs.
- Les positions ne sont connues qu'une fois par minute. Les joueurs de LPL n'ont ni morts inutiles, ni présence sur les objectifs, ni proximité du jungler (pas de chronologie).
- La forme réagit fort sur 15 parties (jusqu'à 20 points d'écart avec la note de saison).
- Une fin de contrat proche ne dit pas si le joueur a prolongé ou signé ailleurs. La base de Riot couvre les ligues majeures et les principales ligues régionales ; ses onglets ne sont pas mis à jour au même rythme.
- La simulation avant et après suppose que chaque joueur joue dans sa nouvelle équipe comme il a joué cette saison : ni entente, ni langue, ni adaptation à une autre ligue.
- Trois sigles de tournois restent sans nom sûr : AC, CCWS, CT.

## Sources

- Matchs : Oracle's Elixir (fichiers annuels). Reste la source des notes. Téléchargement depuis Google Drive, parfois bloqué par un quota.
- Leaguepedia (compte requis) : âge, pays, résidence, contrats en complément, et pour chaque partie hors LPL le fichier complet de Riot et la chronologie (kills avec position, position de chaque joueur toutes les minutes). Couverture : 92 % des parties d'Oracle's Elixir, tout sauf la LPL et une partie des coupes chinoises.
- Contrats : base publique des contrats reconnus par Riot.
- Niveaux de ligue de départ : projet LoL Ratings 3.0, seul élément hérité de l'ancien modèle.

## Suite envisagée

- Faire tourner une fois la mise à jour automatique de bout en bout (jamais réussi : quota Google Drive au seul essai).
- Comprendre le partage équipe / individuel (G2 et Karmine Corp négatifs, bas de tableau positifs) sans casser ce que montrent les tests de transfert.
- La LEC 2025 montre le même écart haut / bas sous-estimé que la LCK et la LPL (6 points), pas la LEC 2026 : à surveiller avant de l'étendre.
- Capter la forme au fil de la saison (une équipe qui monte en puissance n'est pas distinguée d'une équipe qui décline à bilan égal).
- Nouvelle saison : voir la liste des ajouts manuels dans `CLAUDE.md`.
