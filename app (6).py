import re
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st

# ----------------------------- Page setup -----------------------------------
st.set_page_config(
    page_title="ARIV Research Discovery Agent",
    page_icon="🔬",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ariv-ink: #172554;
        --ariv-muted: #64748b;
        --ariv-purple: #6d28d9;
        --ariv-blue: #2563eb;
        --ariv-teal: #0f766e;
        --ariv-orange: #ea580c;
    }
    .stApp {
        background:
          radial-gradient(ellipse at 0% 0%, rgba(139,92,246,.13), transparent 34%),
          radial-gradient(ellipse at 100% 8%, rgba(6,182,212,.12), transparent 30%),
          linear-gradient(180deg, #f8faff 0%, #f4f7ff 50%, #fbfdff 100%);
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stHeader"] { background: rgba(248,250,255,.78); }
    .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1500px; }
    h1, h2, h3, [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    .hero {
        position: relative; overflow: hidden;
        padding: 2rem 2.1rem; border-radius: 26px;
        background: linear-gradient(118deg, #17113b 0%, #4338ca 42%, #087eaa 75%, #0d9488 100%);
        color: white; margin: .15rem 0 1rem 0;
        box-shadow: 0 18px 45px rgba(49,46,129,.22);
        border: 1px solid rgba(255,255,255,.35);
    }
    .hero:after {
        content: ''; position: absolute; width: 270px; height: 270px; right: -55px; top: -125px;
        border: 1px solid rgba(255,255,255,.22); border-radius: 50%;
        box-shadow: 0 0 0 26px rgba(255,255,255,.05), 0 0 0 55px rgba(255,255,255,.04);
    }
    .hero h1 { color: white !important; margin: 0; font-size: clamp(1.8rem, 3.4vw, 2.8rem); letter-spacing: -.045em; }
    .hero p { color: #e0f2fe !important; margin: .65rem 0 0 0; font-size: 1.04rem; max-width: 850px; line-height: 1.65; }
    .hero-kicker { display: inline-block; padding: .32rem .72rem; border: 1px solid rgba(255,255,255,.3);
        border-radius: 999px; color: #e0e7ff; font-size: .76rem; font-weight: 700;
        letter-spacing: .12em; text-transform: uppercase; margin-bottom: .85rem; background: rgba(255,255,255,.1); }
    .hero-pills { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.15rem; }
    .hero-pill { padding: .4rem .7rem; border-radius: 10px; background: rgba(255,255,255,.13);
        border: 1px solid rgba(255,255,255,.16); color: white; font-size: .82rem; }
    .section-kicker { color: #6d28d9; font-size: .74rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .intro-card { background: rgba(255,255,255,.82); border: 1px solid #e0e7ff; border-radius: 18px;
        padding: 1rem 1.15rem; box-shadow: 0 5px 20px rgba(30,41,59,.035); }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(255,255,255,.98), rgba(239,246,255,.92));
        padding: 1rem 1.05rem; border-radius: 17px; border: 1px solid #dbeafe;
        box-shadow: 0 7px 20px rgba(37,99,235,.06);
    }
    div[data-testid="stMetricLabel"] { color: #475569; font-weight: 700; }
    div[data-testid="stMetricValue"] { color: #312e81; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #17113b 0%, #25215a 54%, #123b60 100%);
    }
    [data-testid="stSidebar"] * { color: #f8fafc; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { color: #e0e7ff; font-weight: 600; }
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(255,255,255,.12) !important;
        border: 1px solid rgba(255,255,255,.32) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #ffffff !important;
    }
    [data-testid="stSidebar"] textarea::placeholder,
    [data-testid="stSidebar"] input::placeholder { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #dbeafe; }
    [data-testid="stSidebar"] textarea:focus,
    [data-testid="stSidebar"] input:focus {
        border-color: #a5b4fc !important;
        box-shadow: 0 0 0 2px rgba(165,180,252,.25) !important;
    }
    [data-baseweb="popover"] [role="option"] { color: #172554 !important; }
    .stButton > button, .stDownloadButton > button {
        border-radius: 12px; font-weight: 700; border: 0;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(105deg, #6d28d9, #2563eb, #0891b2); color: white;
        box-shadow: 0 8px 18px rgba(79,70,229,.22);
    }
    .stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(37,99,235,.15); }
    [data-testid="stTabs"] [role="tablist"] { gap: .5rem; border-bottom: 1px solid #dbeafe; }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 12px 12px 0 0; padding: .65rem 1rem; font-weight: 700;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: #ede9fe; color: #5b21b6; border-bottom: 3px solid #7c3aed;
    }
    .ariv-card { border: 1px solid #dbeafe; border-radius: 16px; padding: 1rem;
        margin: .6rem 0; background: rgba(255,255,255,.8); box-shadow: 0 4px 15px rgba(15,23,42,.035); }
    .step-chip { display:inline-block; padding:.3rem .65rem; border-radius:999px;
        background:#ede9fe; color:#5b21b6; font-size:.78rem; font-weight:800; }
    div[data-testid="stAlert"] { border-radius: 14px; }
    .stDataFrame, [data-testid="stDataFrame"] { border: 1px solid #dbeafe; border-radius: 14px; overflow: hidden; }
    hr { border-color: #dbeafe; }
    @media (max-width: 700px) {
        .hero { padding: 1.35rem; border-radius: 20px; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    </style>
    <div class="hero">
      <div class="hero-kicker">Free academic research workspace</div>
      <h1>🔬 ARIV Research Discovery Agent</h1>
      <p>Turn a research idea into a clearer evidence trail. Discover scholarly publications, explore open-access papers, inspect recent work, and validate potential research gaps.</p>
      <div class="hero-pills">
        <span class="hero-pill">🧭 Analysis</span>
        <span class="hero-pill">💡 Recommendation</span>
        <span class="hero-pill">🛠️ Implementation</span>
        <span class="hero-pill">✅ Validation</span>
        <span class="hero-pill">🔓 No paid AI key</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="intro-card">✨ <b>Research smarter, not just faster.</b> Search OpenAlex metadata, review publication details, open available PDF links, and export your results. <span style="color:#64748b">Live internet connection required; no Groq, OpenAI, or paid LLM API key.</span></div>',
    unsafe_allow_html=True,
)


OPENALEX_API = "https://api.openalex.org/works"
USER_AGENT = "ARIVResearchDiscoveryAgent/1.0 (academic literature discovery)"


def clean_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def reconstruct_abstract(inverted_index):
    """Convert OpenAlex's abstract inverted index to readable text, when available."""
    if not isinstance(inverted_index, dict):
        return ""
    positions = {}
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions[index] = word
    if not positions:
        return ""
    return " ".join(positions[i] for i in sorted(positions))


def get_author_names(authorships, limit=6):
    names = []
    for author_item in (authorships or [])[:limit]:
        author = author_item.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(name)
    return ", ".join(names) if names else "Authors not listed in metadata"


def get_publication_source(work):
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    if source.get("display_name"):
        return source["display_name"]
    locations = work.get("locations") or []
    for item in locations:
        src = (item.get("source") or {}).get("display_name")
        if src:
            return src
    return "Publication venue not listed"


def get_links(work):
    doi = work.get("doi") or ""
    doi_url = doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else "")
    primary = work.get("primary_location") or {}
    best = work.get("best_oa_location") or {}
    pdf = best.get("pdf_url") or primary.get("pdf_url") or ""
    landing = best.get("landing_page_url") or primary.get("landing_page_url") or ""
    if not landing:
        landing = doi_url or work.get("id") or ""
    return pdf, landing, doi_url


def search_openalex(topic, max_results=25, from_year=None, open_access_only=False):
    params = {
        "search": topic,
        "per-page": min(max_results, 100),
        "sort": "publication_date:desc",
        "mailto": "research-agent@example.com",
    }
    filters = []
    if from_year:
        filters.append(f"from_publication_date:{from_year}-01-01")
    if open_access_only:
        filters.append("is_oa:true")
    if filters:
        params["filter"] = ",".join(filters)
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(OPENALEX_API, params=params, headers=headers, timeout=35)
    response.raise_for_status()
    payload = response.json()
    rows = []
    for work in payload.get("results", []):
        title_list = work.get("title") or work.get("display_name") or "Untitled record"
        title = clean_text(title_list)
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        pdf_url, landing_url, doi_url = get_links(work)
        publication_date = work.get("publication_date") or ""
        year = work.get("publication_year") or (int(publication_date[:4]) if publication_date[:4].isdigit() else "")
        rows.append({
            "Title": title,
            "Year": year,
            "Authors": get_author_names(work.get("authorships")),
            "Publication venue": get_publication_source(work),
            "Citations": work.get("cited_by_count", 0),
            "Open access": bool(work.get("open_access", {}).get("is_oa", False)),
            "PDF available": bool(pdf_url),
            "PDF link": pdf_url,
            "Article / DOI link": landing_url,
            "DOI": doi_url,
            "Abstract": abstract,
            "Work type": work.get("type") or "",
            "OpenAlex record": work.get("id") or "",
        })
    return pd.DataFrame(rows)


def build_search_links(topic):
    encoded = quote_plus(topic)
    return {
        "Google Scholar": f"https://scholar.google.com/scholar?q={encoded}",
        "Semantic Scholar": f"https://www.semanticscholar.org/search?q={encoded}",
        "CORE": f"https://core.ac.uk/search?q={encoded}",
        "DOAJ": f"https://doaj.org/search/articles/{encoded}",
        "OpenAlex": f"https://openalex.org/works?search={encoded}",
    }


def topic_analysis(topic, df, current_year):
    """Evidence-led descriptive analysis, not a claim of exhaustive coverage."""
    if df.empty:
        return {
            "summary": "No records were returned by OpenAlex for this query. Try broader keywords, synonyms, or a related technical term.",
            "gaps": [
                "The current search returned no records; this does not prove that no research exists.",
                "Try alternative terminology, abbreviations, and adjacent research fields.",
                "Search a second database and compare results before claiming a research gap.",
            ],
            "recommendations": [
                "Expand the topic into 2–4 related keyword combinations.",
                "Search Google Scholar and Semantic Scholar using the links below.",
                "Document the search date, database, exact query, and screening criteria.",
            ],
        }
    recent = df[df["Year"].apply(lambda x: str(x).isdigit() and int(x) >= current_year - 3)]
    venues = df["Publication venue"].replace("Publication venue not listed", pd.NA).dropna()
    top_venues = venues.value_counts().head(5).index.tolist()
    oa_count = int(df["Open access"].sum())
    pdf_count = int(df["PDF available"].sum())
    summary = (
        f"OpenAlex returned {len(df)} records for “{topic}”. "
        f"{len(recent)} records are from {current_year - 3}–{current_year}; "
        f"{oa_count} are marked open access and {pdf_count} have a PDF URL in the metadata. "
        "These counts describe this search result set, not the entire research literature."
    )
    gaps = [
        "Check whether recent papers evaluate the method on real-world data as well as simulation; only claim this gap after reading the full papers.",
        "Compare datasets, benchmark conditions, baselines, and evaluation metrics across the retrieved studies.",
        "Look for limitations and future-work statements in the most relevant recent papers; these are stronger gap evidence than keyword counts alone.",
    ]
    if len(recent) == 0:
        gaps.insert(0, "Few or no records in this result set fall within the recent three-year window; broaden the query and verify coverage in another database.")
    recommendations = [
        "Start with the most relevant recent papers, then use their reference lists and citing papers for backward/forward snowballing.",
        "Record each paper's problem, method, dataset, baseline, metrics, key findings, and limitations in a literature matrix.",
        "Choose a narrow, testable research question and validate novelty with multiple databases and supervisor review.",
    ]
    return {"summary": summary, "gaps": gaps, "recommendations": recommendations, "top_venues": top_venues}


# ----------------------------- Sidebar --------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Research studio")
    st.caption("Set your search, then launch the ARIV workflow.")
    topic = st.text_input(
        "🔎 Research topic",
        value="AI-based maximum power point tracking for photovoltaic systems under partial shading",
        placeholder="Type your research topic here…",
        help="Click the field and type or paste your research title/keywords.",
    )
    max_results = st.slider("Maximum records", 10, 50, 25, step=5)
    all_years = st.checkbox("Search all publication years", value=False)
    publication_year = st.number_input(
        "📅 From publication year",
        min_value=1900,
        max_value=datetime.now().year,
        value=2020,
        step=1,
        disabled=all_years,
        help="Type a year (for example, 2023) or use the arrows. Results from this year onward will be searched.",
    )
    open_access_only = st.checkbox("Only records marked open access", value=False)
    run_search = st.button("🔎 Analyze research topic", type="primary", use_container_width=True)
    st.divider()
    st.caption("No AI model API key is required. Search availability and coverage depend on external scholarly databases.")

if "research_df" not in st.session_state:
    st.session_state.research_df = pd.DataFrame()
if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""

if run_search:
    if not topic.strip():
        st.error("Please enter a research topic.")
    else:
        from_year = None if all_years else int(publication_year)
        try:
            with st.spinner("Searching scholarly metadata and preparing the ARIV workflow…"):
                result_df = search_openalex(
                    topic.strip(),
                    max_results=max_results,
                    from_year=from_year,
                    open_access_only=open_access_only,
                )
                st.session_state.research_df = result_df
                st.session_state.last_topic = topic.strip()
                st.session_state.research_meta = {
                    "publication_year": "Any year" if all_years else f"Since {int(publication_year)}",
                    "open_access_only": open_access_only,
                    "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            if result_df.empty:
                st.warning("No records found. Try broader keywords or remove the open-access filter.")
            else:
                st.success(f"Retrieved {len(result_df)} scholarly records. Review the evidence before drawing conclusions.")
        except requests.RequestException as exc:
            st.error(f"Could not reach OpenAlex. Check your internet connection and try again. Details: {exc}")
        except (ValueError, KeyError) as exc:
            st.error(f"Could not process the returned research metadata: {exc}")

df = st.session_state.research_df
active_topic = st.session_state.last_topic

if not df.empty:
    analysis = topic_analysis(active_topic, df, datetime.now().year)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records retrieved", len(df))
    c2.metric("Recent (last 3 years)", int(df["Year"].apply(lambda x: str(x).isdigit() and int(x) >= datetime.now().year - 3).sum()))
    c3.metric("Open-access records", int(df["Open access"].sum()))
    c4.metric("PDF links found", int(df["PDF available"].sum()))

    st.markdown("## 🧭 Your ARIV research workspace")
    st.caption("Move through each stage to turn search results into a documented research direction.")
    tabs = st.tabs(["A — Analysis", "R — Recommendation", "I — Implementation", "V — Validation"])

    with tabs[0]:
        st.markdown("### 🔎 A — Analysis")
        st.write(analysis["summary"])
        st.markdown("**Publication venues found in the retrieved records**")
        venues = df["Publication venue"].value_counts().head(10).rename_axis("Venue").reset_index(name="Records")
        st.dataframe(venues, use_container_width=True, hide_index=True)
        st.markdown("**Research records**")
        display_cols = ["Title", "Year", "Authors", "Publication venue", "Citations", "Open access", "PDF available", "Article / DOI link", "PDF link"]
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Article / DOI link": st.column_config.LinkColumn("Article / DOI", display_text="Open record"),
                "PDF link": st.column_config.LinkColumn("PDF", display_text="Open/download PDF"),
            },
        )
        st.caption("Venue information is taken from OpenAlex metadata. It can be missing or incomplete; verify journal/conference details on the publisher's page.")

    with tabs[1]:
        st.markdown("### 💡 R — Recommendation")
        st.write("Use these as prompts for further checking, not as automatically proven research gaps.")
        st.markdown("**Potential gap-investigation directions**")
        for item in analysis["gaps"]:
            st.markdown(f"- {item}")
        st.markdown("**Suggested next steps**")
        for item in analysis["recommendations"]:
            st.markdown(f"- {item}")
        st.info("A reliable novelty claim requires full-text reading, synonym searches, database coverage checks, and a documented screening method.")

    with tabs[2]:
        st.markdown("### 🛠️ I — Implementation")
        st.write("Download the retrieved metadata, open available full-text PDFs, and build a literature matrix.")
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download research records (CSV)",
            data=csv_bytes,
            file_name=f"research_records_{re.sub(r'[^a-zA-Z0-9]+', '_', active_topic).strip('_')[:60]}.csv",
            mime="text/csv",
            type="primary",
        )
        st.markdown("**Additional scholarly search portals**")
        for label, url in build_search_links(active_topic).items():
            st.markdown(f"- [{label}]({url})")
        st.markdown("**Suggested literature matrix columns**")
        st.code("Citation | Research problem | Method | Dataset / system | Baselines | Metrics | Main findings | Limitations | Future work | Relevance to my topic", language="text")

    with tabs[3]:
        st.markdown("### ✅ V — Validation")
        st.markdown("Before accepting a finding or gap, verify:")
        checks = [
            "I opened the publisher or repository record and checked the title, authors, year, and venue.",
            "I read the abstract and, where possible, the full paper rather than relying only on metadata.",
            "I checked whether the PDF is legally available from an author, repository, or open-access publisher.",
            "I searched synonyms and adjacent terms in at least one additional scholarly database.",
            "I recorded the search date, query, inclusion criteria, and exclusion criteria.",
            "I compared the proposed gap against limitations and future-work sections of relevant papers.",
        ]
        for item in checks:
            st.checkbox(item, key="validation_" + str(checks.index(item)))
        st.warning("The app cannot guarantee that all papers on a topic have been found or that a topic is novel. Open-access flags and PDF links may be incomplete or may change.")

    st.divider()
    st.markdown("## 📚 Finding downloadable papers")
    st.write(
        "Use the **Open/download PDF** link when one is available. If no PDF link is shown, open the article/DOI record and check the publisher, institutional repository, or author manuscript. "
        "The app does not bypass paywalls or download copyrighted papers without permission."
    )
else:
    st.markdown("## 🚀 Start your research journey")
    st.markdown(
        """
        1. Enter a research topic or draft title in the sidebar.
        2. Select a publication period and whether to limit results to open-access records.
        3. Click **Analyze research topic**.
        4. Review the four ARIV stages: Analysis, Recommendation, Implementation, and Validation.
        5. Open article/PDF links and download the research metadata as CSV.
        """
    )
    st.markdown("### 🎯 Try one of these example topics")
    examples = [
        "Digital twin for photovoltaic performance under dust/soiling",
        "Machine learning for induction motor fault diagnosis using thermal images",
        "Wireless power transfer for electric vehicle charging",
        "AI-based maximum power point tracking under partial shading",
        "Small wind turbine performance prediction using machine learning",
    ]
    for example in examples:
        st.markdown(f"- {example}")

with st.expander("🔐 Privacy, limitations, and free-tier notes"):
    st.markdown(
        """
        - No Groq, OpenAI, or other paid LLM API is used.
        - Scholarly search uses the public OpenAlex API; the app needs internet access.
        - Search results are metadata records, not a guarantee of a complete systematic review.
        - Full-text availability is determined by the metadata returned by OpenAlex and may be incomplete.
        - The app only links to PDFs/records exposed by metadata; it does not circumvent publisher access controls.
        - Do not present automatically suggested gap directions as proven novelty claims.
        - For a publishable systematic review, define a protocol, document database queries, deduplicate records, and apply transparent inclusion/exclusion criteria.
        """
    )
    st.markdown("**Data source:** [OpenAlex API documentation](https://help.openalex.org/api/) · [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)")
