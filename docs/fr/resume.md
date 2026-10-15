# Les résultats en une page

*[English version](../en/summary.md)* · [Application en ligne](https://canada-grocery-prices.streamlit.app/) · Données jusqu'à août 2026 · Chaque chiffre est tracé dans le [journal des décisions](journal-decisions.md).

**Question.** De combien les contre-tarifs canadiens font-ils monter les prix de l'épicerie, à quelle vitesse et pour combien de temps ?
**Démarche.** Données publiques uniquement (Statistique Canada, Banque du Canada, UN Comtrade, Banque mondiale), méthodes choisies pour être faciles à expliquer, chaque choix sourcé.

## La réponse pour les ménages

Pendant l'application des contre-tarifs de 2025 (mars à août 2025), ils ont coûté à un ménage moyen environ **50 cents par 100 dollars d'épicerie** (fourchette plausible de 0 à 1,60 dollar), soit environ 0,5 point sur les 1,8 % de hausse des prix en magasin sur ces mois. L'application le calcule pour vos propres dépenses. (D26)

**D'où vient le coût.** En 2025, quatre catégories portent 64 % de ce coût, dont trois en borne haute (boulangerie, condiments, boissons : leurs codes douaniers sont plus larges que les produits taxés). Les tarifs de 2026 coûtent environ **11 cents par 100 dollars**, dont seulement 2 cents de solides : le fromage, seul produit taxé tel qu'il est vendu en magasin. Le reste porte sur des ingrédients (mélanges de boulangerie, poudres de lait, lactosérum), dont une partie va aux restaurants et aux fabricants. (D33)

**Surveiller 2026.** La prévision faite juste avant les tarifs de septembre 2026 est figée comme trajectoire que les prix auraient suivie sans eux, et chaque nouveau mois y est comparé. Rejouée sur 2018 et 2025, une alerte fondée sur cette comparaison n'a rien détecté (les séries taxées et non taxées sont sorties de leurs intervalles de prévision aussi souvent les unes que les autres) : elle reste donc un outil d'analyse et n'est pas affichée comme une alerte. (D33)

## Trois constats

**1. Les produits américains taxés pèsent peu dans chaque indice de prix de l'épicerie.**
En 2025, la part médiane des produits américains taxés dans une série taxée de l'IPC était de 9 %. Même si le tarif de 25 % avait été répercuté en entier, ces séries n'auraient bougé que d'environ 3 points en moyenne, près de ce que les données mensuelles publiques permettent de détecter (environ 5 points). C'est pourquoi l'effet est difficile à voir dans l'IPC, et pourquoi la Banque du Canada travaille avec des données par produit. (D20, D21)

**2. 2025 : une transmission d'environ 40 %, cohérente avec la Banque du Canada.**
En comparant chaque série taxée à un mélange pondéré de séries semblables non taxées, et en retirant les cours mondiaux, environ 40 % du tarif s'est retrouvé dans les prix en magasin (intervalle à 95 % de −7 % à 86 %). L'intervalle contient l'estimation de la Banque du Canada, environ 25 %. Le café est exclu de cette estimation : sa hausse vient des cours mondiaux (l'arabica a doublé), et il est resté cher après la levée du tarif. (D21, D22)

**3. 2026 : les tarifs « laitiers » visent surtout des ingrédients.**
La liste de septembre 2026 taxe les poudres de lait et le lactosérum (50 %) et le fromage (25 %). Le lait frais, le beurre, le yogourt et la crème glacée n'y figurent pas. Le fromage américain représente environ 2,4 % des dépenses des ménages en fromage : même une transmission complète n'ajouterait que 0,6 point à l'indice des prix du fromage. (D06, D18)

## Prévisions

Prévisions à 12 mois pour 101 séries de prix alimentaires, testées sur 2019–2025 comme si elles avaient été faites dans le passé. Le modèle publié bat une méthode simple « comme l'an dernier » à tous les horizons (MASE 1,28 contre 2,16), et ses intervalles à 80 % et 95 % ont couvert 85–87 % et 96–97 % des valeurs de 2023–2025. Les prix alimentaires sont prévus à +3,5 % pour 2026, juste sous la fourchette de +4 % à +6 % du Food Price Report. (D23)

## Limites

- 2018 (surtaxe de 10 %) : aucun effet détectable ; cela ne confirme ni ne contredit les 70 % de la Banque du Canada pour l'alimentation.
- Un test placebo sur les produits laitiers a en partie échoué : les prix laitiers suivent leur propre dynamique réglementée.
- L'exposition aux importations est mesurée au niveau des produits à 6 chiffres et à la valeur à la frontière ; c'est une approximation.

## En cours

- **Recherche documentaire (RAG) :** retirée de l'application jusqu'à ce qu'elle réponde correctement à 80 % des questions réservées dans chaque langue (aujourd'hui 100 % en anglais, 56 % en français) ; prochaine correction : traduire les questions françaises avant la recherche. (D32)
- **Assistant IA et classification par LLM :** prêts à lancer, en attente d'une clé API ; l'assistant n'est affiché qu'une fois sa fiabilité publiée. (D34)

## Compétences mises en œuvre

- **Inférence causale :** contrôle synthétique avec tests de permutation, doubles différences à traitement continu, tests placebo.
- **Prévision :** référence saisonnière d'abord, backtest à origine glissante, LightGBM, intervalles de prédiction conformes dont la couverture est vérifiée.
- **TALN et recherche d'information :** TF-IDF, plongements multilingues, fusion de rangs et BM25, évalués contre des étiquettes humaines avec intervalles bootstrap.
- **Ingénierie des données et produit :** API publiques (Statistique Canada, Banque du Canada, UN Comtrade, Banque mondiale), mise à jour mensuelle en une commande, SQL, tests en intégration continue, application Streamlit bilingue en ligne.

## Contenu du dépôt

Une mise à jour mensuelle (`python src/refresh.py`), huit notebooks, une application bilingue, des requêtes SQL métier, 30 tests automatiques lancés à chaque envoi, et un journal des décisions (D01–D34).
