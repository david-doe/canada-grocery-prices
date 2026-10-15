"""Canadian grocery prices and counter-tariffs: bilingual public dashboard (EN/FR).

Run locally:  streamlit run app/streamlit_app.py
Data: app/data/ (built by src/build_app_data.py from public Statistics Canada, Bank of Canada,
UN Comtrade and World Bank data). Every number comes from a notebook in notebooks/ and a decision
in docs/ (D-numbers). Design: sober and minimal, light or dark theme (D24, D26).
"""
from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import assistant
import rag
from faq import FAQ

DATA = Path(__file__).parent / "data"
REPO = "https://github.com/david-doe/canada-grocery-prices"
APP_URL = "https://canada-grocery-prices.streamlit.app/"
# Next CPI releases (Statistics Canada release calendar, S7): reference month -> release date
CPI_RELEASES = {"2026-09": "2026-10-19", "2026-10": "2026-11-16", "2026-11": "2026-12-14", "2026-12": "2027-01-18"}
PROV_FR = {"Canada": "Canada", "Newfoundland and Labrador": "Terre-Neuve-et-Labrador", "Prince Edward Island": "Île-du-Prince-Édouard",
           "Nova Scotia": "Nouvelle-Écosse", "New Brunswick": "Nouveau-Brunswick", "Quebec": "Québec", "Ontario": "Ontario",
           "Manitoba": "Manitoba", "Saskatchewan": "Saskatchewan", "Alberta": "Alberta", "British Columbia": "Colombie-Britannique",
           "Whitehorse, Yukon": "Whitehorse (Yukon)", "Yellowknife, Northwest Territories": "Yellowknife (T.N.-O.)"}

st.set_page_config(page_title="Grocery prices & tariffs | Prix d'épicerie et tarifs", layout="wide")

# ------------------------------------------------------------------ language, theme, author
QP = st.query_params
lang = st.sidebar.radio("Language / Langue", ["English", "Français"], horizontal=True,
                        index=1 if QP.get("lang", "en") == "fr" else 0)
FR = lang == "Français"


def t(en: str, fr: str) -> str:
    return fr if FR else en


theme = st.sidebar.radio(t("Theme", "Thème"), [t("Light", "Clair"), t("Dark", "Sombre")], horizontal=True,
                         index=1 if QP.get("theme", "light") == "dark" else 0)
DARK = theme in ("Dark", "Sombre")

