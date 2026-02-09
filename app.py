# app.py
import os
import ast
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from stylist_core import generate_look, filter_dataset
from runway_director import (
    build_runway_scene,
    generate_runway_html,
    build_look_collage,
    get_available_presets,
    get_preset_description,
    parse_director_command,
)

# --------------------
# Constants
DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DATA_PATH = Path(
    os.getenv("DATA_PATH", DATA_DIR / "clothes_enriched_new_cat1_only.csv")
).expanduser()

FEEDBACK_PATH = DATA_DIR / "users_feedback.csv"

st.set_page_config(page_title="Total-Look Stylist", layout="wide")

GALLERY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,500;6..96,700&family=Space+Grotesk:wght@400;500;600&display=swap');

:root {
    --bg-0: #0b0f16;
    --bg-1: #0f1622;
    --bg-2: #141c2a;
    --surface: #121826;
    --surface-2: #0f141f;
    --ink-0: #f3f6fb;
    --ink-1: #b8c2d6;
    --ink-2: #7f8aa5;
    --edge: #1f2a3a;
    --edge-2: #253244;
    --accent: #7cc5ff;
    --accent-2: #5ef2d6;
    --accent-3: #d8e2f2;
    --glow: rgba(124, 197, 255, 0.35);
    --glow-2: rgba(94, 242, 214, 0.28);
    --shadow-soft: 0 20px 60px rgba(6, 10, 18, 0.45);
    --shadow-card: 0 14px 30px rgba(4, 8, 14, 0.45);
    --radius-xl: 28px;
    --radius-lg: 20px;
    --radius-md: 14px;
    --radius-sm: 10px;
    --font-display: 'Bodoni Moda', 'Playfair Display', serif;
    --font-ui: 'Space Grotesk', 'IBM Plex Sans', 'Noto Sans', sans-serif;
}

html, body, .stApp {
    background: radial-gradient(1200px 600px at 10% -10%, rgba(124, 197, 255, 0.18), transparent 60%),
                radial-gradient(900px 500px at 90% 0%, rgba(94, 242, 214, 0.12), transparent 58%),
                linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 45%, var(--bg-0) 100%);
    color: var(--ink-0);
    font-family: var(--font-ui);
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

div[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

.main .block-container {
    padding: 40px 64px 80px;
    max-width: 1400px;
}

h1, h2, h3, .hero-title, .scene-title {
    font-family: var(--font-display);
    color: var(--ink-0);
    letter-spacing: 0.5px;
}

div[data-testid="stTitle"] h1 {
    font-size: clamp(2.8rem, 4.5vw, 4.2rem);
    margin-bottom: 12px;
}

h2 {
    font-size: clamp(1.8rem, 2.6vw, 2.6rem);
}

h3 {
    font-size: clamp(1.3rem, 1.8vw, 1.8rem);
}

p, li, label, textarea, input, .stMarkdown {
    font-family: var(--font-ui);
}

.hero {
    padding: 26px 0 18px;
}

.hero-eyebrow {
    font-size: 12px;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: var(--ink-2);
    margin-bottom: 10px;
}

.hero-title {
    font-size: clamp(3rem, 5.4vw, 5rem);
    line-height: 1.05;
    margin-bottom: 14px;
}

.hero-subtitle {
    font-size: 1.1rem;
    line-height: 1.6;
    color: var(--ink-1);
    max-width: 560px;
}

.hero-meta {
    margin-top: 18px;
    font-size: 0.95rem;
    color: var(--ink-2);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.scene-header {
    padding: 22px 0 16px;
    border-top: 1px solid var(--edge);
}

.scene-kicker {
    font-size: 11px;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: var(--accent-2);
    margin-bottom: 10px;
}

.scene-title {
    font-size: clamp(1.8rem, 2.4vw, 2.6rem);
    margin-bottom: 8px;
}

.scene-subtitle {
    font-size: 1rem;
    color: var(--ink-1);
    max-width: 760px;
}

.scene-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--edge), transparent);
    margin: 18px 0 6px;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: rgba(16, 22, 33, 0.8);
    border: 1px solid var(--edge);
    color: var(--ink-0);
    border-radius: var(--radius-md);
    box-shadow: inset 0 0 0 1px rgba(124, 197, 255, 0.08);
}

div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(124, 197, 255, 0.2);
}

div[data-testid="stTextArea"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
    color: var(--ink-2);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-size: 0.72rem;
}

div[data-testid="stSelectbox"] > div {
    background: rgba(16, 22, 33, 0.8);
    border-radius: var(--radius-sm);
    border: 1px solid var(--edge);
}

button {
    border-radius: 999px !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

button[kind="primary"] {
    background: linear-gradient(120deg, rgba(124, 197, 255, 0.95), rgba(94, 242, 214, 0.95));
    color: #0b0f16;
    border: none;
    box-shadow: 0 12px 30px rgba(94, 242, 214, 0.25);
}

button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 36px rgba(94, 242, 214, 0.35);
}

