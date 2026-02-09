# app.py
import os
import ast
from pathlib import Path

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

st.set_page_config(page_title="Fashion Look Finder", layout="wide")

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
    st.session_state.runway_preset = "minimal"
if "runway_scene_override" not in st.session_state:
    st.session_state.runway_scene_override = None
if "look_items_by_idx" not in st.session_state:
    st.session_state.look_items_by_idx = {}
if "look_collages" not in st.session_state:
    st.session_state.look_collages = {}


st.title("Total-Look Stylist")


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
    "Describe the look (any free text)",
    "I need a look for a graduation in soft pastel tones, summer, feminine.",
    height=120,
)

model_choice = "zai-glm-4.7"
use_unisex_choice = True

# --------------------
# Generate
if st.button("Generate look"):
    with st.spinner("Asking the AI stylist..."):
        look = generate_look(user_query, model=model_choice)

    st.success("Looks generated")

    with st.spinner("Selecting items from the catalog..."):
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
    st.session_state.runway_preset = "minimal"

# --------------------
# Post-generate UI
if st.session_state.runway_items_data:
    st.markdown(
        """
        Turn the selected look into a cinematic runway show.
        Control lighting, camera, and atmosphere with text commands.
        """
    )

    st.subheader("Try-on Collage")
    col_a, col_b = st.columns(2)
    for col, label in zip([col_a, col_b], ["Look 1", "Look 2"]):
        with col:
            collage = st.session_state.look_collages.get(label)
            if collage:
                st.image(collage, caption=label)
            else:
                st.caption(f"{label}: collage unavailable")

    st.subheader("Scene settings")
    col_preset, col_director = st.columns([1, 2])

    with col_preset:
        presets = get_available_presets()
        if st.session_state.runway_preset not in presets:
            st.session_state.runway_preset = presets[0]

        selected_preset = st.selectbox(
            "Scene style",
            presets,
            index=presets.index(st.session_state.runway_preset),
            format_func=lambda x: f"{x.replace('_', ' ').title()}",
        )

        desc = get_preset_description(selected_preset)
        if desc:
            st.caption(desc)

        if st.button("Apply preset", key="apply_preset"):
            st.session_state.runway_preset = selected_preset
            st.session_state.runway_scene_override = None
            st.rerun()

    with col_director:
        director_command = st.text_area(
            "Director command",
            placeholder=(
                "Examples:\n"
                "- Make it like Paris Fashion Week: minimalism, soft light\n"
                "- Now cyberpunk Tokyo, rain, neon, closer camera\n"
                "- Create a 90s editorial cover: bold typography, white background"
            ),
            height=100,
            key="director_command",
        )

        if st.button("Apply command", key="apply_director"):
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

    st.subheader("Runway")
    with st.spinner("Preparing the scene..."):
        scene = build_runway_scene(
            items_data=st.session_state.runway_items_data,
            preset=st.session_state.runway_preset,
            cover_title="Runway",
            cover_subtitle="Try on your new outfit",
            cover_badges=[],
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

    st.subheader("Choose the look you like")
    selected = st.radio(
        "Which look do you prefer?",
        ["Look 1", "Look 2"],
        horizontal=True,
        key="look_choice",
    )
    comment = st.text_input("Comment", key="look_comment")

    if st.button("Save feedback", key="save_feedback"):
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
