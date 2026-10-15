# Journal des décisions

Chaque décision du projet est justifiée par une source (voir `docs/references.md`).
Format : **Décision** → **Justification** → **Alternatives écartées**.
Statut : [décidé] ou [à confirmer] avec les données.

---

## D01 — Sujet : l'inflation alimentaire au Canada et l'effet des contre-tarifs [décidé]
**Décision.** Mesurer et prévoir l'effet des contre-tarifs canadiens sur les prix de l'épicerie, avec un assistant bilingue pour interroger les résultats.

**Justification.**
- La question touche tous les ménages : le *Canada's Food Price Report 2026* prévoit une hausse de 4 à 6 % des prix alimentaires, soit jusqu'à 994 $ de plus pour une famille de quatre [R5].
- Elle est d'actualité : de nouveaux contre-tarifs sont en vigueur depuis le 8 septembre 2026 sur 27,6 G$ d'importations américaines, dont les produits laitiers (50 %) et les fromages (25 %) [R7, R8]. Leur effet sur l'épicerie fait débat [R6].
- La Banque du Canada a publié trois études sur ce sujet en 2025–2026 [R1–R4], signe que la question compte pour les institutions économiques canadiennes.

**Alternatives écartées.** Prévision des ventes sur le jeu de données M5 de Walmart (données américaines de 2016, très utilisées, sans lien avec l'actualité) ; prix du logement (sujet saturé) ; risque de feux de forêt (données géospatiales trop lourdes pour un projet mené seul).

## D02 — Positionnement par rapport aux études de la Banque du Canada [décidé]
**Décision.** Ne pas prétendre découvrir l'effet des tarifs de 2025. Le projet (1) **reproduit** les ordres de grandeur publiés, avec des données **entièrement publiques**, (2) se **concentre sur l'alimentation**, catégorie pour laquelle R1/R2 ne publient pas de taux distinct, et (3) **étend l'analyse aux tarifs de septembre 2026**, qui n'ont pas encore été étudiés.

**Justification.**
- R1/R2 utilisent des prix en ligne quotidiens de 7 détaillants (données privées) et ne donnent pas de taux de transmission propre à l'épicerie.
- R3 utilise les microdonnées de l'IPC, qui ne sont pas publiques.
- Reproduire un résultat avec des données ouvertes est une démarche scientifique reconnue, et suivre en continu un choc en cours apporte quelque chose de nouveau.

**Repositionnement (2026-10-14, après D20–D23).** La reproduction ne peut être que *compatible* avec les estimations de la Banque du Canada (D20–D22) : les sous-indices mensuels publics sont trop agrégés pour les confirmer ou les rejeter. L'apport du projet est donc formulé comme **un suivi transparent fondé sur des données publiques** : ce que chaque liste tarifaire taxe réellement (D18), quelle part peut atteindre les prix en magasin compte tenu de l'exposition aux importations (D21), si les cours mondiaux expliquent un mouvement de prix (D22), et des prévisions mensuelles (D23), le tout reproductible en une commande (D25). L'extension à 2026 se limite à l'exposition et aux scénarios : l'effet direct sur le fromage est d'au plus 0,6 point (D06).

## D03 — Données pour la mesure causale : les sous-indices de l'IPC (18-10-0004-01) [décidé]
**Décision.** Mesurer l'effet des tarifs avec les sous-indices mensuels de l'IPC (par exemple « fromage », « lait frais », « café »), et non avec les prix moyens.

**Justification.** Statistique Canada précise que le tableau des prix moyens « ne mesure pas la variation pure des prix » et recommande l'IPC pour mesurer l'inflation [S3]. L'IPC corrige les changements de qualité et de format.

## D04 — Données pour le tableau de bord : les prix moyens (18-10-0245-01) [décidé]
**Décision.** Utiliser les prix moyens en dollars (par exemple « 4 L de lait ») uniquement pour l'interface grand public et pour l'assistant, et **traiter la rupture de janvier 2024**, date à laquelle d'autres épiciers ont été ajoutés à l'échantillon.

**Justification.** Les prix en dollars parlent davantage au public que des indices. Statistique Canada signale toutefois une rotation des produits et appelle à la prudence sur les variations autour de janvier 2024 [S3]. On ajoute donc une variable indicatrice de rupture, et on ne tire aucune conclusion causale de ce tableau.

## D05 — Méthode causale principale : le contrôle synthétique, produit par produit [décidé]
**Décision.** Pour chaque sous-indice taxé, construire un « jumeau » à partir des sous-indices non taxés les plus proches avant le choc [M1, M2]. L'effet estimé est l'écart entre le prix réel et ce jumeau. On vérifie la robustesse avec une **différence de différences** [M3] et une **DiD synthétique** [M4].

**Justification.**
- C'est la méthode retenue par la Banque du Canada pour l'épisode de 2018 [R3]. La différence de différences est celle de R2.
- Les épisodes de tarifs ont des dates différentes (2018, 2025, 2026). Callaway et Sant'Anna [M3] traitent correctement ce cas de traitement échelonné.
- Les dates de début et de fin des tarifs viennent de sources officielles [R1, R7, R9] (fichier `data/reference/tariff_events.csv`).

**Point à vérifier avec les données.** Le niveau de détail des sous-indices de l'IPC est-il assez fin pour isoler les produits taxés ? À défaut, on pondère selon l'exposition aux importations américaines.

**Constat (2026-10-14, notebook 01).** La branche alimentaire compte 129 séries. Pour les tarifs de septembre 2026 sur les produits laitiers et les fromages, la granularité suffit : *Lait frais*, *Beurre*, *Fromage*, *Crème glacée et produits connexes* et *Autres produits laitiers* existent au niveau national et par province depuis 1949–1985, et des séries nationales plus fines existent depuis 2013 (*Lait entier*, *Lait faible en matières grasses*, *Cheddar*, *Mozzarella*, *Fromage fondu*, *Fromage non affiné ou frais*). La granularité pour les listes de 2018 et 2025 sera vérifiée lors de leur correspondance (étape 3). Le statut reste [à confirmer] d'ici là.

**Conclusion (2026-10-14, notebook 02).** La granularité suffit pour les trois épisodes une fois les lignes tarifaires rattachées aux séries de l'IPC (D18) : 10 séries traitées utilisables pour 2018, 22 pour 2025 et 5 pour 2026. Les séries où les produits taxés ne sont qu'une petite part ou seulement un ingrédient sont exclues plutôt que pondérées par l'exposition aux importations (voir D18).

## D06 — Les a priori sur la transmission : des scénarios encadrés par la littérature [décidé]
**Décision.** Pour les tarifs de 2026, produire trois scénarios plutôt qu'une prévision unique :
- **bas**, environ 25 % de transmission et un effet temporaire (épisode de 2025 [R1, R2]) ;
- **central**, environ 60 % ;
- **haut**, environ 70 % pour l'alimentation, avec un effet persistant (épisode de 2018 [R3]).

**Justification.** Deux études canadiennes récentes donnent des résultats très différents. La littérature américaine montre une transmission presque complète aux prix à la frontière, mais partielle en magasin [L1–L3]. R4 montre que les deux tiers de l'effet passent par les coûts des intrants. Les données des mois à venir indiqueront de quel scénario la réalité se rapproche.

**Hypothèse à tester.** Le système de gestion de l'offre limite les importations laitières américaines. L'effet du tarif de 50 % sur le prix du lait au détail pourrait donc être faible, et passer surtout par les ingrédients (poudres, lactosérum) [R6].

**Fromage 2026, calculé (notebook 06, D23).** Les importations de fromage américain en 2025 étaient d'environ 132 millions de dollars US (24 % des importations de fromage), contre environ 7,7 milliards de dollars canadiens de dépenses des ménages en fromage : exposition s = 0,024. Avec une transmission de 100 %, le tarif de 25 % n'ajouterait que **0,6 point** à l'IPC du fromage ; les trois scénarios ajoutent de 0,15 à 0,4 point, bien à l'intérieur de l'intervalle à 80 % de la prévision (environ ±4 points). Le tarif compte pour les importateurs et pour les fromages faits avec des ingrédients américains, mais son effet direct sur l'IPC du fromage sera trop faible pour être détecté.

## D07 — Variable de contrôle : le taux de change CAD/USD [décidé]
**Décision.** Ajouter le taux USD/CAD quotidien de la Banque du Canada, agrégé par mois, comme variable de contrôle dans les modèles causaux et de prévision.

**Justification.** Le prix d'un produit importé dépend autant du taux de change que du tarif. Si on omet le taux de change, on attribue à tort aux tarifs des variations qu'il explique.

## D08 — Prévision : partir d'une baseline et valider sur une origine glissante [décidé]
**Décision.** Comparer (1) une baseline saisonnière naïve, (2) les modèles ETS et ARIMA par série [F1] et (3) un modèle global LightGBM entraîné sur toutes les séries. L'évaluation se fait par **validation à origine glissante**, avec les métriques MASE et sMAPE.

**Justification.**
- Toute méthode doit battre une référence simple [F1].
- Dans la compétition M5, les modèles globaux à base d'arbres (LightGBM) ont dominé sur des séries de détail apparentées [F2].
- Une validation croisée aléatoire fait fuiter le futur dans l'entraînement, ce qui est une erreur classique [F3].

## D09 — Incertitude : des intervalles de prédiction conformes [décidé]
**Décision.** Accompagner chaque prévision d'un intervalle à 80 % et à 95 % obtenu par prédiction conforme, puis vérifier leur couverture réelle.

**Justification.** La prédiction conforme garantit la couverture sans hypothèse de loi des erreurs [F4]. Pour décider, une fourchette est plus honnête et plus utile qu'un chiffre seul.

## D10 — Point de comparaison externe : le Food Price Report [à confirmer]
**Décision.** Comparer nos prévisions annuelles par catégorie à celles du Food Price Report (+4 à 6 % pour 2026 ; chiffre exact de la prévision 2025 à relever dans le rapport 2025) [R5].

**Justification.** C'est la prévision de référence au Canada, et elle est publiée. Le rapport indique que la prévision 2025 a été globalement juste, mais que la viande a été sous-estimée [R5]. On a donc une comparaison concrète et compréhensible par tous.

**Comparaison faite (notebook 06).** Notre prévision de l'IPC *Aliments* pour 2026 (moyenne annuelle, 8 mois observés et 4 mois prévus) est de **+3,5 %** par rapport à 2025, juste sous la fourchette de +4 % à +6 % du rapport [R5].

## D11 — L'assistant : RAG avec outils, évalué sur un jeu de test [décidé]
**Décision.** Un assistant bilingue qui (1) interroge les tables et les modèles grâce à des outils (SQL, prévisions), (2) cite ses sources [A1], (3) refuse de répondre hors de son périmètre. Il est évalué sur un **jeu de questions bilingue dont les réponses ont été vérifiées**, avec des métriques de fidélité et de pertinence inspirées de RAGAS [A2].

**Justification.** En entreprise, la fiabilité est le premier frein aux assistants IA. Mesurer cette fiabilité, plutôt que la supposer, distingue le projet d'une simple démo.

**Mise à jour (D24).** Pour la première version publique, l'assistant est un ensemble fixe de réponses vérifiées ; la version LLM est reportée.

## D12 — Bilinguisme [décidé]
**Décision.** Produire tout le projet en anglais et en français (README, application, assistant).

**Justification.**
- L'anglais et le français sont les deux langues officielles du Canada, et Statistique Canada publie toutes ses tables dans les deux langues [S1, S2] (paramètre `--lang` de `src/fetch_data.py`).



## D13 — Niveau géographique : le Canada, puis les provinces, avec l'Ontario en priorité [décidé]
**Décision.** Commencer l'analyse au niveau national, puis la décliner par province, en commençant par l'Ontario.

**Justification.** Le Food Price Report prévoit pour l'Ontario une hausse supérieure à la moyenne nationale [R5]. La disponibilité des données par province reste à vérifier.

**Confirmé par les données (2026-10-14, notebook 01).** 32 des 129 séries alimentaires sont publiées par province : les dix provinces plus Whitehorse et Yellowknife (aucune série alimentaire pour Iqaluit), depuis 1978-09 pour la plupart et 1985-01 pour les autres. L'Ontario est toujours présent. Ces 32 séries sont toutes des agrégats (base 2002=100), par exemple *Lait frais*, *Beurre*, *Fromage*, *Légumes frais*. Les séries détaillées (bases 2013, 2023 et 2024) n'existent qu'au niveau national. L'analyse provinciale porte donc sur les agrégats ; l'analyse par produit se fait au niveau national.

## D14 — Limites connues (seront détaillées dans le rapport) [décidé]
- Les données mensuelles agrégées sont moins précises que les prix quotidiens par produit de R1/R2.
- L'exposition réelle aux importations américaines par produit n'est qu'approchée.
- Les effets indirects passent par les intrants [R4] et par la substitution [R3].
- D'autres chocs surviennent en même temps (climat, prix du bœuf [R5], taxe sur les carburants [R6]).
- **Puissance statistique (D20).** Avec les sous-indices mensuels nationaux de l'IPC, le plus petit effet moyen détectable est d'environ 3,6 points pour 2018 et 5,3 points pour 2025, plus que ce qu'impliquent les estimations de la Banque du Canada pour des séries larges de l'IPC.

## D15 — USD/CAD avant 2017 : raccorder l'ancien taux de midi [décidé]
**Décision.** Prolonger la série du taux de change jusqu'au 2007-05-01 avec l'ancien taux de midi de la Banque du Canada (série IEXE0101), et utiliser le taux moyen quotidien actuel (FXUSDCAD) dès son premier jour, le 2017-01-03. Une colonne `source` indique la série d'origine de chaque ligne.

**Justification.**
- FXUSDCAD commence le 2017-01-03. Cela ne laisse que 18 mois avant les tarifs de juillet 2018, une période trop courte pour utiliser le taux de change comme variable de contrôle (D07) dans un contrôle synthétique [M2].
- La Banque du Canada a remplacé le taux de midi par un taux moyen quotidien le 1er mars 2017, a publié les deux en parallèle jusqu'au 28 avril 2017, puis a arrêté le taux de midi [S5, S6].
- Mesure sur nos données, sur les 82 jours où les deux séries existent (du 2017-01-03 au 2017-04-28) : l'écart quotidien est en moyenne de −0,01 % (écart-type 0,12 %), et les moyennes mensuelles diffèrent de moins de 0,03 %. Comme D07 utilise des moyennes mensuelles, le raccord ne crée pas de rupture visible.

**Alternatives écartées.** Garder seulement FXUSDCAD (période avant 2018 trop courte) ; utiliser seulement le taux de midi (arrêté en 2017) ; recaler une série sur l'autre (l'écart mesuré est trop faible pour le justifier).

