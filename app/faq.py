"""Verified bilingual answers for the app's question tab (D24).

Each answer restates a result of the decision log; the matching is by shared keywords (4+ letters), so
the behaviour is fully predictable and easy to explain. Keep answers in sync with docs/ when results change.
"""

FAQ = [
    {
        "q": {"en": "How much did the counter-tariffs cost my household?",
              "fr": "Combien les contre-tarifs ont-ils coûté à mon ménage ?"},
        "a": {"en": "For an average household, about 0.5% of the grocery bill while the 2025 tariffs applied (March to August 2025): "
                    "roughly 5 dollars a month for 1,000 dollars of groceries, within a plausible range of 0 to 16 dollars. Over the same months, "
                    "grocery prices rose 1.8% for all reasons combined. Use the 'What it costs me' tab with your own spending.",
              "fr": "Pour un ménage moyen, environ 0,5 % de la facture d'épicerie pendant l'application des tarifs de 2025 (mars à août 2025) : "
                    "environ 5 dollars par mois pour 1 000 dollars d'épicerie, dans une fourchette plausible de 0 à 16 dollars. Sur les mêmes mois, "
                    "les prix en magasin ont augmenté de 1,8 % toutes causes confondues. Utilisez l'onglet « Ce que ça me coûte » avec vos propres dépenses."},
        "source": "D21, D22, D26",
        "keywords": ["cost", "costs", "household", "family", "bill", "much", "coûté", "coûte", "coût", "ménage", "famille", "facture",
                     "combien", "budget", "spending", "dépenses", "money", "argent"],
    },
    {
        "q": {"en": "Did the 2025 counter-tariffs raise grocery prices?",
              "fr": "Les contre-tarifs de 2025 ont-ils fait monter les prix de l'épicerie ?"},
        "a": {"en": "A little, and only on the tariffed products. Once coffee (driven by world prices) is set aside, about 40% of the "
                    "tariff was passed on, with a wide 95% interval (−7% to 86%) that contains the Bank of Canada's estimate of about 25%. "
                    "Because US goods are a small share of each CPI series (median 9%), the effect on the series themselves is small.",
              "fr": "Un peu, et seulement sur les produits taxés. Une fois le café mis à part (porté par les cours mondiaux), environ 40 % du "
                    "tarif a été répercuté, avec un intervalle à 95 % large (de −7 % à 86 %) qui contient l'estimation de la Banque du Canada, "
                    "environ 25 %. Comme les produits américains pèsent peu dans chaque série de l'IPC (médiane 9 %), l'effet sur les séries est faible."},
        "source": "D21, D22; Bank of Canada R1/R2",
        "keywords": ["2025", "tariffs", "tariff", "counter", "prices", "raise", "rise", "grocery", "tarifs", "tarif", "contre",
                     "prix", "monter", "hausse", "épicerie", "transmission", "pass", "through"],
    },
    {
        "q": {"en": "Why did coffee become so expensive?", "fr": "Pourquoi le café est-il devenu si cher ?"},
        "a": {"en": "Mostly world prices. Arabica coffee roughly doubled in Canadian dollars between mid-2024 and early 2025. Retail coffee "
                    "followed with a lag and stayed high after the tariff was lifted in September 2025, which a tariff effect would not do.",
              "fr": "Surtout à cause des cours mondiaux. L'arabica a environ doublé en dollars canadiens entre la mi-2024 et le début de 2025. "
                    "Le café au détail a suivi avec retard et est resté cher après la levée du tarif en septembre 2025, ce qu'un effet du tarif ne ferait pas."},
        "source": "D22; World Bank Pink Sheet (S15)",
        "keywords": ["coffee", "café", "expensive", "cher", "arabica", "world", "mondial", "mondiaux", "cours"],
    },
    {
        "q": {"en": "Will milk and butter cost more because of the 2026 tariffs?",
              "fr": "Le lait et le beurre vont-ils coûter plus cher à cause des tarifs de 2026 ?"},
        "a": {"en": "Not directly. The September 2026 list taxes cheese at 25%, and milk powders and whey at 50%. Fresh milk, butter, yogurt "
                    "and ice cream are not on the list. Milk powders and whey are ingredients, so any effect on other dairy products would be indirect.",
              "fr": "Pas directement. La liste de septembre 2026 taxe le fromage à 25 %, et les poudres de lait et le lactosérum à 50 %. Le lait frais, "
                    "le beurre, le yogourt et la crème glacée ne sont pas sur la liste. Les poudres de lait et le lactosérum sont des ingrédients : "
                    "l'effet sur les autres produits laitiers serait donc indirect."},
        "source": "D18; Finance Canada list (R7)",
        "keywords": ["milk", "butter", "dairy", "2026", "lait", "beurre", "laitiers", "yogurt", "yogourt", "cream", "crème"],
    },
    {
        "q": {"en": "What about cheese in 2026?", "fr": "Et le fromage en 2026 ?"},
        "a": {"en": "Cheese is taxed at 25% since September 8, 2026. The app shows a no-tariff forecast and three scenarios (25% temporary, 60%, "
                    "70% persistent pass-through). The first month of real data (September 2026) is published on October 19, 2026.",
              "fr": "Le fromage est taxé à 25 % depuis le 8 septembre 2026. L'application montre une prévision sans tarif et trois scénarios "
                    "(transmission de 25 % temporaire, 60 %, 70 % durable). Le premier mois de données réelles (septembre 2026) paraît le 19 octobre 2026."},
        "source": "D06, D17, D23; StatCan release calendar (S7)",
        "keywords": ["cheese", "fromage", "2026", "scenario", "scenarios", "scénario", "scénarios"],
    },
    {
        "q": {"en": "Why compare with a synthetic control?", "fr": "Pourquoi comparer avec un contrôle synthétique ?"},
        "a": {"en": "To know what a tariffed product's price would have done without the tariff, we build a 'twin' from a weighted mix of "
                    "similar untaxed products that moved like it before the tariff. The gap after the tariff is the estimated effect. "
                    "The Bank of Canada used the same idea for 2018.",
              "fr": "Pour savoir ce qu'aurait fait le prix d'un produit taxé sans le tarif, on construit un « jumeau » : un mélange pondéré de "
                    "produits semblables non taxés qui évoluaient comme lui avant le tarif. L'écart après le tarif est l'effet estimé. "
                    "La Banque du Canada a utilisé la même idée pour 2018."},
        "source": "D05, D19; Abadie (M1, M2); Bank of Canada (R3)",
        "keywords": ["synthetic", "control", "method", "méthode", "contrôle", "synthétique", "twin", "jumeau", "comparer", "compare"],
    },
    {
        "q": {"en": "Why did you find no effect for 2018?", "fr": "Pourquoi aucun effet pour 2018 ?"},
        "a": {"en": "The 2018 surtax was 10%, and US goods were a small part of each series: even full pass-through would have moved them by "
                    "about 1.4 points on average, below what monthly public data can detect (about 3.6 points). This does not contradict the "
                    "Bank of Canada, which used non-public micro data.",
              "fr": "La surtaxe de 2018 était de 10 %, et les produits américains pesaient peu dans chaque série : même une transmission complète "
                    "ne les aurait fait bouger que d'environ 1,4 point en moyenne, sous ce que les données mensuelles publiques permettent de détecter "
                    "(environ 3,6 points). Cela ne contredit pas la Banque du Canada, qui a utilisé des microdonnées non publiques."},
        "source": "D20, D21; Bank of Canada (R3)",
        "keywords": ["2018", "effect", "effet", "surtax", "surtaxe", "detect", "détecter", "aucun"],
    },
    {
        "q": {"en": "How accurate are the forecasts?", "fr": "Les prévisions sont-elles fiables ?"},
        "a": {"en": "They were tested on 2019–2025 as if made in the past (rolling-origin backtest) and compared with a simple 'same pattern as "
                    "last year' baseline. Each forecast comes with 80% and 95% intervals whose coverage was checked on 2023–2025.",
              "fr": "Elles ont été testées sur 2019–2025 comme si elles avaient été faites dans le passé (backtest à origine glissante), et comparées "
                    "à une méthode de base simple (« même profil que l'an dernier »). Chaque prévision a des intervalles à 80 % et 95 % dont la couverture "
                    "a été vérifiée sur 2023–2025."},
        "source": "D08, D09, D23; Hyndman & Athanasopoulos (F1)",
        "keywords": ["forecast", "forecasts", "accurate", "accuracy", "prévision", "prévisions", "fiable", "fiables", "backtest", "interval", "intervalle"],
    },
    {
        "q": {"en": "Where do the data come from?", "fr": "D'où viennent les données ?"},
        "a": {"en": "All public: Statistics Canada (CPI 18-10-0004-01, average prices 18-10-0245-01, basket weights 18-10-0007-01, household "
                    "spending 36-10-0225-01), Bank of Canada (USD/CAD), UN Comtrade (imports by product) and the World Bank (world prices). "
                    "Tariff lists come from Finance Canada and the Canada Gazette.",
              "fr": "Toutes publiques : Statistique Canada (IPC 18-10-0004-01, prix moyens 18-10-0245-01, poids du panier 18-10-0007-01, dépenses "
                    "des ménages 36-10-0225-01), Banque du Canada (USD/CAD), UN Comtrade (importations par produit) et Banque mondiale (cours mondiaux). "
                    "Les listes tarifaires viennent de Finances Canada et de la Gazette du Canada."},
        "source": "docs/references.md",
        "keywords": ["data", "données", "source", "sources", "statistics", "statistique", "public", "publiques", "where", "viennent"],
    },
    {
        "q": {"en": "Why not use average prices like '4 L of milk'?", "fr": "Pourquoi ne pas utiliser les prix moyens comme « 4 L de lait » ?"},
        "a": {"en": "Statistics Canada says average prices do not measure pure price change (products and stores change), and the sample "
                    "changed in January 2024. They are shown for information only; the analysis uses the CPI.",
              "fr": "Statistique Canada indique que les prix moyens ne mesurent pas une variation pure des prix (produits et magasins changent), et "
                    "l'échantillon a changé en janvier 2024. Ils sont affichés à titre indicatif ; l'analyse utilise l'IPC."},
        "source": "D03, D04; Statistics Canada (S3)",
        "keywords": ["average", "moyen", "moyens", "litre", "litres", "prices", "prix", "2024", "break", "rupture"],
    },
]