C = ({"bg": "#1a1a19", "panel": "#232322", "border": "#3a3a37", "ink": "#ffffff", "muted": "#c3c2b7", "grid": "#33332f",
      "blue": "#3987e5", "orange": "#d95926", "aqua": "#199e70", "yellow": "#c98500", "band": "57,135,229"}
     if DARK else
     {"bg": "#fcfcfb", "panel": "#f3f2ef", "border": "#e2e1dc", "ink": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e0",
      "blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "yellow": "#eda100", "band": "42,120,214"})

st.markdown(f"""<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: {C['bg']}; color: {C['ink']}; }}
[data-testid="stSidebar"] {{ background: {C['panel']}; border-right: 1px solid {C['border']}; }}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
[data-testid="stMarkdownContainer"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {C['ink']}; }}
[data-testid="stCaptionContainer"], .muted {{ color: {C['muted']} !important; }}
button[role="tab"] p {{ color: {C['muted']}; }}
button[role="tab"][aria-selected="true"] p {{ color: {C['ink']}; }}
[data-baseweb="select"] > div, [data-baseweb="select"] div, [data-baseweb="select"] input, [data-baseweb="input"], [data-baseweb="input"] input, [data-baseweb="base-input"],
[data-testid="stNumberInputContainer"] input, [data-testid="stExpander"] details {{
  background: {C['panel']} !important; color: {C['ink']} !important; border-color: {C['border']} !important; }}
[data-testid="stSelectbox"] div, [data-testid="stSelectbox"] input, [data-testid="stTextInput"] div[data-baseweb],
[role="listbox"], [role="listbox"] *, [role="option"] {{ background-color: {C['panel']} !important; color: {C['ink']} !important; }}
[role="option"]:hover, [role="option"][aria-selected="true"] {{ background-color: {C['border']} !important; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {{ background: {C['panel']} !important; color: {C['ink']} !important; }}
[data-testid="stNumberInputContainer"] button {{ background: {C['panel']} !important; color: {C['ink']} !important; }}
.stDownloadButton button {{ background: {C['panel']}; color: {C['ink']}; border: 1px solid {C['border']}; }}
.kpi {{ border-top: 2px solid {C['border']}; padding-top: .4rem; }}
.kpi .v {{ font-size: 1.9rem; font-weight: 600; color: {C['ink']}; line-height: 1.2; }}
.kpi .l {{ font-size: .85rem; color: {C['muted']}; }}
.banner {{ border: 1px solid {C['border']}; padding: .6rem .9rem; font-size: .95rem; color: {C['ink']}; }}
[data-testid="stMain"] div[role="radiogroup"] {{ gap: .2rem 1.2rem; }}
[data-testid="stMain"] div[role="radiogroup"] label > div > div:first-child:not([data-testid]) {{ display: none; }}
[data-testid="stMain"] div[role="radiogroup"] label {{ padding: .25rem 0; border-bottom: 2px solid transparent; cursor: pointer; }}
[data-testid="stMain"] div[role="radiogroup"] label p {{ color: {C['muted']}; font-size: .95rem; }}
[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) {{ border-bottom-color: {C['blue']}; }}
[data-testid="stMain"] div[role="radiogroup"] label:has(input:checked) p {{ color: {C['ink']}; font-weight: 600; }}
table.clean {{ border-collapse: collapse; width: 100%; font-size: .92rem; color: {C['ink']}; }}
table.clean th {{ text-align: left; font-weight: 600; border-bottom: 1px solid {C['border']}; padding: .35rem .5rem; color: {C['muted']}; }}
table.clean td {{ border-bottom: 1px solid {C['grid']}; padding: .35rem .5rem; vertical-align: top; }}
</style>""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown(t("**Author**  \nDavid Doe  \nData science student, University of Lille",
                      "**Auteur**  \nDavid Doe  \nÉtudiant en data science, Université de Lille"))
st.sidebar.markdown(f"[{t('Source code and method', 'Code source et méthode')}]({REPO})")
st.sidebar.caption(t("Data: Statistics Canada, Bank of Canada, UN Comtrade, World Bank (public).",
                     "Données : Statistique Canada, Banque du Canada, UN Comtrade, Banque mondiale (publiques)."))


# ------------------------------------------------------------------ data
@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


cpi, labels = load("cpi_food.csv"), load("series_labels.csv")
fc, scen = load("forecasts.csv"), load("scenarios_cheese.csv")
sc, ptc = load("sc_results.csv"), load("pass_through_commodity.csv")
expo, avg, bts = load("exposure.csv"), load("avg_prices.csv"), load("backtest_summary.csv")
cost, lookup, prov = load("tariff_cost.csv"), load("tariff_lookup.csv"), load("province_food.csv")
basket, basket26 = load("basket_2025.csv"), load("basket_2026.csv")
notes = __import__("json").loads((DATA / "monthly_notes.json").read_text(encoding="utf-8"))


@st.cache_data
def facts() -> str:
    return assistant.build_facts()
name_fr = dict(zip(labels.series, labels.series_fr))


def label(s: str) -> str:
    return name_fr.get(s, s) if FR else s


def pct(x: float, digits: int = 1, sign: bool = True) -> str:
    s = f"{x:+.{digits}f}" if sign else f"{x:.{digits}f}"
    return (s.replace(".", ",") + " %") if FR else (s + "%")


def share(x: float, digits: int = 0) -> str:
    s = f"{100 * x:.{digits}f}"
    return (s.replace(".", ",") + " %") if FR else (s + "%")


def money(x: float) -> str:
    return (f"{x:,.2f}".replace(",", " ").replace(".", ",") + " $") if FR else f"${x:,.2f}"


def money_md(x: float) -> str:
    """Dollar amount for st.markdown, where a pair of $ signs would be read as a math formula."""
    return money(x).replace("$", r"\$")


def style(fig: go.Figure, ytitle: str, height: int = 420) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), yaxis_title=ytitle, hovermode="x unified",
                      legend=dict(orientation="h", y=-0.15), paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
                      font=dict(color=C["ink"]), hoverlabel=dict(bgcolor=C["panel"], font_color=C["ink"]))
    fig.update_xaxes(showgrid=False, linecolor=C["border"], tickfont=dict(color=C["muted"]), automargin=True)
    fig.update_yaxes(gridcolor=C["grid"], showgrid=True, zeroline=False, linecolor=C["border"], tickfont=dict(color=C["muted"]), automargin=True)
    for tr in fig.data:  # plotly adds markers to short traces by default: keep plain lines
        if tr.type == "scatter" and tr.mode is None:
            tr.mode = "lines"
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displaylogo": False})


def table(df: pd.DataFrame) -> None:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in df.itertuples(index=False))
    st.markdown(f'<table class="clean"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>', unsafe_allow_html=True)


def kpi(col, value: str, text: str) -> None:
    col.markdown(f'<div class="kpi"><div class="v">{value}</div><div class="l">{text}</div></div>', unsafe_allow_html=True)


def fold(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")


# ------------------------------------------------------------------ headline numbers
stores = cpi[cpi.series == "Food purchased from stores"].set_index("month").value
last_month = stores.index[-1]
yoy_last = 100 * (stores.iloc[-1] / stores.iloc[-13] - 1)
f_st = fc[fc.series == "Food purchased from stores"]
fc12 = 100 * (f_st.forecast.iloc[-1] / stores.iloc[-1] - 1)
next_ref = (pd.Period(last_month, "M") + 1).strftime("%Y-%m")
next_release = CPI_RELEASES.get(next_ref, "")
pref = ptc[(ptc.event_id == "CA2025") & (ptc["sample"] == "without coffee and confectionery")
           & (ptc.outcome == "commodity-adjusted (lags 0-11)")].iloc[0]
c25 = cost[cost.event_id == "CA2025"].iloc[0]
per100 = 100 * c25.rate * c25.pt_central * c25.share_central

st.title(t("Canadian grocery prices and counter-tariffs", "Prix de l'épicerie au Canada et contre-tarifs"))
st.markdown(f'<p class="muted">{t("What Canada taxed, what it cost at the checkout, and where food prices are heading. Public data, every number sourced.", "Ce que le Canada a taxé, ce que cela a coûté à la caisse, et où vont les prix alimentaires. Données publiques, chaque chiffre sourcé.")}</p>',
            unsafe_allow_html=True)
st.markdown(f'<div class="banner">{t("Latest data:", "Dernières données :")} <b>{last_month}</b> · '
            f'{t("grocery prices", "prix en magasin")} <b>{pct(yoy_last)}</b> {t("over 12 months", "sur 12 mois")} · '
            f'{t("forecast", "prévision")} <b>{pct(fc12)}</b> {t("over the next 12 months", "sur les 12 prochains mois")}'
            + (f' · {t("next release:", "prochaine publication :")} <b>{next_release}</b>' if next_release else "") + "</div>",
            unsafe_allow_html=True)
st.write("")

SECTIONS = {"context": t("Context", "Contexte"), "overview": t("Results", "Résultats"),
            "cost": t("What it costs me", "Ce que ça me coûte"), "taxed": t("Is it taxed?", "Est-ce taxé ?"),
            "prices": t("Prices and forecasts", "Prix et prévisions"), "provinces": t("Provinces", "Provinces"),
            "effects": t("Tariff effects", "Effets des tarifs"), "average": t("Average prices", "Prix moyens"),
            "questions": t("Questions", "Questions"), "method": t("Method and data", "Méthode et données")}
keys = list(SECTIONS)
start = QP.get("section", "context")
section = st.radio(t("Section", "Section"), keys, index=keys.index(start) if start in keys else 0, horizontal=True,
                   format_func=lambda k: SECTIONS[k], label_visibility="collapsed")
st.markdown(f'<hr style="margin:.2rem 0 1rem 0;border:none;border-top:1px solid {C["border"]}">', unsafe_allow_html=True)


def sync_link(**extra: str) -> str:
    """Keep the address bar in sync, so any view can be shared as a link (D27)."""
    params = {"section": section, "lang": "fr" if FR else "en", "theme": "dark" if DARK else "light", **extra}
    params = {k: v for k, v in params.items() if v not in ("", None)}
    if dict(QP) != params:
        QP.clear()
        QP.update(params)
    return APP_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())


link = sync_link()

# ------------------------------------------------------------------ Context
if section == "context":
    st.markdown(t(
        """### Why this dashboard exists

**The situation.** Since 2018, Canada has answered US tariffs with its own counter-tariffs on US goods, food included.
- **2018**: a 10% surtax on US products such as yogurt, coffee, orange juice, ketchup, soups and whisky, from July 1, 2018 until it was repealed on May 19, 2019 (Canada Gazette, R9, R10).
- **2025**: 25% counter-tariffs on a broad range of US goods from March 4, 2025, including poultry, coffee, tea, orange juice, pasta, sugar, oils and many prepared foods. The food lines were lifted on September 1, 2025 (Finance Canada, R7).
- **2026**: after the United States imposed a 50% tariff on C$27.6 billion of Canadian goods on August 22, 2026, Canada answered dollar for dollar from September 8, 2026: cheese at 25%; milk powders, whey, honey, molasses and bakery mixes at 50% (R7, R8).

Meanwhile, food prices keep rising: *Canada's Food Price Report 2026* expects +4% to +6% in 2026, up to 994 dollars more for a family of four (R5).

**The problem.** Every counter-tariff episode raises the same question at the checkout: *how much of this do I pay?* The public debate mixes tariffs, world commodity prices and general inflation (R6). The best estimates, from the Bank of Canada, find very different answers (about 25% of the tariff passed on in 2025 and temporary; about 70% for food in 2018 and persistent) and rely on data the public cannot see: daily online prices and CPI microdata (R1, R2, R3). Nobody publishes a transparent, regularly updated answer for groceries.

**What this project does.** It uses only public data to answer four questions, with methods that can each be explained in one sentence:
1. **What exactly was taxed?** The official tariff lists, read line by line and placed in the consumer price index.
2. **How much reached the shelf, and what did it cost a household?** Taxed products are compared with similar untaxed ones; the gap is converted into dollars per 100 dollars of groceries.
3. **Was it the tariff or world prices?** World commodity prices (coffee, cocoa, sugar, wheat...) are taken out first.
4. **Where are prices heading?** Forecasts tested on past years, with honest intervals.

Every number is traced to a public source and a written decision; the dashboard is updated after each monthly price release.

**Who it is for.** Households who want to know what tariffs cost them; journalists and citizens who want to check claims; decision makers who design counter-tariffs: the 2026 list, for example, mostly taxes dairy *ingredients*, not milk or butter on the shelf.""",
        """### Pourquoi ce tableau de bord

**La situation.** Depuis 2018, le Canada répond aux tarifs américains par des contre-tarifs sur des produits américains, alimentation comprise.
- **2018** : une surtaxe de 10 % sur des produits américains comme le yogourt, le café, le jus d'orange, le ketchup, les soupes et le whisky, du 1er juillet 2018 à son abrogation le 19 mai 2019 (Gazette du Canada, R9, R10).
- **2025** : des contre-tarifs de 25 % sur un large éventail de produits américains à partir du 4 mars 2025, dont la volaille, le café, le thé, le jus d'orange, les pâtes, le sucre, les huiles et de nombreux aliments préparés. Les lignes alimentaires ont été levées le 1er septembre 2025 (Finances Canada, R7).
- **2026** : après l'imposition par les États-Unis d'un tarif de 50 % sur 27,6 milliards de dollars de produits canadiens le 22 août 2026, le Canada a répondu dollar pour dollar à partir du 8 septembre 2026 : fromage à 25 % ; poudres de lait, lactosérum, miel, mélasse et mélanges pour boulangerie à 50 % (R7, R8).

Pendant ce temps, les prix alimentaires continuent d'augmenter : le *Canada's Food Price Report 2026* prévoit +4 % à +6 % en 2026, soit jusqu'à 994 dollars de plus pour une famille de quatre (R5).

**Le problème.** Chaque épisode de contre-tarifs pose la même question à la caisse : *combien est-ce que je paie ?* Le débat public mélange tarifs, cours mondiaux des matières premières et inflation générale (R6). Les meilleures estimations, celles de la Banque du Canada, donnent des réponses très différentes (environ 25 % du tarif répercuté en 2025, de façon temporaire ; environ 70 % pour l'alimentation en 2018, de façon durable) et reposent sur des données que le public ne voit pas : prix en ligne quotidiens et microdonnées de l'IPC (R1, R2, R3). Personne ne publie de réponse transparente et régulièrement mise à jour pour l'épicerie.

**Ce que fait ce projet.** Il n'utilise que des données publiques pour répondre à quatre questions, avec des méthodes qui s'expliquent chacune en une phrase :
1. **Qu'est-ce qui a été taxé exactement ?** Les listes tarifaires officielles, lues ligne par ligne et placées dans l'indice des prix à la consommation.
2. **Quelle part a atteint les rayons, et combien cela a-t-il coûté à un ménage ?** Les produits taxés sont comparés à des produits semblables non taxés ; l'écart est converti en dollars par 100 dollars d'épicerie.
3. **Le tarif ou les cours mondiaux ?** Les cours mondiaux des matières premières (café, cacao, sucre, blé...) sont retirés d'abord.
4. **Où vont les prix ?** Des prévisions testées sur les années passées, avec des intervalles honnêtes.

Chaque chiffre est relié à une source publique et à une décision écrite ; le tableau de bord est mis à jour après chaque publication mensuelle des prix.

**Pour qui.** Les ménages qui veulent savoir ce que les tarifs leur coûtent ; les journalistes et citoyens qui veulent vérifier des affirmations ; les décideurs qui conçoivent les contre-tarifs : la liste de 2026, par exemple, taxe surtout des *ingrédients* laitiers, pas le lait ni le beurre en rayon."""))
    st.caption(t("Sources R1–R10 are listed in docs/references.md of the repository.", "Les sources R1 à R10 sont listées dans docs/references.md du dépôt."))
    st.markdown(t("**Start here:** [What it costs me](?section=cost) · [Is it taxed?](?section=taxed) · [Results](?section=overview)",
                  "**Commencer ici :** [Ce que ça me coûte](?section=cost&lang=fr) · [Est-ce taxé ?](?section=taxed&lang=fr) · [Résultats](?section=overview&lang=fr)"))

# ------------------------------------------------------------------ 0. Overview
if section == "overview":
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, money(per100), t("per $100 of groceries: estimated cost of the 2025 counter-tariffs while they applied",
                            "par 100 $ d'épicerie : coût estimé des contre-tarifs de 2025 pendant leur application"))
    kpi(c2, f"{share(pref.pass_through)}", t(f"of the 2025 tariff reached shelf prices (95% interval {share(max(pref.lo, 0))} to {share(pref.hi)})",
                                          f"du tarif de 2025 répercuté en magasin (intervalle à 95 % de {share(max(pref.lo, 0))} à {share(pref.hi)})"))
    kpi(c3, f"{share(c25.share_central)}", t("of household food spending was on tariffed US goods in 2025",
                                          "des dépenses alimentaires des ménages portaient sur des produits américains taxés en 2025"))
    kpi(c4, "+0.6 pt" if not FR else "+0,6 pt", t("maximum effect of the 2026 tariff on cheese prices",
                                                  "effet maximal du tarif de 2026 sur le prix du fromage"))
    st.write("")
    st.markdown(t(
        """#### What we found
1. **Counter-tariffs cost households little at the checkout.** In 2025, tariffed US goods were about 5% of food spending. With about 40% of the tariff passed on, the cost was roughly 50 cents per 100 dollars of groceries while the tariffs applied: about 0.5 point of the 1.8% rise in grocery prices between February and August 2025.
2. **The estimate is consistent with the Bank of Canada** (about 25%), with a wide interval: public monthly data cannot be more precise.
3. **Coffee rose because of world prices, not the tariff.** Arabica doubled, and coffee stayed expensive after the tariff was lifted.
4. **The 2026 "dairy" tariffs mostly hit ingredients** (milk powders, whey). Fresh milk and butter are not on the list; cheese is, but US cheese is too small a share of spending to move its price by more than 0.6 point.
5. **2018**: no detectable effect with public data; this neither confirms nor contradicts the Bank of Canada's 70%.""",
        """#### Ce que nous avons trouvé
1. **Les contre-tarifs ont peu coûté aux ménages à la caisse.** En 2025, les produits américains taxés représentaient environ 5 % des dépenses alimentaires. Avec environ 40 % du tarif répercuté, le coût était d'environ 50 cents par 100 dollars d'épicerie pendant l'application des tarifs : environ 0,5 point sur les 1,8 % de hausse des prix en magasin entre février et août 2025.
2. **L'estimation est cohérente avec la Banque du Canada** (environ 25 %), avec un intervalle large : les données mensuelles publiques ne permettent pas plus de précision.
3. **Le café a monté à cause des cours mondiaux, pas du tarif.** L'arabica a doublé, et le café est resté cher après la levée du tarif.
4. **Les tarifs « laitiers » de 2026 visent surtout des ingrédients** (poudres de lait, lactosérum). Le lait frais et le beurre ne sont pas sur la liste ; le fromage l'est, mais le fromage américain pèse trop peu dans les dépenses pour faire bouger son prix de plus de 0,6 point.
5. **2018** : aucun effet détectable avec les données publiques ; cela ne confirme ni ne contredit les 70 % de la Banque du Canada."""))
    st.caption(t("Methods were chosen to be easy to explain; every choice is sourced in the decision log (D01–D28).",
                 "Les méthodes ont été choisies pour être faciles à expliquer ; chaque choix est sourcé dans le journal des décisions (D01–D28)."))
    # automatic monthly note (D27): every sentence is filled from computed numbers
    n = notes
    up = ", ".join(f"{(i['fr'] if FR else i['en']).lower()} ({pct(i['yoy'])})" for i in n["top_up"])
    down = ", ".join(f"{(i['fr'] if FR else i['en']).lower()} ({pct(i['yoy'])})" for i in n["top_down"])
    trend = (t("slowing down", "en ralentissement") if n["stores_yoy"] < n["stores_yoy_prev"] - 0.05 else
             t("speeding up", "en accélération") if n["stores_yoy"] > n["stores_yoy_prev"] + 0.05 else t("stable", "stable"))
    geo = lambda g: PROV_FR.get(g, g) if FR else g
    st.markdown(t(f"#### This month ({n['month']})", f"#### Ce mois-ci ({n['month']})"))
    st.markdown(t(
        f"Grocery prices were **{pct(n['stores_yoy'])}** higher than a year earlier, against {pct(n['stores_yoy_prev'])} the month before: "
        f"{trend}. Restaurant prices: {pct(n['restaurants_yoy'])}. Largest increases over 12 months: {up}. Largest decreases: {down}. "
        f"By province, from {geo(n['province_low']['geo'])} ({pct(n['province_low']['yoy'])}) to {geo(n['province_high']['geo'])} "
        f"({pct(n['province_high']['yoy'])}). Forecast for {n['forecast_month']}: {pct(n['forecast_12m'])}.",
        f"Les prix en magasin étaient **{pct(n['stores_yoy'])}** plus élevés qu'un an plus tôt, contre {pct(n['stores_yoy_prev'])} le mois précédent : "
        f"{trend}. Prix au restaurant : {pct(n['restaurants_yoy'])}. Plus fortes hausses sur 12 mois : {up}. Plus fortes baisses : {down}. "
        f"Par province, de {geo(n['province_low']['geo'])} ({pct(n['province_low']['yoy'])}) à {geo(n['province_high']['geo'])} "
        f"({pct(n['province_high']['yoy'])}). Prévision pour {n['forecast_month']} : {pct(n['forecast_12m'])}."))
    st.caption(t("Written automatically from the latest Statistics Canada release; prices not seasonally adjusted.",
                 "Rédigé automatiquement à partir de la dernière publication de Statistique Canada ; prix non désaisonnalisés."))
    st.markdown(t("#### Share", "#### Partager"))
    s1, s2 = st.columns([2, 1])
    card = DATA / f"share_card_{'fr' if FR else 'en'}.png"
    s1.image(str(card), use_container_width=True)
    s2.markdown(t("Link to this view:", "Lien vers cette vue :"))
    s2.code(link, language=None)
    s2.download_button(t("Download the summary image", "Télécharger l'image de synthèse"), card.read_bytes(),
                       file_name=card.name, mime="image/png", use_container_width=True)

# ------------------------------------------------------------------ 1. What it costs me
if section == "cost":
    st.markdown(t("#### How much did the counter-tariffs add to my grocery bill?", "#### Combien les contre-tarifs ont-ils ajouté à ma facture d'épicerie ?"))
    a, b = st.columns([1, 1])
    bill_qp = QP.get("bill", "1000")
    bill = a.number_input(t("My grocery spending per month ($)", "Mes dépenses d'épicerie par mois ($)"), min_value=0, max_value=10000,
                          value=int(bill_qp) if str(bill_qp).isdigit() else 1000, step=50)
    link = sync_link(bill=str(int(bill)))
    ep = b.radio(t("Tariffs", "Tarifs"), ["CA2025", "CA2026"], horizontal=True,
                 format_func=lambda e: {"CA2025": t("2025 (measured)", "2025 (mesuré)"), "CA2026": t("2026 (scenarios)", "2026 (scénarios)")}[e])
    r = cost[cost.event_id == ep].iloc[0]
    mid = bill * r.rate * r.pt_central * r.share_central
    lo = bill * r.rate * r.pt_low * r.share_low
    hi = bill * r.rate * r.pt_high * r.share_high
    months = int(r.months)
    c1, c2, c3 = st.columns(3)
    kpi(c1, money(mid), t("per month (central estimate)", "par mois (estimation centrale)"))
    kpi(c2, f"{money(lo)} – {money(hi)}", t("per month (plausible range)", "par mois (fourchette plausible)"))
    kpi(c3, money(mid * months), t(f"over {months} months", f"sur {months} mois"))
    st.write("")
    fy = cpi[(cpi.series == "Food purchased from stores")].set_index("month").value
    if ep == "CA2025":
        infl = 100 * (fy.loc["2025-08"] / fy.loc["2025-02"] - 1)
        st.markdown(t(f"For comparison, grocery prices rose **{pct(infl)}** between February and August 2025 for all reasons combined, "
                      f"so by August a {money_md(bill)} monthly bill cost about **{money_md(bill * infl / 100)} more per month**.",
                      f"Pour comparer, les prix en magasin ont augmenté de **{pct(infl)}** entre février et août 2025, toutes causes confondues, "
                      f"si bien qu'en août une facture mensuelle de {money_md(bill)} coûtait environ **{money_md(bill * infl / 100)} de plus par mois**."))
    st.markdown(t(
        f"""**How it is computed** (one line): cost = spending × tariff rate × share passed on × share of food spending on tariffed US goods.
- Tariff rate: {share(r.rate)} ({'import-weighted average of 25% and 50%' if ep == 'CA2026' else 'all food lines'}).
- Share passed on: {share(r.pt_central)} ({'measured, D22' if ep == 'CA2025' else 'central scenario, D06'}); range {share(r.pt_low)} to {share(r.pt_high)}.
- Share of food spending on tariffed US goods: {share(r.share_central, 1)} (range {share(r.share_low, 1)} to {share(r.share_high, 1)}), from UN Comtrade imports and Statistics Canada household spending (D21, D26).""",
        f"""**Comment c'est calculé** (en une ligne) : coût = dépenses × taux du tarif × part répercutée × part des dépenses alimentaires sur des produits américains taxés.
- Taux du tarif : {share(r.rate)} ({'moyenne pondérée par les importations de 25 % et 50 %' if ep == 'CA2026' else 'toutes les lignes alimentaires'}).
- Part répercutée : {share(r.pt_central)} ({'mesurée, D22' if ep == 'CA2025' else 'scénario central, D06'}) ; fourchette de {share(r.pt_low)} à {share(r.pt_high)}.
- Part des dépenses alimentaires sur des produits américains taxés : {share(r.share_central, 1)} (fourchette de {share(r.share_low, 1)} à {share(r.share_high, 1)}), d'après les importations UN Comtrade et les dépenses des ménages de Statistique Canada (D21, D26)."""))
    st.caption(t("An average household estimate: a basket heavy in US products (for example US cheese, orange juice or snacks) costs more.",
                 "Estimation pour un ménage moyen : un panier riche en produits américains (fromage, jus d'orange ou collations américains, par exemple) coûte davantage."))
    def cost_bars(names: list[str], costs: pd.Series, upper: pd.Series, height: int) -> None:
        """Where the cost comes from (D33): monthly cost per category for this bill, upper bounds hatched."""
        st.markdown(t("##### Where the cost comes from", "##### D'où vient le coût"))
        names = [n + (" *" if u else "") for n, u in zip(names, upper)]
        fig = go.Figure(go.Bar(x=costs, y=names, orientation="h", marker=dict(
            color=C["blue"], pattern=dict(shape=["/" if u else "" for u in upper], fgcolor=C["bg"], size=6,
                                         solidity=0.3, fillmode="overlay")),
            text=[money(v) for v in costs], textposition="outside", textfont=dict(color=C["muted"]), cliponaxis=False,
            customdata=100 * costs / costs.sum(),
            hovertemplate="%{y}: %{x:.2f} $ (%{customdata:.0f}%)<extra></extra>"))
        fig.update_layout(bargap=0.35)
        show(style(fig, "", height=height).update_xaxes(title=t("Cost per month for this bill, central estimate ($)",
                                                                "Coût par mois pour cette facture, estimation centrale ($)"),
                                                        showgrid=True, gridcolor=C["grid"]))

    if ep == "CA2026":
        bk = basket26.assign(cost=bill * basket26.share * basket26.rate * r.pt_central).sort_values("cost")
        cost_bars(list(bk.group_fr if FR else bk.group), bk.cost, bk.upper_bound, 260)
        direct = bk[~bk.upper_bound].cost.sum()
        r25 = cost[cost.event_id == "CA2025"].iloc[0]
        mid25 = bill * r25.rate * r25.pt_central * r25.share_central
        st.caption(t(f"Cheese is the only product taxed as sold in stores: {money_md(direct)} per month ({share(direct / bk.cost.sum())} of the cost). "
                     "* Hatched bars are upper bounds: these are ingredients, and part of the imports goes to restaurants and food "
                     f"manufacturers rather than to grocery shelves (D18). For comparison, the 2025 tariffs cost {money_md(mid25)} per month for this bill.",
                     f"Le fromage est le seul produit taxé tel qu'il est vendu en magasin : {money_md(direct)} par mois ({share(direct / bk.cost.sum())} du coût). "
                     "* Les barres hachurées sont des bornes hautes : ce sont des ingrédients, et une partie des importations va aux restaurants et aux "
                     f"fabricants plutôt qu'aux rayons d'épicerie (D18). Pour comparer, les tarifs de 2025 coûtaient {money_md(mid25)} par mois pour cette facture."))
    if ep == "CA2025":
        bk = basket.assign(cost=bill * basket.spend_share * r.rate * r.pt_central * basket.exposure).sort_values("cost")
        cost_bars([(rb.series_fr if FR else rb.series).replace(" (2013=100)", "") for rb in bk.itertuples()], bk.cost, bk.upper_bound, 420)
        top4 = bk.cost.nlargest(4).sum() / bk.cost.sum()
        st.caption(t(f"The four largest categories carry {share(top4)} of the cost. * Hatched bars are upper bounds: their customs codes "
                     "are broader than the taxed products (D21), so the true share of bakery, condiments and beverages is lower.",
                     f"Les quatre premières catégories portent {share(top4)} du coût. * Les barres hachurées sont des bornes hautes : leurs codes douaniers "
                     "sont plus larges que les produits taxés (D21), si bien que la part réelle de la boulangerie, des condiments et des boissons est plus faible."))
        with st.expander(t("My basket: adjust by category (2025)", "Mon panier : ajuster par catégorie (2025)")):
            st.markdown(t("Each line starts at the average household's monthly spending for your total bill. Change the lines you know; "
                          "the cost uses each category's own share of US goods.",
                          "Chaque ligne part de la dépense mensuelle du ménage moyen pour votre facture totale. Modifiez les lignes que vous connaissez ; "
                          "le coût utilise la part de produits américains propre à chaque catégorie."))
            total_mid = total_lo = total_hi = 0.0
            cols = st.columns(2)
            for i, rb in enumerate(basket.itertuples()):
                name = (rb.series_fr if FR else rb.series).replace(" (2013=100)", "")
                v = cols[i % 2].number_input(f"{name} ($)", min_value=0.0, max_value=5000.0, value=round(bill * rb.spend_share, 0),
                                             step=5.0, key=f"basket_{i}")
                total_mid += v * r.rate * r.pt_central * rb.exposure
                total_lo += v * r.rate * r.pt_low * rb.exposure
                total_hi += v * r.rate * r.pt_high * rb.exposure
            c1, c2 = st.columns(2)
            kpi(c1, money(total_mid), t("per month for this basket (central)", "par mois pour ce panier (central)"))
            kpi(c2, f"{money(total_lo)} – {money(total_hi)}", t("per month (range of the share passed on)", "par mois (fourchette de la part répercutée)"))
            st.caption(t("Share of US goods per category: UN Comtrade imports over household spending (D21). For bakery, condiments and beverages "
                         "it is an upper bound (the customs codes are broader than the taxed products). Untaxed food adds nothing.",
                         "Part des produits américains par catégorie : importations UN Comtrade sur dépenses des ménages (D21). Pour la boulangerie, les condiments "
                         "et les boissons, c'est une borne haute (les codes douaniers sont plus larges que les produits taxés). L'alimentation non taxée n'ajoute rien."))

# ------------------------------------------------------------------ 2. Is it taxed?
if section == "taxed":
    st.markdown(t("#### Was a product taxed by Canada's counter-tariffs?", "#### Un produit a-t-il été taxé par les contre-tarifs canadiens ?"))
    q = st.text_input(t("Type a product (for example: orange juice, coffee, cheese, pasta)",
                        "Tapez un produit (par exemple : jus d'orange, café, fromage, pâtes)"), value=QP.get("q", ""))
    link = sync_link(q=q.strip())
    exp_lab = {"direct": t("taxed directly", "taxé directement"), "partial": t("partly taxed", "en partie taxé"),
               "input": t("ingredients taxed", "ingrédients taxés"), "over_quota_only": t("only above the import quota", "seulement au-delà du contingent")}
    if q.strip():
        k = fold(q.strip())
        hit = lookup[lookup.apply(lambda r: k in fold(" ".join(str(v) for v in [r.series, r.series_fr, r.note_en, r.note_fr])), axis=1)]
        if hit.empty:
            st.markdown(t("No match. This product does not appear on the food tariff lists mapped to the CPI, or try another word.",
                          "Aucun résultat. Ce produit ne figure pas sur les listes tarifaires alimentaires rattachées à l'IPC, ou essayez un autre mot."))
        else:
            out = hit.assign(
                y=hit.event_id.str[2:], when=hit.start + " → " + hit.end.fillna("").replace("", t("in force", "en vigueur")),
                s=[label(s) for s in hit.series], e=hit.exposure.map(exp_lab), n=hit.note_fr if FR else hit.note_en)
            table(out[["y", "rate", "e", "s", "n", "when"]].set_axis(
                [t("Year", "Année"), t("Rate", "Taux"), t("How", "Comment"), t("CPI series", "Série de l'IPC"),
                 t("Products", "Produits"), t("Period", "Période")], axis=1))
    st.caption(t("Only US-origin products are taxed. Source: official tariff lists (Finance Canada, Canada Gazette), mapped to CPI series in D18.",
                 "Seuls les produits d'origine américaine sont taxés. Source : listes tarifaires officielles (Finances Canada, Gazette du Canada), rattachées aux séries de l'IPC dans D18."))

# ------------------------------------------------------------------ 3. Prices and forecasts
if section == "prices":
    series_list = sorted(fc.series.unique(), key=label)
    default = series_list.index("Food purchased from stores") if "Food purchased from stores" in series_list else 0
    s = st.selectbox(t("CPI series", "Série de l'IPC"), series_list, index=default, format_func=label)
    h, f = cpi[cpi.series == s], fc[fc.series == s]
    band = C["band"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f.month, y=f.hi95, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=f.month, y=f.lo95, fill="tonexty", fillcolor=f"rgba({band},0.14)", line=dict(width=0), name=t("95% interval", "Intervalle 95 %")))
    fig.add_trace(go.Scatter(x=f.month, y=f.hi80, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=f.month, y=f.lo80, fill="tonexty", fillcolor=f"rgba({band},0.28)", line=dict(width=0), name=t("80% interval", "Intervalle 80 %")))
    fig.add_trace(go.Scatter(x=h.month, y=h.value, line=dict(color=C["ink"], width=2), name=t("Observed", "Observé")))
    fig.add_trace(go.Scatter(x=f.month, y=f.forecast, line=dict(color=C["blue"], width=2), name=t("Forecast", "Prévision")))
    show(style(fig, t(f"Index ({h.base.iloc[-1]})", f"Indice ({h.base.iloc[-1]})")))
    last, f12 = h.value.iloc[-1], f.forecast.iloc[-1]
    st.markdown(t(f"Forecast for {f.month.iloc[-1]}: **{pct(100 * (f12 / last - 1))}** vs {h.month.iloc[-1]} "
                  f"(80% interval {pct(100 * (f.lo80.iloc[-1] / last - 1))} to {pct(100 * (f.hi80.iloc[-1] / last - 1))}).",
                  f"Prévision pour {f.month.iloc[-1]} : **{pct(100 * (f12 / last - 1))}** par rapport à {h.month.iloc[-1]} "
                  f"(intervalle 80 % de {pct(100 * (f.lo80.iloc[-1] / last - 1))} à {pct(100 * (f.hi80.iloc[-1] / last - 1))})."))
    if s == "Cheese":
        st.markdown(t("**2026 tariff scenarios for cheese** (D06): even the high scenario stays inside the 80% interval.",
                      "**Scénarios du tarif de 2026 pour le fromage** (D06) : même le scénario haut reste dans l'intervalle à 80 %."))
        table(scen[["month", "forecast", "low (25%, temporary)", "central (60%)", "high (70%, persistent)"]].round(1).set_axis(
            [t("Month", "Mois"), t("No tariff", "Sans tarif"), t("Low 25%", "Bas 25 %"), t("Central 60%", "Central 60 %"), t("High 70%", "Haut 70 %")], axis=1))
    with st.expander(t("How good are the forecasts? (backtest)", "Quelle est la qualité des prévisions ? (backtest)")):
        piv = bts[bts.h.isin([1, 3, 6, 12])].pivot(index="h", columns="model", values="mase").round(2).reset_index()
        table(piv.rename(columns={"h": t("Months ahead", "Mois d'avance"), "ets": "ETS", "lightgbm": "LightGBM",
                                  "seasonal_naive": t("Same as last year", "Comme l'an dernier")}))
        st.caption(t("Error (MASE) measured on 2019–2025 as if the forecasts had been made in the past; lower is better (D08, D23).",
                     "Erreur (MASE) mesurée sur 2019–2025 comme si les prévisions avaient été faites dans le passé ; plus bas est meilleur (D08, D23)."))

# ------------------------------------------------------------------ 4. Provinces
if section == "provinces":
    lastp = prov[prov.month == prov.month.max()].sort_values("yoy")
    names = [PROV_FR.get(g, g) if FR else g for g in lastp.geo]
    fig = go.Figure(go.Bar(x=lastp.yoy, y=names, orientation="h",
                           marker=dict(color=[C["blue"] if g != "Canada" else C["ink"] for g in lastp.geo]),
                           text=[pct(v) for v in lastp.yoy], textposition="outside", textfont=dict(color=C["muted"]),
                           cliponaxis=False, hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    fig.update_layout(bargap=0.35)
    show(style(fig, "", height=460).update_xaxes(title=t(f"Grocery price change over 12 months to {prov.month.max()} (%)",
                                                         f"Variation des prix en magasin sur 12 mois jusqu'à {prov.month.max()} (%)"), showgrid=True, gridcolor=C["grid"]))
    geo = st.selectbox(t("Compare over time", "Comparer dans le temps"), [g for g in lastp.geo if g != "Canada"],
                       index=list(g for g in lastp.geo if g != "Canada").index("Ontario"), format_func=lambda g: PROV_FR.get(g, g) if FR else g)
    fig = go.Figure()
    for g, col in [("Canada", C["ink"]), (geo, C["blue"])]:
        d = prov[prov.geo == g]
        fig.add_trace(go.Scatter(x=d.month, y=d.yoy, line=dict(color=col, width=2), name=PROV_FR.get(g, g) if FR else g))
    show(style(fig, t("Change over 12 months (%)", "Variation sur 12 mois (%)"), height=360))
    st.caption(t("Statistics Canada publishes food prices for the ten provinces, Whitehorse and Yellowknife (D13).",
                 "Statistique Canada publie les prix alimentaires des dix provinces, de Whitehorse et de Yellowknife (D13)."))

# ------------------------------------------------------------------ 5. Tariff effects (analysts)
if section == "effects":
    ev = st.radio(t("Episode", "Épisode"), ["CA2025", "CA2018"], horizontal=True,
                  format_func=lambda e: {"CA2025": t("2025 (25%)", "2025 (25 %)"), "CA2018": t("2018 (10%)", "2018 (10 %)")}[e])
    d = sc[sc.event_id == ev].sort_values("effect_during")
    fig = go.Figure()
    for g, col in [("treated", C["blue"]), ("placebo", C["orange"])]:
        dd = d[d.group == g]
        if len(dd):
            fig.add_trace(go.Scatter(x=dd.effect_during, y=[label(s) for s in dd.series], mode="markers",
                                     marker=dict(color=col, size=10, line=dict(color=C["bg"], width=1.5)),
                                     name={"treated": t("Tariffed", "Taxée"), "placebo": t("Placebo (taxed only above quota)", "Placebo (taxé seulement hors contingent)")}[g],
                                     customdata=dd[["p_value"]], hovertemplate="%{y}: %{x:.1f}% (p=%{customdata[0]:.2f})<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=C["muted"]))
    fig.update_yaxes(type="category", dtick=1, automargin=True)
    show(style(fig, "", height=max(420, 24 * len(d))))
    st.caption(t("Gap between each tariffed series and a weighted mix of similar untaxed series (synthetic control), average over the tariff months, in %. "
                 "p = share of untaxed series with a gap at least as unusual (D19, D20).",
                 "Écart entre chaque série taxée et un mélange pondéré de séries semblables non taxées (contrôle synthétique), moyenne sur les mois du tarif, en %. "
                 "p = part des séries non taxées avec un écart au moins aussi inhabituel (D19, D20)."))
    pt = ptc[ptc.event_id == ev].copy()
    names = {"all treated": t("All tariffed series", "Toutes les séries taxées"),
             "without coffee and confectionery": t("Without coffee and confectionery", "Sans le café ni la confiserie"),
             "raw (D21)": t("Not adjusted", "Non corrigé"),
             "commodity-adjusted (lags 0-11)": t("World prices removed (lags 0-11)", "Cours mondiaux retirés (retards 0-11)"),
             "commodity-adjusted (lags 0-17)": t("World prices removed (lags 0-17)", "Cours mondiaux retirés (retards 0-17)")}
    out = pd.DataFrame({t("Series", "Séries"): pt["sample"].map(names), t("Estimate", "Estimation"): pt.outcome.map(names),
                        t("Share passed on", "Part répercutée"): (100 * pt.pass_through).round(0).astype(int).astype(str) + " %",
                        t("95% interval", "Intervalle à 95 %"): (100 * pt.lo).round(0).astype(int).astype(str) + " % ; " + (100 * pt.hi).round(0).astype(int).astype(str) + " %",
                        "p": pt.p.round(2)})
    st.markdown(t("**Share of the tariff passed on to prices** (D21–D22)", "**Part du tarif répercutée sur les prix** (D21–D22)"))
    table(out)

# ------------------------------------------------------------------ 6. Average prices
if section == "average":
    item_name = lambda i: avg.loc[avg.item == i, "item_fr"].iloc[0] if FR else i
    items = sorted(avg.item.unique(), key=item_name)
    it = st.selectbox(t("Product", "Produit"), items, format_func=item_name)
    a = avg[avg.item == it]
    fig = go.Figure(go.Scatter(x=a.month, y=a.price, line=dict(color=C["blue"], width=2), name="$"))
    fig.add_vline(x="2024-01", line=dict(color=C["muted"], dash="dot"))
    show(style(fig, t("Average price, Canada ($)", "Prix moyen, Canada ($)")))
    st.caption(t("For information only: Statistics Canada changed the sample in January 2024 (dotted line), so changes across that date are not pure price changes (D04).",
                 "À titre indicatif : Statistique Canada a modifié l'échantillon en janvier 2024 (ligne pointillée), les variations autour de cette date ne sont donc pas de pures variations de prix (D04)."))

# ------------------------------------------------------------------ 7. Questions
if section == "questions":
    if assistant.api_key():
        st.markdown(t("#### Ask in your own words", "#### Posez votre question"))
        st.caption(t("AI assistant (Claude) answering only from this dashboard's verified facts, with their decision numbers. "
                     "It says so when the facts do not cover a question (D28).",
                     "Assistant IA (Claude) qui répond uniquement à partir des faits vérifiés de ce tableau de bord, avec leurs numéros de décision. "
                     "Il le dit quand les faits ne couvrent pas une question (D28)."))
        st.session_state.setdefault("ai_count", 0)
        aq = st.text_area(t("Your question", "Votre question"), max_chars=assistant.MAX_QUESTION_CHARS, key="ai_q", height=80)
        if st.button(t("Ask", "Demander"), disabled=st.session_state.ai_count >= 10) and aq.strip():
            st.session_state.ai_count += 1
            with st.spinner(t("Reading the facts...", "Lecture des faits...")):
                answer, _info = assistant.ask(aq.strip(), facts(), "fr" if FR else "en")
            st.markdown(answer)
        if st.session_state.ai_count >= 10:
            st.caption(t("Limit of 10 questions per visit reached.", "Limite de 10 questions par visite atteinte."))
        st.markdown(t("#### Verified answers", "#### Réponses vérifiées"))
    if rag.enabled():  # RAG removed from the app for now (D32); the RAG secret set to "on" shows it again
        st.markdown(t("#### Search the official documents", "#### Chercher dans les documents officiels"))
        st.caption(t("Bank of Canada studies, Canada Gazette orders, Statistics Canada methodology and this project's decision log: "
                     "765 passages ranked by keywords (BM25; multilingual embeddings, Reciprocal Rank Fusion and a cross-encoder were also evaluated, D30). "
                     "Questions in French also find English documents, less reliably.",
                     "Études de la Banque du Canada, ordonnances de la Gazette du Canada, méthodologie de Statistique Canada et journal des décisions du projet : "
                     "765 passages classés par mots-clés (BM25 ; des embeddings multilingues, Reciprocal Rank Fusion et un cross-encoder ont aussi été évalués, D30). "
                     "Une question en français trouve aussi les documents en anglais, de façon moins fiable."))
        n_en = int((~rag.corpus().doc_id.str.endswith("-FR")).sum())
        st.caption(t(f"Language: {n_en} of the {len(rag.corpus())} passages are in English, the language of the sources. "
                     "Ask in English or French: the written answer follows the language of your question; quoted passages stay in their original language.",
                     f"Langue : {n_en} des {len(rag.corpus())} passages sont en anglais, la langue des sources. "
                     "Posez votre question en français ou en anglais : la réponse rédigée suit la langue de votre question ; les passages cités restent dans leur langue d'origine.")
                   + ("" if rag.provider() else t(" No written answer is available in this version: only the passages are shown.",
                                                  " Aucune réponse rédigée n'est disponible dans cette version : seuls les passages sont affichés.")))
        dq = st.text_input(t("Your question about the documents", "Votre question sur les documents"), key="doc_q",
                           placeholder=t("e.g. Which data did the Bank of Canada use for 2025?", "ex. : Quelles données la Banque du Canada a-t-elle utilisées pour 2025 ?"))
        if dq.strip():
            with st.spinner(t("Searching...", "Recherche...")):
                hits = rag.search(dq.strip(), 5, rag.APP_SEARCH)  # best light method on both question sets (D30, A33)
            if rag.provider():
                st.markdown(rag.answer(dq.strip(), hits, "fr" if FR else "en"))
                if rag.provider() == "gemini":
                    st.caption(t("Answer written by Gemini (Google, free tier: questions may be used by Google to improve its products; "
                                 "do not enter personal information).",
                                 "Réponse rédigée par Gemini (Google, offre gratuite : les questions peuvent servir à Google pour améliorer ses produits ; "
                                 "n'écrivez pas d'informations personnelles)."))
            for h in hits.itertuples():
                with st.expander(f"[{h.chunk_id}] {h.title}"):
                    st.markdown(rag.clean_start(h.text))
                    st.caption(f"{h.licence} · {h.url}")
    st.markdown(t("#### Verified answers", "#### Réponses vérifiées") if not assistant.api_key() else "")
    st.markdown(t("Answers come from a fixed set of verified answers, each with its source. No AI model is used here, so answers cannot be invented.",
                  "Les réponses viennent d'un ensemble fixe de réponses vérifiées, chacune avec sa source. Aucun modèle d'IA n'est utilisé ici : les réponses ne peuvent pas être inventées."))
    q = st.text_input(t("Your question", "Votre question"), key="faq_q")
    lk = "fr" if FR else "en"

    def score(item: dict, text: str) -> int:
        return len(set(re.findall(r"\w{4,}", text.lower())) & set(item["keywords"]))

    if q:
        best = max(FAQ, key=lambda it: score(it, q))
        if score(best, q) == 0:
            st.markdown(t("No verified answer matches this question. Try one of the questions below.",
                          "Aucune réponse vérifiée ne correspond. Essayez une des questions ci-dessous."))
        else:
            st.markdown(f"**{best['q'][lk]}**\n\n{best['a'][lk]}\n\n*{t('Source', 'Source')} : {best['source']}*")
    for it in FAQ:
        with st.expander(it["q"][lk]):
            st.markdown(it["a"][lk])
            st.caption(f"{t('Source', 'Source')} : {it['source']}")

# ------------------------------------------------------------------ 8. Method and data
if section == "method":
    st.markdown(t(
        """#### The method in five steps
1. **What was taxed?** The official tariff lists (2018, 2025, 2026) are read line by line and each food product is placed in the consumer price index (CPI) series where Statistics Canada prices it.
2. **Did prices rise because of the tariff?** Each taxed series is compared with a "twin" built from similar untaxed series that moved like it before the tariff. The gap after the tariff is the effect.
3. **How much of the tariff reached the shelf?** The effect is divided by what a full pass-through would give, given how much of each series is made of US goods.
4. **Tariff or world prices?** The part explained by world prices of coffee, cocoa, sugar, wheat and other commodities is removed first.
5. **Where are prices heading?** Forecasts are tested on 2019–2025 as if made in the past, and their intervals are checked against what actually happened.""",
        """#### La méthode en cinq étapes
1. **Qu'est-ce qui a été taxé ?** Les listes tarifaires officielles (2018, 2025, 2026) sont lues ligne par ligne et chaque produit alimentaire est placé dans la série de l'indice des prix à la consommation (IPC) où Statistique Canada le relève.
2. **Les prix ont-ils monté à cause du tarif ?** Chaque série taxée est comparée à un « jumeau » construit à partir de séries semblables non taxées qui évoluaient comme elle avant le tarif. L'écart après le tarif est l'effet.
3. **Quelle part du tarif a atteint les rayons ?** L'effet est divisé par ce que donnerait une transmission complète, compte tenu de la part des produits américains dans chaque série.
4. **Tarif ou cours mondiaux ?** La part expliquée par les cours mondiaux du café, du cacao, du sucre, du blé et d'autres matières premières est retirée d'abord.
5. **Où vont les prix ?** Les prévisions sont testées sur 2019–2025 comme si elles avaient été faites dans le passé, et leurs intervalles sont comparés à ce qui s'est réellement passé."""))
    st.markdown(t("#### Limits", "#### Limites"))
    st.markdown(t(
        """- Monthly public indexes mix taxed and untaxed products: small effects cannot be measured precisely.
- The share of US goods is approximated from import values at the border.
- A placebo test on dairy products partly failed: dairy prices follow their own regulated dynamics.""",
        """- Les indices mensuels publics mélangent produits taxés et non taxés : les petits effets ne peuvent pas être mesurés précisément.
- La part des produits américains est approchée à partir des valeurs d'importation à la frontière.
- Un test placebo sur les produits laitiers a en partie échoué : les prix laitiers suivent leur propre dynamique réglementée."""))
    st.markdown(t("#### Download the data", "#### Télécharger les données"))
    d1, d2, d3, d4 = st.columns(4)
    for col, (fname, en, fr) in zip([d1, d2, d3, d4], [("forecasts.csv", "Forecasts", "Prévisions"),
                                                        ("tariff_lookup.csv", "Taxed products", "Produits taxés"),
                                                        ("sc_results.csv", "Tariff effects", "Effets des tarifs"),
                                                        ("province_food.csv", "Provinces", "Provinces")]):
        col.download_button(t(en, fr), (DATA / fname).read_bytes(), file_name=fname, mime="text/csv", use_container_width=True)
    st.markdown(t("#### Cite", "#### Citer"))
    st.code(f"Doe, D. (2026). Canadian grocery prices and counter-tariffs: a public-data monitor [Software and dashboard]. {REPO}", language=None)
    st.markdown(t(f"Full decision log, references and code: [{REPO}]({REPO}). Data are public (Statistics Canada Open Licence, Bank of Canada, UN Comtrade, World Bank).",
                  f"Journal des décisions, références et code complets : [{REPO}]({REPO}). Les données sont publiques (licence ouverte de Statistique Canada, Banque du Canada, UN Comtrade, Banque mondiale)."))
