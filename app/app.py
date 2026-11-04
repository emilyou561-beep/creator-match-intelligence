"""Streamlit interface for the AI Creator Matching Tool MVP."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "python"))

DATABASE_FILE = PROJECT_DIR / "database" / "creator_matching.db"
if not DATABASE_FILE.exists():
    subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "setup_database.py")],
        cwd=PROJECT_DIR,
        check=True,
    )

from campaign_parser import available_tags, parse_campaign_description  # noqa: E402
from analytics import build_analytics  # noqa: E402
from matcher import match_creators  # noqa: E402


st.set_page_config(
    page_title="Creator Match Intelligence",
    page_icon="✦",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #191616;
        --paper: #fffdf9;
        --coral: #ef5269;
        --orange: #f47854;
        --peach: #f7c28f;
        --pink: #efb8df;
        --blue: #73cdef;
        --aqua: #54c7c8;
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--coral);
        background-image:
            linear-gradient(rgba(247, 190, 132, .32) 1px, transparent 1px),
            linear-gradient(90deg, rgba(247, 190, 132, .32) 1px, transparent 1px),
            radial-gradient(circle at 82% 8%, rgba(244, 120, 84, .95), transparent 34%),
            linear-gradient(135deg, #ef4765 0%, #ef5b67 52%, #f49278 100%);
        background-size: 54px 54px, 54px 54px, auto, auto;
    }

    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important;}
    #MainMenu, footer {visibility: hidden;}

    .block-container {
        position: relative;
        max-width: 1120px;
        margin-top: 2.4rem;
        margin-bottom: 4rem;
        padding: 5.7rem 3.2rem 3rem;
        background: var(--paper);
        border: 1.5px solid var(--ink);
        border-radius: 26px;
        box-shadow: 18px 18px 0 var(--peach);
    }

    .block-container::before {
        content: "−   □   ×";
        position: absolute;
        inset: 0 0 auto 0;
        height: 43px;
        padding: 7px 18px 0 0;
        background: var(--pink);
        border-bottom: 1.5px solid var(--ink);
        color: var(--ink);
        font: 800 24px/1 Arial, sans-serif;
        text-align: right;
        letter-spacing: .08em;
    }

    html, body, [class*="css"] {font-family: Arial, Helvetica, sans-serif; color: var(--ink);}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stCaptionContainer"] p,
    [data-testid="stExpander"] p,
    [data-testid="stMetricLabel"] p {
        color:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
    }
    h1, h2, h3 {font-family: Arial Black, Arial, Helvetica, sans-serif !important; color:var(--ink) !important;}
    h1 {letter-spacing:-.055em !important;}

    .project-nav {
        display:flex;
        justify-content:space-between;
        align-items:center;
        color:var(--ink) !important;
        font-weight:800;
        margin-bottom:1.7rem;
        text-transform:lowercase;
    }
    .project-nav span {font-size:.92rem; font-weight:600; text-transform:none;}

    .hero-wrap {position:relative; padding:1.2rem 0 1rem;}
    .hero-pill {
        display:inline-block;
        padding:.48rem 1.15rem;
        border:1.5px solid var(--ink);
        border-radius:999px;
        background:var(--blue);
        font-weight:900;
        color:var(--ink) !important;
        letter-spacing:.045em;
        transform:rotate(-2deg);
        box-shadow:3px 3px 0 var(--ink);
    }
    .hero-title {
        max-width:900px;
        margin:.9rem 0 .75rem;
        font-family:Arial Black, Arial, sans-serif;
        font-size:clamp(3.5rem, 7vw, 6.2rem);
        line-height:.88;
        letter-spacing:-.07em;
        text-transform:uppercase;
        color:var(--ink) !important;
        font-weight:900;
    }
    .subtitle {color:#403a3a; max-width:760px; font-size:1.08rem; line-height:1.55; margin-bottom:1.4rem;}
    [data-testid="stForm"] {
        border:1.5px solid var(--ink);
        border-radius:22px;
        padding:1.5rem 1.5rem 1.2rem;
        background:#fff;
        box-shadow:8px 8px 0 #f6d1e9;
    }
    [data-testid="stWidgetLabel"] p {font-weight:800 !important; color:var(--ink) !important;}
    [role="radiogroup"] p,
    textarea,
    input,
    [data-baseweb="select"] *,
    [data-testid="stMultiSelect"] * {
        color:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
    }
    textarea, [data-baseweb="select"] > div {
        border-color:var(--ink) !important;
        border-radius:14px !important;
        background:#fffdf9 !important;
    }
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background:var(--blue) !important;
        color:var(--ink) !important;
        border:1px solid var(--ink);
    }
    [data-testid="stFormSubmitButton"] button {
        min-height:3.25rem;
        border:1.5px solid var(--ink) !important;
        border-radius:999px !important;
        background:var(--peach) !important;
        color:var(--ink) !important;
        font-weight:900 !important;
        text-transform:uppercase;
        letter-spacing:.035em;
        box-shadow:4px 4px 0 var(--ink);
        transition:transform .12s ease, box-shadow .12s ease;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        transform:translate(2px,2px);
        box-shadow:2px 2px 0 var(--ink);
    }
    [role="radiogroup"] {gap:.45rem;}
    [role="radiogroup"] label {
        border:1px solid var(--ink);
        border-radius:999px;
        padding:.35rem .75rem;
        background:#fff;
    }
    [class*="st-key-creator-card-"] {
        border:1.5px solid var(--ink) !important;
        border-radius:22px !important;
        background:#fff !important;
        box-shadow:8px 8px 0 var(--blue);
        padding:1.25rem !important;
        margin-bottom:1.35rem;
    }
    [data-testid="stMetric"] {
        background:var(--peach);
        border:1px solid var(--ink);
        border-radius:999px;
        padding:12px 15px;
        text-align:center;
    }
    [data-testid="stMetricLabel"] {justify-content:center;}
    [data-testid="stMetricValue"] {font-family:Arial Black, Arial, sans-serif; color:var(--ink);}
    [data-testid="stExpander"] {border:1px solid #7c7474; border-radius:14px; background:#fffdf9; overflow:hidden;}
    [data-testid="stExpander"] details > summary,
    [data-testid="stExpander"] details > summary:hover,
    [data-testid="stExpander"] details[open] > summary {
        background:var(--coral) !important;
        color:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
    }
    [data-testid="stExpander"] details > summary p,
    [data-testid="stExpander"] details > summary svg {
        color:var(--ink) !important;
        fill:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
    }
    .score-breakdown {
        width:100%;
        border-collapse:collapse;
        background:#fff !important;
        color:var(--ink) !important;
    }
    .score-breakdown thead th {
        background:var(--coral) !important;
        color:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
        font-weight:900 !important;
        border:1px solid var(--ink) !important;
        padding:.55rem .65rem;
        text-align:left;
    }
    .score-breakdown tbody td {
        background:#fff !important;
        color:var(--ink) !important;
        -webkit-text-fill-color:var(--ink) !important;
        border:1px solid #d8ceca !important;
        padding:.5rem .65rem;
    }
    .score-breakdown tbody td:last-child {
        text-align:right;
    }
    [class*="st-key-analytics-panel"] {
        border:1.5px solid var(--ink);
        border-radius:22px;
        padding:1.25rem;
        background:#fff;
        box-shadow:7px 7px 0 var(--pink);
        margin-bottom:1.2rem;
    }
    hr {border-color:var(--ink) !important; opacity:.25;}

    @media (max-width: 760px) {
        .block-container {margin-top:1rem; padding:4.6rem 1.15rem 2rem; border-radius:18px; box-shadow:8px 8px 0 var(--peach);}
        .hero-title {font-size:3.6rem;}
        .project-nav span {display:none;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="project-nav">
      <div>creator match intelligence</div>
      <span>Creator Decision Support</span>
    </div>
    <div class="hero-wrap">
      <div class="hero-pill">EXPLAINABLE MATCHING</div>
      <div class="hero-title">Find the right<br>creator, faster.</div>
      <div class="subtitle">Turn campaign requirements into a focused creator shortlist.
      Every recommendation is ranked with transparent data and rules, while final selection stays human-led.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_active_tags() -> list[str]:
    return available_tags()


def show_requirements(requirements: dict) -> None:
    with st.expander("Structured campaign requirements", expanded=False):
        st.json(requirements)


def show_results(results: pd.DataFrame) -> None:
    st.divider()
    st.subheader("Your creator shortlist")
    if results.empty:
        st.warning(
            "No creator met the eligibility rules and 50-point quality threshold. "
            "Try broadening the tags or changing the brand-experience requirement."
        )
        return

    st.caption(
        f"Showing {len(results)} qualified recommendation(s). The tool returns up to five rather than filling the list with weak matches."
    )
    for row in results.itertuples(index=False):
        with st.container(border=True, key=f"creator-card-{row.creator_code.lower()}"):
            heading, score = st.columns([4, 1])
            with heading:
                st.markdown(f"### MATCH {row.recommendation_rank:02d} · {row.creator_name}")
                st.caption(f"{row.creator_code} · {row.primary_category}")
            with score:
                st.metric("Match score", f"{row.match_score:.1f}")

            st.markdown("**Why recommended**")
            for reason in row.why_recommended:
                st.markdown(f"- {reason}")

            tag_text = row.matched_tags or "No requested tag match"
            brand_text = row.relevant_brands or "No verified relevant collaboration"
            st.caption(f"Matched tags: {tag_text}")
            st.caption(f"Relevant brands: {brand_text}")

            with st.expander("Score breakdown"):
                breakdown = pd.DataFrame(
                    {
                        "Component": ["Industry", "Tags", "Brand experience", "Completeness", "Risk"],
                        "Points": [
                            row.industry_points,
                            round(row.tag_points, 1),
                            row.brand_points,
                            round(row.completeness_points, 1),
                            -row.risk_penalty,
                        ],
                    }
                )
                st.markdown(
                    breakdown.to_html(
                        index=False,
                        classes="score-breakdown",
                        border=0,
                        justify="left",
                        float_format=lambda value: f"{value:.1f}",
                    ),
                    unsafe_allow_html=True,
                )


@st.cache_data
def get_analytics() -> dict[str, object]:
    return build_analytics()


def horizontal_bar_chart(
    data: pd.DataFrame,
    category: str,
    value: str,
    color: str,
    value_title: str,
    value_format: str = ".0f",
) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=8, color=color, stroke="#191616", strokeWidth=1)
        .encode(
            x=alt.X(f"{value}:Q", title=value_title, axis=alt.Axis(format=value_format)),
            y=alt.Y(f"{category}:N", title=None, sort="-x"),
            tooltip=[
                alt.Tooltip(f"{category}:N", title="Group"),
                alt.Tooltip(f"{value}:Q", title=value_title, format=value_format),
            ],
        )
        .properties(height=max(180, len(data) * 34))
        .configure_view(stroke=None)
        .configure_axis(
            labelColor="#191616",
            titleColor="#191616",
            gridColor="#eadfd9",
            domainColor="#191616",
        )
    )


def render_analytics() -> None:
    analytics = get_analytics()
    summary = analytics["summary"]

    st.subheader("Creator database analytics")
    st.caption(
        "Coverage and data-quality indicators for a 10-record synthetic sample. "
        "These figures demonstrate the workflow and are not production metrics."
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Creators", f"{summary['creator_count']}")
    metric_columns[1].metric("Avg. completeness", f"{summary['average_completeness']:.1f}/100")
    metric_columns[2].metric(
        "Verified collab coverage", f"{summary['verified_collaboration_coverage']:.0f}%"
    )
    metric_columns[3].metric("Major active risks", f"{summary['major_active_risk_count']}")

    left, right = st.columns(2)
    with left:
        with st.container(key="analytics-panel-category"):
            st.markdown("### Creator coverage by category")
            st.altair_chart(
                horizontal_bar_chart(
                    analytics["category_distribution"],
                    "primary_category",
                    "creator_count",
                    "#73cdef",
                    "Creators",
                ),
                width="stretch",
            )
    with right:
        with st.container(key="analytics-panel-tags"):
            st.markdown("### Most represented tags")
            st.altair_chart(
                horizontal_bar_chart(
                    analytics["tag_distribution"],
                    "tag_name",
                    "creator_count",
                    "#f7c28f",
                    "Creators",
                ),
                width="stretch",
            )

    left, right = st.columns(2)
    with left:
        with st.container(key="analytics-panel-collaboration"):
            st.markdown("### Verified collaboration coverage")
            st.altair_chart(
                horizontal_bar_chart(
                    analytics["collaboration_coverage"],
                    "primary_category",
                    "coverage_rate",
                    "#efb8df",
                    "Coverage",
                    ".1f",
                ),
                width="stretch",
            )
    with right:
        with st.container(key="analytics-panel-risk"):
            st.markdown("### Risk records by severity")
            st.altair_chart(
                horizontal_bar_chart(
                    analytics["risk_distribution"],
                    "severity",
                    "risk_record_count",
                    "#ef5269",
                    "Risk records",
                ),
                width="stretch",
            )

    with st.container(key="analytics-panel-missing"):
        st.markdown("### Missing-data rate")
        st.altair_chart(
            horizontal_bar_chart(
                analytics["missing_data"],
                "field",
                "missing_rate",
                "#54c7c8",
                "Missing rate (%)",
                ".1f",
            ),
            width="stretch",
        )

    categories = analytics["category_distribution"]
    smallest_category = categories.sort_values(["creator_count", "primary_category"]).iloc[0]
    top_tag = analytics["tag_distribution"].iloc[0]
    missing = analytics["missing_data"].sort_values("missing_rate", ascending=False).iloc[0]
    st.markdown("### What this sample suggests")
    st.markdown(
        f"- **Coverage gap:** {smallest_category['primary_category']} has only "
        f"{int(smallest_category['creator_count'])} creator in the sample.\n"
        f"- **Most represented tag:** {top_tag['tag_name']} appears across "
        f"{int(top_tag['creator_count'])} creators.\n"
        f"- **Data-quality priority:** {missing['field']} has the highest missing rate "
        f"at {missing['missing_rate']:.0f}%."
    )


def render_matcher() -> None:
    input_mode = st.radio(
        "Input mode",
        ["Structured inputs", "AI description"],
        horizontal=True,
        help="Structured mode works without an API key. AI mode extracts the same fields from natural language.",
    )
    requirements: dict | None = None

    if input_mode == "Structured inputs":
        with st.form("structured_campaign_form"):
            description = st.text_area(
                "Campaign / product description",
                value="A new skincare serum designed for sensitive skin.",
                height=90,
            )
            left, right = st.columns(2)
            with left:
                category = st.selectbox(
                    "Target creator category", ["Beauty", "Fashion", "Fitness", "Lifestyle", "Tech"]
                )
                tags = st.multiselect(
                    "Preferred tags",
                    get_active_tags(),
                    default=["Skincare", "Clean Beauty", "Sensitive Skin"],
                    max_selections=5,
                )
            with right:
                brand_preference = st.selectbox(
                    "Previous brand experience", ["Preferred", "Required", "Not Important"]
                )
                risk_tolerance = st.selectbox("Risk tolerance", ["Low", "Medium", "High"])
            submitted = st.form_submit_button("Find creators", type="primary", width="stretch")

        if submitted:
            requirements = {
                "product_description": description,
                "target_category": category,
                "preferred_tags": tags,
                "brand_experience_preference": brand_preference,
                "risk_tolerance": risk_tolerance,
            }
    else:
        api_ready = bool(os.getenv("OPENAI_API_KEY"))
        if api_ready:
            st.success("AI requirement extraction is configured.", icon="✓")
        else:
            st.info(
                "AI mode needs OPENAI_API_KEY. Structured mode remains fully available."
            )

        with st.form("ai_campaign_form"):
            ai_description = st.text_area(
                "Describe the campaign in natural language",
                value=(
                    "We need skincare creators for a sensitive-skin serum. Previous beauty "
                    "partnerships are preferred and there must be no major controversies."
                ),
                height=130,
            )
            ai_submitted = st.form_submit_button(
                "Parse and find creators", type="primary", width="stretch", disabled=not api_ready
            )

        if ai_submitted:
            try:
                parsed = parse_campaign_description(ai_description)
                requirements = parsed.model_dump()
            except Exception as error:
                st.error(f"Could not parse campaign requirements: {error}")

    if requirements is not None:
        show_requirements(requirements)
        try:
            recommendations = match_creators(requirements=requirements)
            show_results(recommendations)
        except Exception as error:
            st.error(f"Could not calculate recommendations: {error}")


workspace_view = st.radio(
    "Workspace view",
    ["Creator matcher", "Database analytics"],
    horizontal=True,
    label_visibility="collapsed",
    key="workspace-view",
)

if workspace_view == "Creator matcher":
    render_matcher()
else:
    render_analytics()

st.divider()
st.caption(
    "Synthetic demonstration data only · Recommendations support human review · "
    "No result should be interpreted as a claim about a real creator"
)