button[kind="secondary"] {
    background: transparent;
    color: var(--ink-0);
    border: 1px solid var(--edge);
}

div[data-testid="stImage"] img {
    border-radius: var(--radius-lg);
    border: 1px solid var(--edge);
    background: var(--surface);
    box-shadow: var(--shadow-card);
}

div[data-testid="stAlert"] {
    background: rgba(16, 22, 33, 0.9);
    border: 1px solid var(--edge-2);
    color: var(--ink-0);
}

div[data-testid="stRadio"] > div {
    background: rgba(16, 22, 33, 0.8);
    border: 1px solid var(--edge);
    border-radius: var(--radius-md);
    padding: 12px 16px;
}

div[data-testid="stCaptionContainer"] {
    color: var(--ink-2);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero, .scene-header, div[data-testid="stImage"], div[data-testid="stRadio"] {
    animation: fadeUp 0.7s ease both;
}

@media (max-width: 900px) {
    .main .block-container {
        padding: 28px 22px 64px;
    }

    .hero-title {
        font-size: clamp(2.6rem, 10vw, 3.4rem);
    }
}
</style>
"""

st.markdown(GALLERY_CSS, unsafe_allow_html=True)

# --------------------
# Feedback storage
if FEEDBACK_PATH.exists():
    users_feedback = pd.read_csv(FEEDBACK_PATH)
else:
    users_feedback = pd.DataFrame(columns=["user_query", "selected_look", "comment"])

# --------------------
# Session state
if "runway_scene" not in st.session_state:
    st.session_state.runway_scene = None
if "runway_items_data" not in st.session_state:
    st.session_state.runway_items_data = []
if "generated_look" not in st.session_state:
    st.session_state.generated_look = None
if "filtered_results" not in st.session_state:
    st.session_state.filtered_results = {}
if "runway_preset" not in st.session_state:
    st.session_state.runway_preset = "gallery_night"
if "runway_scene_override" not in st.session_state:
    st.session_state.runway_scene_override = None
if "look_items_by_idx" not in st.session_state:
    st.session_state.look_items_by_idx = {}
if "look_collages" not in st.session_state:
    st.session_state.look_collages = {}


def section_header(title: str, subtitle: Optional[str] = None, kicker: Optional[str] = None) -> None:
    kicker_html = f'<div class="scene-kicker">{kicker}</div>' if kicker else ""
    subtitle_html = f'<div class="scene-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="scene-header">
            {kicker_html}
            <div class="scene-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">Gallery Night Direction</div>
        <div class="hero-title">Total-Look Stylist</div>
        <div class="hero-subtitle">
            Curate two editorial-ready looks in a single prompt. Cool light, crisp silhouettes,
            and a runway built for spotlight moments.
        </div>
        <div class="hero-meta">Cold light - Studio shadows - Two looks at a time</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def to_list(val):
    """
    Converts a list-like string into a real list.
    Leaves NaN and existing lists unchanged.
    """
    if pd.isna(val) or isinstance(val, list):
        return val
    return ast.literal_eval(val)


df_enriched = pd.read_csv(
    DEFAULT_DATA_PATH,
    converters={"category_id": to_list},
)

# Basic cleanup
if not df_enriched.empty:
    df_enriched = df_enriched.fillna("")
    df_enriched = df_enriched.drop_duplicates(["image_external_url"]).drop_duplicates(
        ["good_id", "store_id"]
    )

# --------------------
# User prompt
user_query = st.text_area(
    "Creative direction",
    "Gallery opening, cool tones, modern minimal, sculptural lines, polished footwear.",
    height=150,
)

model_choice = "zai-glm-4.7"
use_unisex_choice = True

# --------------------
# Generate
if st.button("Generate looks", type="primary"):
    with st.spinner("Consulting the stylist..."):
        look = generate_look(user_query, model=model_choice)

    st.success("Looks curated")

    with st.spinner("Sourcing the edit from the catalog..."):
        results = filter_dataset(
            df_enriched,
            look,
            max_per_item=100,
            use_unisex_choice=use_unisex_choice,
        )

    st.session_state.generated_look = look
    st.session_state.filtered_results = results

    # Build both looks and prepare runway items
    look_items_by_idx = {}
    for look_idx in (0, 1):
        selected_items = []
        for part, df_part in results.items():
            if df_part is not None and len(df_part) > look_idx:
                row = df_part.iloc[look_idx].to_dict()
                row["category"] = part
                row["look_label"] = f"Look {look_idx + 1}"
                selected_items.append(row)
        look_items_by_idx[look_idx] = selected_items

    look_collages = {}
    runway_items_data = []
    for look_idx in (0, 1):
        label = f"Look {look_idx + 1}"
        items_list = look_items_by_idx.get(look_idx, [])
        collage_data_uri = build_look_collage(items_list) if items_list else None
        look_collages[label] = collage_data_uri

        if collage_data_uri:
            runway_items_data.append(
                {
                    "name": label,
                    "category": "Look",
                    "image_data_uri": collage_data_uri,
                    "look_label": label,
                }
            )
        elif items_list:
            fallback_item = items_list[0]
            runway_items_data.append(
                {
                    "name": label,
                    "category": "Look",
                    "image_external_url": fallback_item.get("image_external_url"),
                    "look_label": label,
                }
            )
        else:
            runway_items_data.append(
                {
                    "name": label,
                    "category": "Look",
                    "look_label": label,
                }
            )

    st.session_state.runway_items_data = runway_items_data
    st.session_state.look_items_by_idx = look_items_by_idx
    st.session_state.look_collages = look_collages
    st.session_state.runway_scene_override = None
    st.session_state.runway_preset = "gallery_night"

# --------------------
# Post-generate UI
if st.session_state.runway_items_data:
    section_header(
        "Try-on Collage",
        "Two silhouettes, staged like gallery prints. Inspect proportions and palette balance.",
        kicker="Scene 01",
    )
    col_a, col_b = st.columns(2)
    for col, label in zip([col_a, col_b], ["Look 1", "Look 2"]):
        with col:
            collage = st.session_state.look_collages.get(label)
            if collage:
                st.image(collage, caption=label)
            else:
                st.caption(f"{label}: collage unavailable")

    st.markdown('<div class="scene-divider"></div>', unsafe_allow_html=True)
    section_header(
        "Director's Booth",
        "Shape the light, camera, and atmosphere with a preset or a directorial note.",
        kicker="Scene 02",
    )
    col_preset, col_director = st.columns([1, 2])

    with col_preset:
        presets = get_available_presets()
        if st.session_state.runway_preset not in presets:
            st.session_state.runway_preset = presets[0]

        selected_preset = st.selectbox(
            "Lighting preset",
            presets,
            index=presets.index(st.session_state.runway_preset),
            format_func=lambda x: f"{x.replace('_', ' ').title()}",
        )

        desc = get_preset_description(selected_preset)
        if desc:
            st.caption(desc)

        if st.button("Apply lighting", key="apply_preset"):
            st.session_state.runway_preset = selected_preset
            st.session_state.runway_scene_override = None
            st.rerun()

    with col_director:
        director_command = st.text_area(
            "Director note",
            placeholder=(
                "Examples:\n"
                "- Make it like Paris Fashion Week: minimalism, soft light\n"
                "- Now cyberpunk Tokyo, rain, neon, closer camera\n"
                "- Create a 90s editorial cover: bold typography, white background"
            ),
            height=100,
            key="director_command",
        )

        if st.button("Apply direction", key="apply_director"):
            if director_command.strip():
                with st.spinner("Director is setting the scene..."):
                    director_result = parse_director_command(
                        director_command,
                        model=model_choice,
                    )

                if director_result:
                    st.session_state.runway_scene_override = director_result
                    st.session_state.runway_preset = director_result.scene.preset
                    st.success("Scene updated!")
                else:
                    st.warning("Couldn't parse the command. Using the current preset.")

    st.markdown('<div class="scene-divider"></div>', unsafe_allow_html=True)
    section_header(
        "Runway Gallery",
        "Spotlight the looks in a darkened hall with soft fog and cool reflections.",
        kicker="Scene 03",
    )
    with st.spinner("Preparing the gallery..."):
        scene = build_runway_scene(
            items_data=st.session_state.runway_items_data,
            preset=st.session_state.runway_preset,
            cover_title="GALLERY NIGHT",
            cover_subtitle="Two looks, one spotlight",
            cover_badges=["cool light", "studio edit"],
        )

        override = st.session_state.runway_scene_override
        if override:
            scene.scene = override.scene
            scene.cover = override.cover
            scene.transitions = override.transitions

        st.session_state.runway_scene = scene

        html = generate_runway_html(scene)
        components.html(
            html,
            height=650,
            scrolling=False,
        )

    st.markdown('<div class="scene-divider"></div>', unsafe_allow_html=True)
    section_header(
        "Final Selection",
        "Pick the look that deserves the closing spotlight.",
        kicker="Scene 04",
    )
    selected = st.radio(
        "Select a winner",
        ["Look 1", "Look 2"],
        horizontal=True,
        key="look_choice",
    )
    comment = st.text_input("Notes (optional)", key="look_comment")

    if st.button("Save vote", key="save_feedback"):
        new_row = {
            "user_query": user_query,
            "selected_look": selected,
            "comment": comment,
        }
        users_feedback = pd.concat(
            [users_feedback, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        users_feedback.to_csv(FEEDBACK_PATH, index=False)
        st.success("Thanks for the feedback!")