## D16 — Une seule source pour les chiffres : les tables EN ; les tables FR seulement pour les libellés [décidé]
**Décision.** Tous les calculs lisent les fichiers StatCan en anglais. Les fichiers en français servent uniquement aux libellés français (zone géographique, produit), joints par l'identifiant de série StatCan `VECTOR`. Le chargement passe par `src/load_data.py`.

**Justification.**
- Statistique Canada publie chaque table dans les deux langues [S1, S2] (D12). Vérification du 2026-10-14 : les fichiers EN et FR des deux tables ont les mêmes lignes (1 152 913 et 141 432), les mêmes identifiants `VECTOR` et les mêmes valeurs, avec 0 écart.
- Les formats diffèrent : séparateur « , » en anglais, « ; » en français, noms de colonnes traduits, BOM UTF-8 dans les deux cas. Une seule source évite de lire deux fois les mêmes chiffres et le risque de résultats différents selon la langue.

**Alternatives écartées.** Faire l'analyse deux fois, une par langue (deux fois plus de travail et un risque d'écart) ; traduire les libellés à la main (les libellés français officiels de StatCan existent déjà).

## D17 — Quelles séries utiliser pour chaque épisode tarifaire [décidé]
**Décision.** Une série de l'IPC n'est utilisée pour un épisode que si elle a **au moins 36 mois de données avant le premier mois du tarif** et au moins un mois après. Les séries qui commencent trop tard sont remplacées par leur agrégat parent. La règle est codée dans `src/cpi_catalog.py` (`MIN_PRE_MONTHS`).

**Justification.**
- Un contrôle synthétique n'est crédible que s'il reproduit la série traitée sur une longue période avant le traitement ; avec une période courte, un bon ajustement peut être obtenu par hasard [M2].
- Les séries alimentaires de l'IPC sont très saisonnières (surtout les fruits et légumes frais). Trois cycles annuels complets sont le minimum retenu pour séparer la saisonnalité de la tendance [F1].
- Appliqué aux données (notebook 01) : 106 séries sont retenues pour 2018 et 101 pour 2025. Exclues pour 2025 : les 15 coupes de viande (base 2024-04, seulement 11 mois avant) et les 8 séries de fruits et légumes frais (base 2023-04, 23 mois avant) ; 5 séries arrêtées en 2021-05 n'ont aucune donnée après mars 2025. Pour 2026, 114 séries ont assez d'historique, mais **aucune donnée postérieure aux tarifs n'existe encore** : le dernier mois publié est août 2026, et l'IPC de septembre 2026 paraît le 19 octobre 2026 [S7].

**Conséquences.** L'analyse de 2026 ne peut commencer qu'une fois plusieurs mois postérieurs aux tarifs publiés (septembre le 19 octobre, octobre le 16 novembre, novembre le 14 décembre 2026 [S7]). D'ici là, on travaille sur 2018 et 2025 (étapes 3 et 4).

**Alternatives écartées.** 24 mois (ferait entrer les 15 coupes de viande dans l'épisode 2026 avec seulement 29 mois d'historique, environ deux cycles) ; 48 ou 60 mois (retirerait de l'épisode 2026 les 8 séries de fruits et légumes frais, qui ont 41 mois d'historique, sans rien changer pour 2018 ni 2025).

