# Fichiers de matchs (Oracle's Elixir)

Copie des fichiers annuels d'Oracle's Elixir (https://oracleselixir.com/tools/downloads, données de Tim Sevenhuysen),
compressés, pour éviter le quota de téléchargement de Google Drive. Relevé du 14 novembre 2026 (parties jusqu'au 13 novembre 2026).
Cette branche ne contient que des données : le code est sur `main`.

| Fichier | Contenu |
|---|---|
| `2023_…csv.gz` à `2026_…csv.gz` | fichiers officiels d'Oracle's Elixir, un par saison |
| `oe_2022.csv.gz` | saison 2022 (bonus de LoL Ratings) |

Les parties qu'Oracle's Elixir n'a pas (petites ligues, finale des Worlds 2026) et les chronologies Leaguepedia sont sur `main`,
dans `pipeline/lp_games_<année>.csv.gz` et `pipeline/lp_timeline_<année>.csv.gz`.

Récupération, depuis le dossier du projet :

    mkdir -p data/raw
    for f in 2023 2024 2025 2026; do
      curl -sL "https://raw.githubusercontent.com/Oradixx/rift-scout/donnees-oe/${f}_LoL_esports_match_data_from_OraclesElixir.csv.gz" | gunzip > "data/raw/${f}_LoL_esports_match_data_from_OraclesElixir.csv"
    done
    curl -sL "https://raw.githubusercontent.com/Oradixx/rift-scout/donnees-oe/oe_2022.csv.gz" | gunzip > data/raw/oe_2022.csv
