# Prix de l'épicerie et contre-tarifs au Canada

*[English version](README.md)*

Un suivi transparent, fondé sur des données publiques, de la façon dont les contre-tarifs canadiens se répercutent sur les prix de l'épicerie : ce qui a été taxé, quelle part s'est retrouvée en magasin, et où vont les prix alimentaires. Bilingue (FR/EN), mis à jour chaque mois, chaque choix sourcé.

**Application en ligne : [https://canada-grocery-prices.streamlit.app/](https://canada-grocery-prices.streamlit.app/)** · **Les résultats en une page : [docs/fr/resume.md](docs/fr/resume.md)**

## Constats principaux (données jusqu'à août 2026)

1. **Ce que cela a coûté aux ménages** : environ 50 cents par 100 dollars d'épicerie pendant l'application des contre-tarifs de 2025 (fourchette plausible de 0 à 1,60 dollar), soit environ 0,5 point sur les 1,8 % de hausse des prix en magasin sur ces mois.
2. **Les produits américains taxés pèsent peu dans chaque indice de prix de l'épicerie** (médiane 9 % en 2025). Même une transmission complète ne ferait bouger ces indices que d'environ 3 points, près de la limite de détection des données mensuelles publiques.
3. **Contre-tarifs de 2025 : environ 40 % de transmission** (intervalle à 95 % de −7 % à 86 %) une fois les cours mondiaux retirés, cohérent avec l'estimation d'environ 25 % de la Banque du Canada. La flambée du café en 2025 vient des cours mondiaux, pas du tarif.
4. **Les tarifs « laitiers » de 2026 visent surtout des ingrédients** (poudres de lait, lactosérum). Le lait frais et le beurre ne sont pas sur la liste ; le tarif de 25 % sur le fromage peut ajouter au plus 0,6 point à l'indice des prix du fromage.
5. **Prévisions** : prix alimentaires +3,5 % en 2026 (Food Price Report : +4 % à +6 %), avec des intervalles qui ont couvert 85–97 % des valeurs passées.

## Les méthodes, en une phrase chacune

| Question | Méthode | Où |
|---|---|---|
| Qu'est-ce qui a été taxé ? | Listes tarifaires officielles rattachées aux séries de l'IPC, avec un niveau de confiance par rattachement | notebook 02, D18 |
| Les prix ont-ils monté à cause du tarif ? | Comparer chaque série taxée à un mélange pondéré de séries semblables non taxées (contrôle synthétique), puis différences avant/après | notebooks 03–04, D19–D21 |
| Le tarif ou les cours mondiaux ? | Retirer la part expliquée par les cours mondiaux des matières premières | notebook 05, D22 |
| Où vont les prix ? | Prévisions simples et par apprentissage automatique, testées sur 2019–2025, avec des intervalles vérifiés sur le passé | notebook 06, D23 |
| Une nouvelle liste tarifaire peut-elle être rattachée automatiquement ? | TALN : TF-IDF, embeddings multilingues et fusion de classements proposent des séries de l'IPC pour chaque ligne douanière, évalués contre la correspondance manuelle | notebook 07, D29 |
| Que disent les documents officiels ? | RAG : BM25, embeddings, fusion de classements et reclassement par cross-encoder sur 765 passages officiels, évalués par rappel@k, MRR et nDCG | notebook 08, D30 |
| Quelles catégories pèsent dans le coût ? | SQL sur un entrepôt DuckDB (CTE, fonctions de fenêtre) | `sql/`, D31 |

## Application

En ligne : [https://canada-grocery-prices.streamlit.app/](https://canada-grocery-prices.streamlit.app/). Un tableau de bord bilingue, en thème clair ou sombre, qui commence par le contexte (ce qui s'est passé, pourquoi c'est important, ce que ce projet apporte), puis montre ce que les tarifs ont coûté à un ménage (saisissez vos propres dépenses), si un produit a été taxé, l'inflation alimentaire par province, les prévisions avec intervalles, les effets des tarifs, une note mensuelle rédigée automatiquement à partir des dernières données, des liens partageables et une image de synthèse, et un onglet de questions fondé sur des réponses vérifiées. Un assistant IA optionnel répond à vos questions formulées librement, uniquement à partir des faits vérifiés du tableau de bord (activé avec une clé API ; son jeu d'évaluation bilingue est prêt et sera lancé dès qu'une clé sera disponible, D34).

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Reproduire

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python src/refresh.py        # télécharge les dernières données, reconstruit rôles, prévisions et données de l'application
python src/fetch_trade.py    # importations UN Comtrade (nécessaires au notebook 04)
python src/sql/warehouse.py  # entrepôt SQL et requêtes métier
pytest -q                    # 22 vérifications (aussi lancées par GitHub Actions à chaque envoi)
```

Les notebooks `01` à `06` de `notebooks/` s'exécutent dans l'ordre et gardent leurs résultats.

## Organisation du dépôt

```
src/                 téléchargement, catalogue de l'IPC, rôles tarifaires, mise à jour
src/causal/          contrôle synthétique, doubles différences, exposition, correction des cours mondiaux
src/forecast/        modèles de prévision, backtest, intervalles conformes
app/                 application Streamlit et son petit jeu de données
data/reference/      fichiers de référence versionnés (listes tarifaires, correspondances)
notebooks/           01 couverture, 02 correspondance, 03 reproduction, 04 transmission, 05 cours mondiaux, 06 prévisions, 07 TALN, 08 RAG
src/nlp/, src/rag/   classification des lignes tarifaires, corpus documentaire et évaluation de la recherche
sql/                 questions métier en SQL (DuckDB)
docs/                journal des décisions, références, résumé d'une page (FR et EN)
tests/               vérifications automatiques
```

## Perspectives

- **Assistant IA et classification par LLM** (D28, D29, D34) : le code et les jeux de questions sont prêts ; ils se lancent en une commande dès qu'une clé API Anthropic est disponible, et l'assistant n'apparaît dans l'application qu'une fois sa fiabilité publiée.
- **Recherche documentaire (RAG)** (D30, D32) : retirée de l'application jusqu'à ce que le corrigé des questions réservées atteigne 80 % dans chaque langue (aujourd'hui 100 % en anglais, 56 % en français). Prochaine correction : traduire les questions françaises avant la recherche, puis mesurer sur un nouveau jeu de questions jamais utilisé.
- **Méthodes** : intervalles conformes par groupe de séries (Mondrian), doubles différences synthétiques, données commerciales à 8 chiffres.

## Traçabilité

Chaque choix est justifié dans le [journal des décisions](docs/fr/journal-decisions.md) (D01–D34) et appuyé par les [références](docs/references.md), toutes vérifiées en ligne.

## Données

Toutes publiques : Statistique Canada (IPC 18-10-0004-01, prix moyens 18-10-0245-01, poids du panier 18-10-0007-01, dépenses des ménages 36-10-0225-01), Banque du Canada (USD/CAD), UN Comtrade (importations par produit), Banque mondiale (cours des matières premières). Listes tarifaires : Finances Canada et Gazette du Canada.

## Auteur

David Doe, étudiant en data science, Université de Lille.