## D18 — Séries traitées, placebo et témoins pour chaque épisode tarifaire [décidé]
**Décision.** Rattacher chaque ligne tarifaire alimentaire des listes officielles à la série de l'IPC où le produit est relevé, puis donner à chaque série alimentaire de l'IPC un rôle par épisode :
- **traitée** : les produits de détail taxés forment une part importante de la série, à un taux qui s'applique réellement (exposition `direct`) ;
- **placebo** : seules les importations hors contingent ont été taxées (exposition `over_quota_only`) ; sert de test de falsification ;
- **exclue** : les produits taxés sont une part faible ou incertaine de la série (`partial`), seulement un ingrédient (`input`), la série est un agrégat qui contient des séries exposées, ou elle a été exposée à un autre épisode situé dans la fenêtre d'estimation ;
- **témoin** : tout le reste des aliments achetés en magasin. Les aliments achetés au restaurant sont hors champ.

Fichiers : `data/reference/tariff_hs6_food.csv` (listes au niveau SH à 6 chiffres), `data/reference/tariff_cpi_map.csv` (correspondance avec niveau de confiance et notes EN/FR), `src/tariff_map.py`, notebook 02.

**Justification.**
- Seuls les textes officiels disent ce qui a été taxé. Lignes alimentaires (chapitres SH 01 à 24) : **2018**, 25 lignes dans 18 sous-positions à 10 % [R10], inchangées par la modification d'avril 2019, qui ne retire que les bateaux [R11], et abrogées le 2019-05-19 [R9] ; **2025**, 407 lignes dans 183 sous-positions à 25 % [R7], toutes levées le 2025-09-01 (la liste en vigueur à partir de cette date ne contient aucune ligne alimentaire [R7]) ; **2026**, 66 lignes dans 15 sous-positions [R7] : fromages à 25 % ; poudres de lait, lactosérum, miel, mélasse et mélanges pour boulangerie à 50 %. L'alcool, le tabac, les animaux vivants et les aliments pour animaux sont hors de l'IPC alimentaire (120 lignes en 2025, 1 en 2018).
- Les produits sous gestion de l'offre ont des contingents tarifaires. Les importations américaines dans le contingent entrent en franchise ; au-delà, elles paient déjà environ 241 % (lait), 298,5 % (beurre) ou 245,5 % (fromage) [S9]. En 2025, le lait, le beurre, le fromage, les œufs en coquille et la crème glacée n'étaient taxés **qu'au-delà du contingent** : les 25 % supplémentaires ne devraient rien changer. Traiter ces séries comme des placebos teste la méthode : un effet « significatif » sur elles révélerait un défaut [M2].
- Les séries exposées seulement en partie ou par leurs intrants dilueraient l'effet si on les traitait, et contamineraient les témoins si on les utilisait comme donneurs ; les deux cas violent l'hypothèse d'absence d'interférence du contrôle synthétique et des doubles différences [M2, M3]. Le canal des intrants est réel [R4] : ces séries restent donc hors des deux groupes.
- La fenêtre d'estimation de 2026 (36 mois avant, D17) commence en 2023-09 et contient l'épisode de 2025 : 50 séries exposées en 2025 ne sont donc pas des témoins pour 2026.
- **Constat pour 2026.** Le tarif « laitier » de 50 % vise les poudres de lait et le lactosérum, qui sont des ingrédients. Le lait frais, le beurre, le yogourt et la crème glacée ne sont pas sur la liste. Seul le fromage est taxé directement. Cela appuie l'hypothèse de D06 : l'effet sur les produits laitiers en magasin passerait surtout par les intrants [R6].
- Résultat (séries avec assez d'historique et des données après le tarif) : 2018, 10 traitées et 71 témoins ; 2025, 22 traitées, 11 placebos et 28 témoins ; 2026, 5 traitées (le fromage et ses 4 sous-séries, en attente des données après le tarif, D17) et 39 témoins.

**Hypothèses vérifiées (2026-10-14).**
- *Le yogourt est relevé dans Autres produits laitiers* : **confirmé par élimination.** Le yogourt est un produit représentatif de l'IPC [S11] ; *Produits laitiers* compte exactement cinq sous-séries (lait frais, beurre, fromage, crème glacée, autres produits laitiers) et le yogourt n'est aucune des quatre premières. StatCan ne publie pas le contenu de chaque série : c'est la vérification la plus solide possible. *Autres produits laitiers* comptait environ 3 produits représentatifs dans le panier de 2014 [S10] : l'effet de 2018 y est dilué, et l'étape 4 donne donc les résultats avec et sans cette série.
- *Le miel est relevé dans Sucre et sirop* : **impossible à vérifier** (en 2014, la série n'avait qu'un produit représentatif [S10] ; le miel est aujourd'hui un produit représentatif [S11], classe non publiée). **Aucun rôle n'en dépend** : en 2025, la série est traitée par le sucre et le sirop d'érable ; en 2026, elle reste exclue car la mélasse est un intrant. Confiance abaissée à `low` pour 2026.

**Alternatives écartées.** Pondérer chaque série par sa part d'importations américaines : plus précis, mais cela demande une table de passage entre codes SH et séries de l'IPC qui n'est pas publique ; gardé comme test de robustesse possible. Traiter tous les produits laitiers de 2025 comme traités : ignore les contingents et biaiserait l'estimation de 2025 vers zéro.

## D19 — Plan d'estimation pour reproduire 2018 et 2025 [décidé]
**Décision.**
- **Variable étudiée** : 100 × log de l'IPC, désaisonnalisé (facteurs par mois calendaire estimés sur la seule période avant le tarif) et centré sur la moyenne d'avant. Les résultats sont en % (points de log).
- **Fenêtres** : 60 mois avant le tarif pour l'ajustement (≥ 36, D17) ; *pendant* = mois où le tarif s'applique (2018-07 à 2019-05 ; 2025-03 à 2025-08) ; *après* = jusqu'à 12 mois après la levée, arrêté avant mars 2020 pour 2018 (pandémie).
- **Contrôle synthétique** pour chaque série traitée : poids ≥ 0 de somme 1, ajustés sur la période avant [M1, M2]. Donneurs = témoins de D18 au niveau le plus fin, pour qu'une série et son parent ne soient jamais ensemble dans le groupe (52 donneurs pour 2018, 22 pour 2025).
- **Inférence** : permutation dans l'espace, c'est-à-dire le même estimateur appliqué à chaque donneur ; p-valeur = rang du ratio RMSPE après/avant [M1].
- **Robustesse** : doubles différences 2×2 et étude d'événement, avec effets fixes série et mois, erreurs types groupées par série. Chaque épisode a une seule date de début : les effets fixes doubles ne subissent donc pas le biais des traitements échelonnés [M3].
- **Lecture** : `rho` = effet ÷ taux du tarif = transmission × part des produits américains taxés dans la série. Ce n'est pas un taux de transmission à lui seul.

**Justification.** La spécification a été choisie sur la qualité de l'ajustement avant le tarif, un critère fixé avant de regarder les effets [M2]. Retirer la saisonnalité et centrer sur la moyenne d'avant (ce qui joue le rôle d'un effet fixe par série [M4]) fait baisser la RMSPE médiane avant le tarif des séries traitées de 1,32 à 1,07 point (2018) et de 2,87 à 2,11 points (2025), par rapport à un ancrage de chaque série sur le dernier mois avant le tarif. Les deux spécifications sont gardées dans le notebook 03.

**Alternatives écartées.** Ancrage sur le dernier mois avant le tarif (ajustement moins bon, un seul mois bruité oriente toute la trajectoire) ; une fenêtre avant plus courte (D17) ; les doubles différences synthétiques [M4] comme estimateur principal (gardées pour plus tard : avec 22 donneurs en 2025, le gain est faible face au problème de puissance de D20).

## D20 — Résultats de la reproduction 2018 et 2025 : aucun effet détectable avec les sous-indices publics de l'IPC [décidé]
**Constats (notebook 03, spécification D19).**

| | 2018 (surtaxe de 10 %) | 2025 (contre-tarifs de 25 %) |
|---|---|---|
| Contrôle synthétique, effet moyen pendant le tarif | −1,8 % (0 série sur 10 avec p < 0,10) | +1,1 %, médiane −0,2 % (2 sur 22 avec p < 0,10) |
| Doubles différences, effet moyen pendant le tarif [IC 95 %] | −1,9 [−4,4 ; +0,7] | +2,1 [−1,6 ; +5,8] |
| Effet minimal détectable (puissance 80 %) | 3,6 points | 5,3 points |
| Séries placebo (produits laitiers et œufs hors contingent) | — | −2,4 % en moyenne ; doubles différences −2,0 [−4,9 ; +0,9] |

- **2018.** Aucune hausse de prix n'est détectable dans les séries traitées ; l'étude d'événement les montre même un peu sous les témoins des mois 1 à 5 (deux mois avec p < 0,05). Retirer *Autres produits laitiers* (série large, D18) ne change rien (−1,8 [−4,5 ; +0,9]).
- **2025.** La moyenne positive vient du café (+18,2 %, p = 0,04) et de la confiserie (+3,9 %, p = 0,09). Les deux ont bougé pendant de fortes hausses des cours mondiaux du café et du cacao, que les séries canadiennes témoins ne peuvent pas reproduire. Sans eux, les doubles différences tombent à +1,0 [−2,3 ; +4,3]. Avec seulement les rattachements de confiance élevée, l'effet est de +4,0 [−0,1 ; +8,0]. L'étude d'événement montre des séries traitées déjà 1 à 2 points au-dessus des témoins dans les 10 mois avant le tarif : l'hypothèse de tendances parallèles est donc douteuse.
- **Falsification.** Les séries placebo, qui devraient être à zéro, sont en moyenne 2,4 % sous leur contrôle synthétique (fromage p = 0,04). Les prix laitiers suivent leur propre dynamique réglementée, que des donneurs non laitiers ne captent pas. Les p-valeurs individuelles proches de 0,05 ne sont donc pas des preuves fiables ici ; avec 22 tests, on attend de toute façon environ un faux positif à 5 %.

**Comparaison avec la littérature (D02).** R3 trouve une transmission d'environ 70 % pour l'alimentation en 2018. Une surtaxe de 10 % transmise à 70 % ne ferait bouger une série large de l'IPC au-delà de notre borne haute (+0,7 %) que si les produits américains taxés pèsent plus d'environ 10 % de cette série. R1/R2 trouvent une transmission d'environ 25 % en 2025. Notre `rho` de 2025 (0,04 en contrôle synthétique, 0,08 en doubles différences, borne haute 0,23) est compatible avec 25 % × la part américaine. **Nous ne confirmons ni ne contredisons les estimations de la Banque du Canada. Les sous-indices mensuels publics sont trop agrégés pour détecter des effets de cette taille.** C'est un résultat en soi, et il explique pourquoi R1/R2/R3 utilisent des données par produit ou des microdonnées.

**Conséquences.**
1. On ne peut pas annoncer de taux de transmission sans pondération par l'exposition. Prochaine étape : estimer la part américaine de chaque série de l'IPC à partir des données commerciales de Statistique Canada (importations par code SH) et de l'offre intérieure, puis convertir les effets en taux de transmission.
2. Contrôler les cours mondiaux (café, cacao, oranges) avant de lire les hausses du café et de la confiserie en 2025 comme des effets du tarif.
3. Pour 2026, les séries de fromage sont le cas le plus favorable (25 % sur toutes les lignes, dans et hors contingent). La précision restera limitée : publier l'effet minimal détectable à côté de chaque estimation.

**Alternatives écartées.** Ne présenter que les séries significatives (le café) comme preuve de transmission : les tests multiples, un facteur confondant mondial et un placebo raté s'y opposent.

## D21 — Transmission à partir d'effets pondérés par l'exposition [décidé]
**Décision.** Convertir les effets en taux de transmission comparables à ceux de la Banque du Canada [R1–R3] :
- **Exposition** de chaque série traitée `s` = importations américaines de ses sous-positions SH6 taxées (UN Comtrade [S12], année avant le tarif : 2017 ou 2024, converties au taux USD/CAD annuel) ÷ dépense des ménages pour la série (poids dans le panier de l'IPC [S13] ÷ poids des aliments achetés en magasin × dépense de consommation finale des ménages en aliments et boissons non alcoolisées [S14], même année). Les sous-positions taxées seulement hors contingent sont exclues (D18).
- **Estimation principale** : doubles différences à traitement continu, dose = 100 × tarif × `s` (0 pour les témoins), effets fixes série et mois, erreurs types groupées par série [M3, M5]. Le coefficient est le taux de transmission.
- Code : `src/fetch_trade.py`, `src/causal/exposure.py` ; résultats : notebook 04.

**Justification.**
- Un effet sur une série large de l'IPC mélange la transmission et la part des produits américains taxés dans cette série ; seul le rapport des deux est comparable à R1–R3.
- L'exposition est faible : `s` médian = 0,12 en 2018 et 0,09 en 2025. Avec une transmission complète, l'effet moyen attendu ne serait que de 1,4 point (2018) et 3,0 points (2025), sous les effets minimaux détectables de D20 (3,6 et 5,3 points). Cela explique pourquoi D20 n'a rien trouvé.

**Résultats.**

| | Transmission [IC 95 %] |
|---|---|
| 2018, les 10 séries traitées | −0,96 [−2,45 ; +0,54] |
| 2018, séries avec leur propre poids seulement (6) | −0,16 [−1,05 ; +0,73] |
| 2025, les 22 séries traitées | +0,83 [−0,11 ; +1,78] |
| 2025, sans le café ni la confiserie (20) | +0,35 [−0,12 ; +0,81] |
| 2025, séries avec leur propre poids seulement (17) | +0,27 [−0,19 ; +0,73] |

- **2025** : toutes les variantes contiennent les ~25 % de R1/R2. L'estimation au-dessus de 80 % avec toutes les séries vient du café et de la confiserie (chocs de prix mondiaux, D20).
- **2018** : l'estimation principale exclut les 70 % de R3 au seuil de 5 %, mais pas la variante limitée aux séries qui ont leur propre poids. Une transmission négative n'a pas de sens économique ; elle signale une dynamique intérieure que les témoins ne captent pas. **Aucune conclusion contre R3 n'est tirée.**

**Biais connus.** Les importations sont à la valeur à la frontière, la dépense est au prix de détail (sous-estime `s`) ; les importations vont aussi aux restaurants et aux transformateurs (surestime `s`). Cinq codes SH6 sont plus larges que les lignes taxées à 8 chiffres (`hs6_broader`, `s` est alors une borne haute) ; huit séries détaillées utilisent le poids d'une série parente (sous-estime `s`). Les poids du panier sont arrondis à 0,01 %, ce qui est grossier pour les petites séries.

**Alternatives écartées.** Les données commerciales de Statistique Canada à 8 ou 10 chiffres par pays supprimeraient le biais des codes trop larges, mais elles ne sont pas accessibles par une API ouverte ; UN Comtrade à 6 chiffres est public et reproductible. La part des États-Unis dans les importations totales : elle ignore la production intérieure, qui domine beaucoup de séries alimentaires.

## D22 — Contrôler les cours mondiaux des matières premières [décidé]
**Décision.** Pour les 12 séries traitées liées à une matière première mondiale (`data/reference/commodity_map.csv` : café, cacao, oranges, sucre, huile de colza, riz, blé, thé, arachides), retirer la composante due aux cours mondiaux avant d'estimer les effets :
- cours mondiaux : « Pink Sheet » de la Banque mondiale, mensuel [S15], convertis en dollars canadiens (D15) ;
- élasticités estimées sur les **variations sur 12 mois** (en log), retards de 0 à 11 mois en quatre blocs, sur tous les mois avant le tarif depuis 2005 ;
- la composante obtenue est retirée de la série, puis le contrôle synthétique (D19) et les doubles différences de transmission (D21) sont relancés. Code : `src/fetch_commodities.py`, `src/causal/commodity.py` ; résultats : notebook 05.

**Justification.** Le Canada subit les cours mondiaux sans les influencer : ils ne dépendent pas des tarifs canadiens et peuvent être retirés sans biaiser l'effet du tarif. Les variations sur 12 mois éliminent la saisonnalité et les fausses tendances de niveau ; la longue fenêtre couvre plusieurs cycles des matières premières.

**Résultats.**
- Les élasticités sont plausibles : café 0,16, blé → farine 0,19, blé → pâtes 0,24, sucre 0,27, huile de colza → margarine 0,15.
- **Café 2025** : l'arabica en dollars canadiens a environ doublé entre la mi-2024 et le début de 2025. Il explique 7,1 des 18,2 points d'écart ; l'écart corrigé (11,2 points, p = 0,04) dépasse encore les 7,1 points qu'une transmission complète du tarif produirait (D21), et il reste élevé **après** la levée du tarif (14,5 points de septembre 2025 à août 2026). Un effet du tarif s'effacerait à sa levée ; celui-ci ne s'efface pas. La hausse du café est donc lue comme un effet des cours mondiaux que la structure de retards de 0 à 17 mois ne capte pas entièrement, **et non** comme une transmission du tarif.
- **Transmission 2025** : toutes les séries, corrigées, 0,69 [0,01 ; 1,38] (retards 0–11) et 0,62 [0,03 ; 1,20] (retards 0–17). Ce sont les seules estimations significatives à 5 %, et elles reposent sur le café. **Estimation retenue : sans le café ni la confiserie, après correction : 0,39 [−0,07 ; 0,86]** (0,44 [−0,05 ; 0,93] avec retards 0–17). Elle contient les ~25 % de R1/R2 et exclut une transmission supérieure à environ 90 %.
- **2018** : inchangé, −0,94 [−2,44 ; +0,56].

**Règle utilisée pour l'estimation retenue (énoncée avant de la publier).** Une série est jugée contaminée quand son effet corrigé dépasse l'effet attendu à transmission complète et persiste après la levée du tarif. Seul le café remplit les deux conditions ; la confiserie est retirée avec lui car le cacao a connu son propre choc record en 2024–2025 et son élasticité corrigée est quasi nulle (R² 0,02), donc la correction n'y est pas fiable.

**Alternatives écartées.** Une première version régressait l'écart du contrôle synthétique sur les cours, sur la seule fenêtre de 60 mois avant le tarif. Elle était instable : la correction des oranges déplaçait l'effet de 16 points, et l'élasticité du café sortait à 0,04, faute de variation suffisante des cours dans la fenêtre. La comparaison avec l'IPC américain pour les mêmes produits : les États-Unis ont imposé leurs propres tarifs aux pays producteurs de café en 2025, ce n'est donc pas un témoin propre.

## D23 — Résultats des prévisions et intervalles [décidé]
**Décision.** Publier des prévisions à 12 mois pour les 101 séries alimentaires nationales de l'IPC qui commencent au plus tard en 2014 et vont jusqu'au dernier mois, avec le modèle choisi par D24 et des intervalles conformes à 80 % et 95 % par horizon. Code : `src/forecast/models.py` ; résultats : notebook 06.

**Résultats (origine glissante, 27 origines de 2019-01 à 2025-08, horizons 1 à 12) [F3].**

| Modèle | MASE | sMAPE (%) |
|---|---|---|
| LightGBM, global | 1,28 | 3,2 |
| ETS, par série | 1,37 | 3,4 |
| Naïf saisonnier (référence) | 2,16 | 5,2 |

- Les deux modèles battent la référence à tous les horizons [F1, F2]. ETS est le meilleur à 1 mois (MASE 0,61 contre 0,65) ; LightGBM fait mieux à partir de 3 mois. ETS est 6 % au-dessus de LightGBM au total, au-delà de la marge de 5 % de D24 : LightGBM est donc publié.
- Les intervalles conformes calibrés sur les origines 2019–2022 couvrent 85–87 % (cible 80 %) et 96–97 % (cible 95 %) des valeurs de 2023–2025 : légèrement prudents, comme attendu après la poussée d'inflation de 2022 [F4].
- Le MASE dépasse 1 aux horizons longs car l'échelle est l'erreur naïve à un an mesurée sur l'historique ; la poussée d'inflation de 2021–2023 fait rater tous les modèles à 12 mois.

**Alternatives écartées.** Un seul découpage entraînement/test (une seule période déciderait de tout, F3) ; des intervalles tirés des résidus du modèle (ils supposent une loi et n'étaient pas vérifiés).

## D24 — Méthodes explicables et présentation sobre [décidé]
**Décision.**
- **Prévisions** : la prévision publiée utilise le modèle le plus simple dont le MASE moyen est à moins de 5 % du meilleur, dans l'ordre naïf saisonnier, ETS, LightGBM. LightGBM reste dans le backtest comme point de comparaison.
- **Assistant** : un onglet de questions fondé sur un ensemble fixe de réponses bilingues vérifiées (`app/faq.py`), chacune citant sa décision et sa source, trouvées par mots-clés communs. Aucun modèle de langage.
- **Présentation** : aucun emoji nulle part (application, README, journaux) ; les statuts sont des mots ([décidé], [à confirmer], verified, to check). Graphiques minimalistes avec les mêmes cinq couleurs.
- **Données de l'application** : un petit jeu dérivé dans `app/data/` (produit par `src/build_app_data.py`), pour que l'application fonctionne sans les fichiers bruts.

**Justification.**
- Le projet est une pièce de portfolio : chaque méthode doit pouvoir être expliquée à un non-spécialiste en quelques phrases. À précision proche, la prévision la plus simple est préférée, ce qui est une pratique courante [F1].
- Un assistant à réponses fixes ne peut pas inventer de chiffres ; son comportement est entièrement prévisible et testable. L'objectif de fiabilité de D11 est tenu sans modèle à surveiller.
- Un style sobre garde l'attention sur les résultats et fait professionnel.

**Alternatives écartées.** Un assistant LLM avec outils (D11) : plus souple, mais il demande une clé API, un suivi et un jeu d'évaluation avant d'être fiable ; gardé pour une version ultérieure. Publier toujours le modèle le plus précis : le gain par rapport à ETS doit être assez grand pour justifier une explication plus difficile.

## D25 — Mise à jour mensuelle, vérifications automatiques et abandon de l'étude détaillée du fromage 2026 [décidé]
**Décision.**
- **Mise à jour mensuelle** : une commande, `python src/refresh.py`, lancée après chaque publication de l'IPC (calendrier [S7]) : téléchargement, catalogue et rôles, prévision publiée avec les quantiles conformes du notebook 06, scénarios du fromage, données de l'application. Les estimations causales historiques ne sont pas recalculées.
- **Vérifications automatiques** : 12 tests dans `tests/` (nombre de lignes officielles, validité des correspondances, comportement des estimateurs sur des cas connus, quantile conforme, données de l'application, absence d'emojis), lancés avec `pytest -q` sans les données brutes.
- **Références** : chaque DOI a été résolu sur doi.org et son titre, premier auteur et année Crossref comparés à `docs/references.md` (tous concordent) ; les références arXiv et web ont été ouvertes. Seule l'année de publication de S10 reste à vérifier.
- **Fromage 2026** : pas d'étude causale dédiée (ancienne étape 4c). La mise à jour mensuelle tient la série du fromage et les scénarios à jour.

**Justification.**
- Un suivi n'est utile que s'il est mis à jour ; une seule commande garde la mise à jour explicable et reproductible.
- Avec une exposition de 0,024, une transmission complète n'ajoute au plus que 0,6 point à l'IPC du fromage (D06), pour un effet minimal détectable de plusieurs points (D20) : une étude dédiée conclurait « non détectable » par construction.
- Les tests détectent les erreurs silencieuses : le premier passage a trouvé un mot-clé de la FAQ (« 4l ») trop court pour être jamais reconnu.

**Alternatives écartées.** Une tâche planifiée dans le cloud (demande un dépôt public et des secrets ; possible plus tard). Recalculer toutes les estimations causales chaque mois : elles portent sur des épisodes terminés et ne changeraient pas.

## D26 — Fonctions grand public : coût pour le ménage, recherche de produits, provinces, thème clair et sombre [décidé]
**Décision.** Faire répondre l'application aux questions d'un non-spécialiste, avec les mêmes méthodes explicables :
- **Ce que ça me coûte** : coût = dépenses mensuelles d'épicerie × taux du tarif × part répercutée × part des dépenses alimentaires sur des produits américains taxés. Pour 2025 : taux 25 %, part répercutée 39 % (fourchette 0–86 %, D22), part des dépenses 5,3 % (fourchette 2,6–7,5 %) : environ **0,52 dollar par 100 dollars d'épicerie** pendant l'application des tarifs, soit environ 0,5 point sur les 1,8 % de hausse des prix en magasin entre février et août 2025. Pour 2026 : taux pondéré par les importations de 43 %, part des dépenses 0,4 %, scénarios de transmission de 25 à 70 % (D06).
- **Est-ce taxé ?** : une recherche dans les listes officielles rattachées aux séries de l'IPC (D18), en anglais et en français, insensible aux accents.
- **Provinces** : variation sur 12 mois de l'IPC des aliments achetés en magasin pour les dix provinces, Whitehorse et Yellowknife (D13).
- **Bandeau des dernières données**, **méthode en langage simple**, **téléchargements** et **mention de citation** ; auteur affiché : David Doe, étudiant en data science, Université de Lille.
- **Thème clair et sombre** au choix dans la barre latérale ; les mêmes cinq couleurs, ajustées à chaque fond.

**Justification.**
- La part des dépenses est le rapport entre les importations américaines des lignes alimentaires taxées (UN Comtrade [S12]) et les dépenses des ménages en aliments et boissons non alcoolisées (2024, [S14]). Valeur centrale : lignes rattachées aux séries traitées de l'IPC (D21) ; basse : codes à 6 chiffres exacts seulement ; haute : toutes les lignes alimentaires taxées, ingrédients compris. La fourchette est toujours affichée, jamais un chiffre seul.
- C'est une estimation pour un ménage moyen : les valeurs à la frontière sous-estiment les valeurs au détail, et un panier riche en produits américains coûte davantage. Les deux réserves sont écrites à côté du résultat.
- Les tableaux sont rendus en HTML simple pour suivre le thème choisi.

**Alternatives écartées.** Un coût par panier de produits choisi par l'utilisateur (demande des parts américaines par produit qui ne sont pas publiques) ; une carte des provinces (un diagramme en barres trié compare les valeurs plus précisément).

## D27 — Contexte, note mensuelle, vues partageables et détail du panier [décidé]
**Décision.**
- **Section Contexte en premier** : la situation (épisodes de 2018, 2025 et 2026, prix alimentaires), le problème (les ménages ne voient pas ce que les tarifs leur coûtent ; les estimations officielles reposent sur des données non publiques) et ce que fait le projet, chaque fait relié à R1–R10.
- **Note mensuelle** : un paragraphe rempli automatiquement à partir de la dernière publication (variation sur 12 mois et sa direction, restaurants, trois plus fortes hausses et baisses parmi les séries détaillées, écart entre provinces, prévision). Aucun texte n'est écrit à la main ni par un modèle.
- **Vues partageables** : chaque section, langue, thème, recherche de produit et montant d'épicerie est conservé dans l'adresse (`?section=cost&lang=fr&bill=1500`), et une image de synthèse de 1200 × 630 est générée dans les deux langues.
- **Détail du panier (2025)** : les dix catégories taxées avec le plus d'importations américaines, plus « autres produits taxés », chacune avec sa propre part de produits américains (D21) ; l'utilisateur peut modifier les montants.

**Justification.** Un non-spécialiste doit comprendre pourquoi la question compte avant de lire les résultats ; une note datée donne une raison de revenir ; les liens et l'image rendent le travail facile à partager ; le détail du panier répond à « et si j'achète beaucoup de café ? » avec la même méthode en une ligne. Le panier aux montants du ménage moyen donne 5,15 dollars par mois pour 1 000 dollars, cohérent avec les 5,20 globaux (D26), et un test vérifie que l'écart reste sous 10 %.

**Alternatives écartées.** Un texte rédigé par un modèle pour la note mensuelle (non reproductible, risque de chiffres inventés) ; des balises d'aperçu pour les réseaux sociaux (non configurables sur Streamlit Community Cloud ; l'image est proposée au téléchargement à la place).

## D28 — Assistant IA optionnel fondé sur les faits du tableau de bord, avec jeu d'évaluation [décidé, évaluation en perspective (D34)]
**Décision.** Ajouter un assistant qui répond aux questions formulées librement, par un seul appel à Claude (`claude-opus-5-5`, effort faible, repli côté serveur en cas de refus), à partir d'un texte fixe des faits vérifiés du tableau de bord (dernières données, coûts, transmission, effets par série, listes tarifaires, provinces, prévisions, FAQ vérifiée, contexte). Il doit répondre uniquement à partir de ces faits, garder les fourchettes, citer les numéros de décision, et le dire quand les faits ne couvrent pas une question. Il n'est activé que si une `ANTHROPIC_API_KEY` est configurée dans les secrets Streamlit ; sinon la FAQ à réponses fixes reste le seul mode. Limites : 500 caractères par question, 10 questions par visite.

**Évaluation.** 20 questions bilingues (`data/reference/assistant_eval.csv`) : 16 avec des faits attendus, 4 hors champ qui doivent être déclinées sans chiffre. `python src/eval_assistant.py` note chaque réponse par mots-clés attendus (insensible aux accents) et enregistre les résultats. **Pas encore lancée : il faut une clé API.** L'assistant ne doit être présenté comme fiable qu'une fois ce taux publié.

**Justification.** Cela réalise D11 sans renoncer à D24 : le modèle ne voit ni internet ni les données brutes, seulement des faits déjà vérifiés et affichés dans l'application, et ses réponses peuvent donc être contrôlées sur le tableau de bord. Le texte des faits est déterministe (sans horodatage, trié) : le préfixe d'environ 5 000 jetons est mis en cache et chaque question coûte peu.

**Alternatives écartées.** Des outils qui interrogent librement les données (plus souple, plus difficile à vérifier) ; un assistant toujours actif sans vérification de clé (risque de coût et d'abus).

## D29 — TALN : classer les séries de l'IPC pour chaque ligne tarifaire [décidé, étape LLM en perspective (D34)]
**Décision.** Pré-rattacher toute nouvelle liste tarifaire aux séries de l'IPC par des méthodes de texte, évaluées contre la correspondance manuelle de D18 (vérité terrain : 151 sous-positions SH6 alimentaires, dont 135 avec une série de l'IPC, 123 séries candidates). Les libellés douaniers viennent de la nomenclature SH d'UN Comtrade. Méthodes, de la plus simple à la plus avancée : TF-IDF sur n-grammes de mots et de caractères [N10] ; embeddings de phrases multilingues (paraphrase-multilingual-MiniLM-L12-v2) [N2, N3] ; leur combinaison (moyenne de scores standardisés fixée d'avance, et Reciprocal Rank Fusion [N4]) ; puis, avec une clé API, Claude choisit une série parmi les 5 candidates grâce à un schéma JSON qui n'autorise que ces candidates ou « aucune ». Code : `src/nlp/hs_cpi_classifier.py` ; résultats : notebook 07.

**Résultats** (strict = série exacte ; intervalles bootstrap à 95 % [N8]) :

| Méthode | Top-1 | Rappel@5 | MRR |
|---|---|---|---|
| TF-IDF | 39 % [31 ; 48] | 73 % [65 ; 80] | 0,54 |
| Embeddings | 36 % [27 ; 44] | 72 % [64 ; 79] | 0,51 |
| Hybride (poids fixes) | 38 % [30 ; 46] | **81 % [74 ; 87]** | 0,55 |
| RRF | **44 % [36 ; 53]** | 79 % [71 ; 85] | **0,58** |

- La liste courte hybride bat TF-IDF sur le rappel@5 (test exact de McNemar [N9], p = 0,007) ; les embeddings seuls non (p = 1,0). Avec la mesure tolérante (parent ou enfant accepté), les embeddings placent la bonne famille dans les 5 premières propositions pour 96 % des lignes : ils trouvent la bonne branche, pas le bon niveau.
- Analyse des erreurs : 32 des 84 erreurs en première position sont des erreurs de niveau (par exemple *Herbes et épices* au lieu de son parent *Condiments, épices et vinaigres*), corrigées en un clic. Les 52 autres demandent une connaissance du domaine qui manque aux modèles : *Gallus domesticus* est le poulet ; les poudres de lait et le yogourt relèvent des *Autres produits laitiers* ; l'huile de colza est le canola. C'est le rôle de l'étape LLM, codée mais **pas encore mesurée** (pas de clé API).
- Usage : un relecteur vérifie 5 propositions au lieu de 123 séries ; le meilleur poids trouvé dans le tableau de sensibilité n'est pas utilisé, pour ne pas régler la méthode sur les lignes de test.

**Alternatives écartées.** Entraîner un classifieur supervisé (135 lignes étiquetées sont trop peu, et chaque nouvelle liste apporte de nouveaux produits) ; demander au LLM de choisir parmi les 123 séries sans liste courte (prompts plus longs, plus difficiles à auditer).

## D31 — Entrepôt SQL, intégration continue et outils des équipes data [décidé]
**Décision.**
- **SQL** : un entrepôt DuckDB (`src/sql/warehouse.py`) avec des tables de dimensions et de faits (séries, IPC, prévisions, provinces, lignes tarifaires, correspondance, exposition) et cinq questions métier traitées en SQL dans des fichiers lisibles (`sql/*.sql`) : CTE, jointures, fonctions de fenêtre (LAG, RANK, sommes cumulées), agrégation conditionnelle, QUALIFY.
- **Intégration continue** : GitHub Actions lance les tests à chaque envoi (`.github/workflows/tests.yml`, dépendances légères dans `requirements-ci.txt`).
- **Vocabulaire du métier relié au projet** : recherche hybride (BM25 + vecteurs + RRF), reclassement par cross-encoder, embeddings, sorties structurées, évaluation de RAG, cache de prompts, prédiction conforme, backtest, inférence causale, tests placebo et de permutation.

**Justification.** SQL, tests automatisés et chaînes reproductibles sont demandés dans la plupart des offres en data ; les montrer sur les données du projet convainc davantage qu'un exercice séparé. Les requêtes ont aussi produit des constats : quatre catégories taxées portent les deux tiers du coût de 2025 (boulangerie, condiments, boissons, confiserie), et les prévisions attendent un retour vers la moyenne après les plus fortes variations (bacon, oranges, pâtes).

**Limite découverte grâce au SQL.** Les intervalles conformes ont la même largeur relative pour toutes les séries à un horizon donné (14,1 % à 12 mois pour 80 %), car ils sont calibrés sur toutes les séries ensemble (D23). Une prédiction conforme par groupe de séries (« Mondrian ») corrigerait cela ; notée comme prochaine étape.

**Alternatives écartées.** Un entrepôt infonuagique (coût et comptes pour un projet de portfolio) ; LangChain ou LlamaIndex pour la recherche (pratiques, mais coder BM25, RRF et l'évaluation montre les mécanismes ; les mêmes briques existent dans ces bibliothèques).

## D30 — RAG : recherche dans les documents officiels, avec réponses citées [décidé, en pause dans l'application depuis D32]
**Décision.** Une fonction de recherche documentaire qui retrouve des passages de sources officielles et, avec une clé API, rédige une réponse courte qui les cite [A1]. Corpus : 765 passages d'environ 1 000 caractères (chevauchement de 150) tirés des études de la Banque du Canada R1–R4 (réutilisation permise avec attribution), des ordonnances de la Gazette du Canada R9–R11 et des documents de Statistique Canada S3, S10 (Licence du gouvernement ouvert – Canada), ainsi que des journaux de décisions et résumés du projet ; les sources commerciales sont exclues. Chaque passage est indexé avec le titre de son document en tête (en-tête de contexte). Code : `src/rag/build_corpus.py`, `app/rag.py`, `src/rag/eval_rag.py` ; résultats : notebook 08.

**Évaluation** (16 questions, 10 en anglais et 6 en français, pertinence binaire = document attendu + mot-clé attendu ; intervalles bootstrap à 95 % [N8]) :

| Configuration | Rappel@1 | Rappel@5 | MRR [IC 95 %] | nDCG@5 [N7] |
|---|---|---|---|---|
| BM25 [N1] | 56 % | 69 % | 0,64 [0,43 ; 0,85] | 0,47 |
| Embeddings multilingues [N2, N3] | 50 % | **94 %** | 0,65 [0,46 ; 0,83] | 0,43 |
| RRF des deux [N4], sans titres | 50 % | 63 % | 0,57 [0,34 ; 0,78] | 0,33 |
| RRF des deux, avec titres | 56 % | 81 % | 0,63 [0,43 ; 0,84] | 0,46 |
| RRF + reclassement par cross-encoder [N5, N6] | **75 %** | **94 %** | **0,81 [0,62 ; 0,95]** | **0,68** |

- Le reclassement est le meilleur sur toutes les mesures et corrige les questions en français (rappel@1 de 83 % contre 33 % pour RRF), mais son gain sur RRF n'est pas significatif avec 16 questions (test de randomisation apparié, p = 0,12) : il faut un jeu de questions plus grand pour le démontrer.
- RRF échoue sur les questions en français parce que BM25 ne peut pas apparier des mots français à des documents anglais et tire la fusion vers le bas ; les embeddings et le cross-encoder franchissent la barrière de la langue.
- **Choix pour l'application** : le cross-encoder demande plusieurs gigaoctets de mémoire, trop pour l'application hébergée. L'application affiche 5 passages, donc le rappel@5 est la mesure pertinente ; parmi les méthodes légères, les embeddings sont les meilleurs sur ce point (94 %) et fonctionnent en français. Ce choix a été fait après avoir vu les résultats ; il est écrit ici pour cette raison.
- **Les réponses générées** sont codées (uniquement à partir des passages, un [chunk_id] après chaque phrase appuyée) et seront mesurées sur le taux de citation et l'ancrage numérique (chiffres de la réponse retrouvés dans les passages cités, une mesure simple de fidélité [A2]) dès qu'une clé API sera disponible.

**Alternatives écartées.** Mettre tous les documents dans le prompt (plus de 500 000 caractères : la recherche est nécessaire ici, contrairement au petit ensemble de faits de D28) ; une base vectorielle hébergée (765 passages tiennent dans une matrice de 1 Mo).

**Mise à jour (A29) : début des passages et langue de la réponse.** (1) Le chevauchement de 150 caractères était coupé à un nombre fixe de caractères : 81 % des passages commençaient au milieu d'un mot et l'application affichait des débuts de phrase tronqués. Le découpage fait désormais commencer le chevauchement à un début de phrase (sinon de mot) ; pour le corpus actuel, qui ne peut pas être reconstruit hors ligne, l'application et le prompt de réponse retirent le fragment répété en tête (`clean_start`, 160 caractères au plus, donc seul du texte de chevauchement est retiré). La recherche est inchangée : l'indexation utilise toujours les passages enregistrés, donc l'évaluation ci-dessus reste valable (BM25 relancé : mêmes chiffres). (2) 91 % des passages sont en anglais (seuls le journal et le résumé du projet sont en français). La langue de la réponse est maintenant détectée à partir de la question (16 questions d'évaluation sur 16 bien détectées) au lieu d'être prise dans la langue de l'application, et le prompt nomme explicitement la langue cible, car une consigne générique « répondre dans la langue de la question » est en concurrence avec un contexte surtout anglais [A1, N3]. L'application indique que les sources sont surtout en anglais et que les passages cités restent dans leur langue d'origine.

**Mise à jour (A30) : fournisseur des réponses.** L'application en ligne n'avait pas de clé API : elle n'écrivait aucune réponse et n'affichait que des passages en anglais. Les réponses peuvent maintenant être rédigées par Gemini (offre gratuite de Google AI Studio) ou par Claude, au choix du secret `RAG_PROVIDER` ou selon la clé présente (Gemini d'abord). Raisons : une démonstration publique à coût nul qui répond vraiment ; Claude reste un second fournisseur, pour que le choix repose sur une comparaison mesurée et non sur une préférence. L'offre gratuite permet à Google d'utiliser les questions soumises pour améliorer ses produits et ses quotas sont bas [A3] : les questions sont publiques et portent sur des documents publics, l'application le signale sous chaque réponse de Gemini, et toute erreur renvoie aux passages. L'évaluation des réponses utilise désormais la recherche de l'application (embeddings), ajoute la part des réponses rédigées dans la langue de la question et compare les fournisseurs sur les mêmes questions avec le test apparié.

**Mise à jour (A31) : réponses mesurées avec Gemini.** Exécution de `src/rag/eval_rag.py` le 15 octobre 2026 sur les 16 questions, avec Gemini seul (pas de clé Claude). Le modèle par défaut `gemini-flash-latest` (alors Gemini 3.8 Flash) a répondu à 7 questions sur 16 : l'offre gratuite autorise 20 requêtes par jour et par modèle et environ 5 par minute, et les autres appels ont échoué sur des erreurs de quota (429) ou de surcharge (503). Une seconde exécution avec `gemini-flash-lite-latest` (quota distinct, choisi par le secret `GEMINI_MODEL`) a répondu aux 16 : 10 réponses sur 16 citent un passage (62 %), 16 sur 16 sont rédigées dans la langue de la question (100 % : 10 en anglais, 6 en français), et 12 des 16 nombres écrits hors citations figurent dans les passages cités (75 %). Les 6 réponses sans citation sont toutes des abstentions (« les passages ne répondent pas ») et, pour 5 d'entre elles, un passage pertinent figurait parmi les 5 premiers retrouvés (rangs 1 à 4) : le modèle est trop prudent plutôt que trompé par la recherche. Trois corrections de mesure et de robustesse accompagnent l'exécution : les citations groupées comme [R4-003, R4-002] sont désormais comptées, les générations en échec sont comptées à part au lieu de passer pour des réponses dans la bonne langue, et les appels à Gemini sont relancés brièvement sur 429 et 503 et espacés dans l'évaluation. Conséquences : 16 questions restent trop peu pour un test de significativité (étape 2 : agrandir le jeu) ; 20 requêtes par jour rendent Flash inutilisable pour une application publique comme pour une évaluation plus large, d'où Flash-Lite ou une offre payante ; les fausses abstentions doivent devenir un indicateur suivi.

**Mise à jour (A32) : Flash-Lite par défaut, réponses moins prudentes.** Deux corrections suivent A31. (1) Le modèle par défaut de l'application devient `gemini-flash-lite-latest` : Flash autorise 20 requêtes gratuites par jour, ce qu'une application publique et une évaluation plus large dépassent aussitôt, alors que Flash-Lite a répondu aux 16 questions le même jour ; une offre payante coûterait de l'argent pour une démonstration de portfolio, et le secret `GEMINI_MODEL` permet toujours de changer de modèle. (2) La consigne demande désormais au modèle de répondre avec ce que disent les passages même s'ils ne couvrent qu'une partie de la question, de dire ce qui manque, et de s'abstenir seulement quand aucun passage n'est pertinent : dans A31, 5 des 6 abstentions avaient un passage pertinent sous la main. L'évaluation compte maintenant les abstentions et les fausses abstentions (abstention alors qu'un passage pertinent était fourni), repérées par un motif de phrases en anglais et en français qui retrouvait exactement les 6 abstentions d'A31. Résultats sur les 16 questions, le même jour, avec Flash-Lite : réponses citant un passage 10/16 à 16/16, abstentions 6 à 0 (fausses abstentions 5 à 0), ancrage numérique 12/16 à 19/20 nombres, langue 16/16 dans les deux exécutions. Une lecture manuelle des nouvelles réponses est moins flatteuse que le taux de citation : 10 répondent correctement, 3 en partie (Q04 date d'abrogation, Q10 la règle mais pas sa raison, Q11 chocs de prix mondiaux sans l'arabica) et 3 ne répondent pas tout en citant un passage annexe (Q01, Q13 ; Q15 où aucun passage pertinent n'a été retrouvé). Le taux de citation ne mesure donc plus si la question reçoit une réponse ; l'étape 2 ajoute un corrigé vérifié à la main. Deux limites connues : les réponses ajoutent parfois une phrase inutile sur ce que les passages ne couvrent pas (Q05, Q06, Q11), et la consigne a été revue après lecture des réponses à ces mêmes 16 questions, si bien que le gain doit être confirmé sur de nouvelles questions (étape 2) avant d'être tenu pour général.

**Mise à jour (A33) : questions réservées avec un corrigé.** Les 16 questions ont servi à revoir la consigne dans A32 ; 34 questions nouvelles (18 en anglais, 16 en français ; `data/reference/rag_eval_holdout.csv`) ont donc été rédigées à partir des sources avec un corrigé : les formes acceptées de la réponse attendue (un nombre, une date ou une expression), vérifiées à la main dans les passages (pour les questions en français sur des sources anglaises, le corrigé contient la traduction française). Une réponse atteint le corrigé quand elle contient l'une de ces formes (`has_answer()`, pourcentages écrits en toutes lettres acceptés). Résultats avec Flash-Lite et la recherche alors utilisée par l'application (embeddings) : corrigé atteint 19/34 (56 %) ; 19 questions ont reçu un passage pertinent et 18 d'entre elles ont reçu une réponse correcte ; 15 n'en ont pas reçu et une seule de celles-ci a été correcte. Le goulot d'étranglement était la recherche, pas la rédaction. Sur le jeu réservé, les embeddings classent le moins bien (MRR 0,44 [0,30 ; 0,59], recall@5 56 %) et BM25 mieux (MRR 0,63, recall@5 82 %) ; sur les 50 questions des deux jeux, BM25 devance les embeddings (MRR 0,63 contre 0,51, recall@5 0,78 contre 0,68, test apparié p = 0,10). Le cross-encoder est le meilleur (MRR 0,87 sur le jeu réservé, p < 0,001 contre RRF) mais demande 2,4 Go de mémoire et environ 11 secondes par question sur 4 processeurs, trop lourd pour l'application hébergée. La recherche de l'application devient donc BM25, qui ne demande en plus aucun téléchargement de modèle. Nouvelle exécution avec BM25 : corrigé atteint 27/34 (79 % [65 % ; 91 %]), anglais 18/18, français 9/16 ; 28 questions ont reçu un passage pertinent et 27 d'entre elles une réponse correcte ; ancrage numérique 59/63 (94 %). L'écart restant vient des questions en français sur des sources anglaises, que les mots-clés ne relient pas : traduire la question avant la recherche (étape 4 de la feuille de route) est la prochaine correction. Le choix de BM25 a utilisé le jeu réservé, qui n'est donc plus vierge pour la recherche ; un troisième jeu sera nécessaire avant la prochaine comparaison.

## D32 — Mettre la recherche documentaire (RAG) en pause dans l'application ; priorité au côté opérationnel et métier [décidé]
**Décision.** La recherche documentaire avec réponses rédigées (RAG, D30) est retirée de l'application hébergée (d'abord remplacée par une mention « en développement » dans A34, puis retirée entièrement dans A35) ; le code, les tests et l'évaluation restent dans le dépôt, et la section revient avec le secret `RAG` réglé sur `on`. Les réponses vérifiées (questions et réponses fixes avec leur source, sans IA, D24) restent telles quelles. Le travail sur le RAG continue hors ligne (jeux d'évaluation, recherche, traduction des questions en français) et sera présenté comme un travail en cours tant qu'il n'atteint pas un seuil de qualité fixé à l'avance. La priorité suivante du projet est son usage opérationnel et le besoin métier auquel il répond : mesurer ce que les tarifs coûtent aux ménages et quelles catégories de l'épicerie ils touchent.

**Raisons.** Le porteur du projet a jugé les réponses pas assez convaincantes pour une démonstration publique, et les mesures vont dans le même sens : avant A33, le corrigé était atteint pour 56 % des questions nouvelles, et même après le passage à BM25 les questions en français n'atteignent que 56 % (anglais 100 %). Une fonction juste environ une fois sur deux pour la moitié des utilisateurs nuit à la crédibilité du reste du projet, dont les résultats sont vérifiés (D24). Garder le code, les tests et l'évaluation (D30, A31 à A33) préserve le travail et montre la méthode ; un seuil mesuré évite de la réactiver à l'impression.

**Condition de remise en ligne.** Corrigé atteint pour au moins 80 % des questions réservées dans chaque langue, sur un jeu qui n'a pas servi à régler le système, avec une recherche assez légère pour l'application hébergée.

**Alternatives écartées.** Garder le RAG en ligne avec un avertissement (les utilisateurs liraient quand même des réponses peu fiables) ; garder la recherche de passages sans réponse rédigée (une fonction partielle resterait affichée, et les questions en français trouveraient encore des passages faibles) ; supprimer la fonction (le travail d'évaluation fait partie du portfolio et les prochaines corrections sont connues).

## D33 — Côté opérationnel : figer la prévision d'avant les tarifs de 2026, pas d'alerte automatique, coût par catégorie [décidé]
**Décision.**
- **Contrefactuel figé.** La prévision faite avec les données jusqu'à août 2026, le mois précédant les tarifs de 2026 (8 septembre 2026, D18), est enregistrée dans `data/reference/forecast_vintage_2026-08.csv`. La mise à jour mensuelle (D25) remplace `forecasts.csv` et effacerait sinon la trajectoire que les prix auraient suivie sans les tarifs ; les scénarios du fromage (D06) partent désormais de cette prévision figée.
- **Pas d'alerte automatique dans l'application.** Une règle de surveillance a été construite (`src/monitor/tariff_watch.py`) : chaque mois, une série au-dessus de son intervalle conforme à 80 % [F4] est signalée, et les séries taxées sont comparées aux séries non taxées (test exact de Fisher, unilatéral [M6]). Rejouée sur les deux épisodes passés avec le modèle publié, elle ne détecte rien : 2018, 4 % des séries taxées signalées contre 7 % des non taxées ; 2025, 14 % contre 15 % ; aucun mois avec p < 0,05. Le seul signal fort de 2025, le café (18 % au-dessus de sa prévision), vient des cours mondiaux (D22). La règle reste donc un outil d'analyse et n'est pas affichée comme une alerte.
- **Coût par catégorie dans l'application.** La section « Ce que ça me coûte » montre, pour la facture de l'utilisateur, d'où vient le coût de 2025 : la même méthode en une ligne appliquée à chaque catégorie du panier (D27), triée, avec les catégories en borne haute hachurées.

**Raisons.** Le besoin métier est de dire à un ménage, à un détaillant ou à un analyste ce que les tarifs coûtent et où. Le test rétrospectif confirme le résultat principal du projet (D20, D21) : l'effet d'un tarif sur une série de l'IPC (environ 3 points au plus) reste sous ce que les données mensuelles publiques permettent de détecter (environ 5 points), et l'effet de 2026 sur le fromage est d'au plus 0,6 point (D06). Une alerte qui ne sonne presque jamais, et sonne pour une mauvaise raison quand les cours mondiaux bougent, induirait en erreur. La vue par catégorie répond à la question pratique avec des chiffres déjà vérifiés : quatre catégories portent 64 % du coût central, dont trois en borne haute (boulangerie, condiments, boissons : leurs codes douaniers sont plus larges que les produits taxés).

**Alternatives écartées.** Afficher l'alerte avec ses limites écrites à côté (elle afficherait surtout « rien de visible » ou un faux signal) ; des alertes par série sans comparaison aux séries non taxées (le café passerait pour un effet du tarif) ; recalculer le contrefactuel chaque mois (il absorberait le tarif).

**Mise à jour (A38) : coût de 2026 par catégorie.** La même vue couvre désormais les tarifs de 2026, à partir des importations américaines de 2025 des 15 lignes taxées (UN Comtrade, D21) rapportées aux dépenses alimentaires des ménages de 2024, le dénominateur du total publié (D26) ; les groupes s'additionnent exactement à ce total. Pour une facture de 1 000 $ par mois, scénario central : mélanges et pâtes de boulangerie 0,64 $, poudres de lait et lactosérum 0,25 $, fromage 0,17 $, miel et mélasse 0,04 $, soit 1,10 $ contre 5,20 $ pour 2025. Le fromage est le seul produit taxé tel qu'il est vendu en magasin (16 % du coût) ; les trois autres groupes sont des ingrédients (D18) et sont affichés comme bornes hautes, car une partie de leurs importations va aux restaurants et aux fabricants. La part solide du coût de 2026 pour un ménage est donc d'environ 0,17 $ par mois pour 1 000 $ d'épicerie, cohérente avec l'effet sur le fromage d'au plus 0,6 point (D06).

## D34 — Les étapes qui demandent une clé API payante sont présentées comme perspectives [décidé]
**Décision.** Les deux étapes qui demandent une clé API Anthropic ne sont pas lancées dans cette version et sont présentées comme perspectives dans le README, le résumé d'une page et les notes du projet : la fiabilité de l'assistant IA optionnel (D28, 20 questions bilingues, `python src/eval_assistant.py`) et l'étape LLM du classifieur des lignes tarifaires (D29, Claude choisit une des 5 séries candidates). Le code, les jeux de questions et la notation sont prêts : chaque étape tient en une commande dès qu'une clé existe. Sans clé, l'application en ligne n'affiche pas l'assistant (D28), si bien qu'aucune réponse d'IA non mesurée n'atteint les utilisateurs ; les réponses vérifiées restent le seul mode de l'onglet des questions.

**Raisons.** Une clé payante est un coût récurrent pour un projet étudiant, et les parties qui répondent à la question du projet (suivi des prix, estimation causale, prévisions, coût pour les ménages) n'en dépendent pas. La règle de D24 et D32 s'applique : l'application ne montre que ce qui est vérifié, et une fonction d'IA n'est montrée qu'une fois sa fiabilité publiée. Dire ouvertement ce qui reste à faire est plus crédible qu'une affirmation sans chiffre ; le README disait que la fiabilité de l'assistant était « mesurée », ce qui n'était pas encore vrai, et il est corrigé.

**Alternatives écartées.** Noter l'assistant avec la clé Gemini gratuite déjà utilisée pour le RAG (D30) : le prompt et le préfixe de faits mis en cache sont conçus pour Claude, donc le score décrirait un autre assistant que celui qui serait déployé ; afficher l'assistant sans son évaluation (contraire à D28).
