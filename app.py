# app.py
'''import debugpy

try:
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()
except RuntimeError:
    pass
'''
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import ast
import numpy as np
import streamlit.components.v1 as components
# --- ваш бизнес-код ---
from stylist_core import generate_look, filter_dataset
from runway_director import (
    build_runway_scene,
    parse_director_command,
    generate_runway_html,
    get_available_presets,
    get_preset_description,
    build_look_collage
)

# ──────────────────────────────────────────────────────────────
# Константы (можно переопределить через переменные окружения)
DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DATA_PATH = Path(
    os.getenv("DATA_PATH", DATA_DIR / "clothes_enriched_new_cat1_only.csv")
).expanduser()
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SUPPORTED_EXT = {".parquet", ".csv"}

# Путь для хранения отзывов
FEEDBACK_PATH = DATA_DIR / "users_feedback.csv"

# Загружаем существующие отзывы или создаем новый DataFrame
if FEEDBACK_PATH.exists():
    users_feedback = pd.read_csv(FEEDBACK_PATH)
else:
    users_feedback = pd.DataFrame(columns=["user_query", "selected_look", "comment"])
# ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Fashion Look Finder", layout="wide")

# Initialize session state for runway mode
if 'runway_scene' not in st.session_state:
    st.session_state.runway_scene = None
if 'selected_look_items' not in st.session_state:
    st.session_state.selected_look_items = []
if 'selected_look_items_by_look' not in st.session_state:
    st.session_state.selected_look_items_by_look = {}
if 'runway_preset' not in st.session_state:
    st.session_state.runway_preset = "minimal"
if 'generated_look' not in st.session_state:
    st.session_state.generated_look = None
if 'filtered_results' not in st.session_state:
    st.session_state.filtered_results = {}
if 'runway_autoswitch' not in st.session_state:
    st.session_state.runway_autoswitch = False

# Create tabs
tab1, tab2 = st.tabs(["Look Generator", "Runway Director"])

if st.session_state.runway_autoswitch:
    components.html(
        """
        <script>
        const tabs = window.parent.document.querySelectorAll('button[role="tab"]');
        if (tabs && tabs.length > 1) {
            tabs[1].click();
        }
        </script>
        """,
        height=0,
        width=0,
    )
    st.session_state.runway_autoswitch = False

with tab1:
    st.title("Total-Look Stylist")

def to_list(val):
    """
    Преобразует строку-представление списка в настоящий список.
    Оставляет без изменений NaN и уже готовые списки.
    """
    if pd.isna(val) or isinstance(val, list):
        return val
    return ast.literal_eval(val)   # безопасный eval для литералов

df_enriched = pd.read_csv(
    DEFAULT_DATA_PATH,
    converters={'category_id': to_list}
)
df_enriched = df_enriched.fillna("")

df_enriched = df_enriched.drop_duplicates(['image_external_url']).drop_duplicates(['good_id', 'store_id'])
#df_enriched = df_enriched[~df_enriched.image_external_url.str.contains('//imocean.ru/')]

# --- ввод запроса пользователя ---
user_query = st.text_area(
    "Describe the look (any free text)",
    "I need a look for a graduation in soft pastel tones, summer, feminine.",
    height=120,
)


model_choice = st.sidebar.selectbox(
    "LLM model", ["zai-glm-4.7"], index=0
)
use_unisex_choice = st.sidebar.selectbox(
    "Allow unisex items in the look?", [ "Allow", "Do not allow"], index=0
)
use_unisex_choice = True if use_unisex_choice == "Allow" else False

# --- обработка запроса ---
if st.button("Generate look"):
    with st.spinner("Asking the AI stylist..."):
        look = generate_look(user_query, model=model_choice)

    st.success("Look generated")

    # --- dataset filtering ---
    with st.spinner("Selecting items from the catalog..."):
        results = filter_dataset(df_enriched, look, max_per_item=100, use_unisex_choice=use_unisex_choice)

    st.session_state.generated_look = look
    st.session_state.filtered_results = results

# --- selected look ---
if st.session_state.generated_look:
    results = st.session_state.filtered_results or {}

    # --- visualize top-2 looks ---
    st.markdown("### Top-2 total looks")
    col1, col2 = st.columns(2)

    def show_look(col, idx):
        with col:
            st.write(f"#### Look {idx+1}")
            for part, df_part in results.items():
                if df_part is not None and len(df_part) > idx:
                    row = df_part.iloc[idx]
                    url = row.get('image_external_url')
                    name = row.get('name', part)
                    if url:
                        st.image(url, caption=f"{part}: {name}")

    show_look(col1, 0)
    show_look(col2, 1)

    st.markdown("### Choose the look you like")
    selected = st.radio(
        "Which look do you prefer?",
        ["Look 1", "Look 2"],
        horizontal=True,
        key="look_choice",
    )
    comment = st.text_input("Comment", key="look_comment")

    col_save, col_runway = st.columns(2)
    with col_save:
        if st.button("Save feedback", key="save_feedback"):
            new_row = {
                "user_query": user_query,
                "selected_look": selected,
                "comment": comment,
            }
            users_feedback = pd.concat(
                [users_feedback, pd.DataFrame([new_row])], ignore_index=True
            )
            users_feedback.to_csv(FEEDBACK_PATH, index=False)
            st.success("Thanks for the feedback!")

    with col_runway:
        if st.button("Show on runway", key="go_to_runway"):
            # Store both looks for runway + collage
            look_items_by_idx = {}
            for look_idx in (0, 1):
                selected_items = []
                for part, df_part in results.items():
                    if df_part is not None and len(df_part) > look_idx:
                        row = df_part.iloc[look_idx].to_dict()
                        row['category'] = part
                        row['look_label'] = f"Look {look_idx + 1}"
                        selected_items.append(row)
                look_items_by_idx[look_idx] = selected_items

            st.session_state.selected_look_items = (
                look_items_by_idx.get(0, []) + look_items_by_idx.get(1, [])
            )
            st.session_state.selected_look_items_by_look = {
                "Look 1": look_items_by_idx.get(0, []),
                "Look 2": look_items_by_idx.get(1, []),
            }
            st.session_state.runway_autoswitch = True
            st.success("Looks saved! Switching to Runway Director...")
            st.rerun()
# Runway Director Tab
with tab2:
    st.title("AI Runway Director")
    st.markdown("""
    Turn the selected look into a cinematic runway show.
    Control lighting, camera, and atmosphere with text commands.
    """)
    
    # Check if we have items to display
    if not st.session_state.selected_look_items:
        st.info("First generate a look in the Look Generator tab and pick your favorite option.")
    else:
        # Scene preset selection
        st.subheader("Scene settings")
        
        col_preset, col_director = st.columns([1, 2])
        
        with col_preset:
            st.write("**Choose a preset:**")
            presets = get_available_presets()
            selected_preset = st.selectbox(
                "Scene style",
                presets,
                index=presets.index(st.session_state.runway_preset),
                format_func=lambda x: f"{x.replace('_', ' ').title()}"
            )
            
            # Show preset description
            desc = get_preset_description(selected_preset)
            if desc:
                st.caption(desc)
            
            if st.button("Apply preset", key="apply_preset"):
                st.session_state.runway_preset = selected_preset
                st.rerun()
        
        with col_director:
            st.write("**Director command:**")
            director_command = st.text_area(
                "Describe how the show should look",
                placeholder='Examples:\n- "Make it like Paris Fashion Week: minimalism, soft light"\n- "Now cyberpunk Tokyo, rain, neon, closer camera"\n- "Create a 90s editorial cover: bold typography, white background"',
                height=100,
                key="director_command"
            )
            
            if st.button("Apply command", key="apply_director"):
                if director_command.strip():
                    with st.spinner("Director is setting the scene..."):
                        # Parse director command
                        director_result = parse_director_command(
                            director_command,
                            model=model_choice
                        )
                        
                        if director_result:
                            # Update scene with director command
                            if st.session_state.runway_scene:
                                st.session_state.runway_scene.scene = director_result.scene
                                st.session_state.runway_scene.cover = director_result.cover
                                st.session_state.runway_scene.transitions = director_result.transitions
                            st.success("Scene updated!")
                        else:
                            st.warning("Couldn't parse the command. Using the current preset.")
        
        # Build and display runway scene
        st.subheader("Runway")
        
        with st.spinner("Preparing the scene..."):
            # Build runway scene
            scene = build_runway_scene(
                items_data=st.session_state.selected_look_items,
                preset=st.session_state.runway_preset,
                cover_title="VOGUE",
                cover_subtitle="Collection 2026",
                cover_badges=["Total Look", "AI Styled"]
            )
            
            st.session_state.runway_scene = scene

            # Build visual collage (mannequin try-on)
            if st.session_state.selected_look_items_by_look:
                st.subheader("Try-on Collage")
                col_a, col_b = st.columns(2)
                for col, (label, items_list) in zip(
                    [col_a, col_b],
                    st.session_state.selected_look_items_by_look.items()
                ):
                    with col:
                        collage_data_uri = build_look_collage(items_list)
                        if collage_data_uri:
                            st.image(collage_data_uri, caption=label)
            
            # Generate HTML
            html = generate_runway_html(scene)
            
            # Display runway
            components.html(
                html,
                height=650,
                scrolling=False
            )
        
        # Scene info
        st.subheader("Scene info")
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("Theme", scene.scene.theme)
        with col_info2:
            st.metric("Lighting", scene.scene.lighting)
        with col_info3:
            st.metric("Atmosphere", scene.scene.atmosphere)
        
        # Cover info
        st.write("**Cover:**")
        st.write(f"- Title: {scene.cover.title}")
        st.write(f"- Subtitle: {scene.cover.subtitle}")
        if scene.cover.badges:
            st.write(f"- Badges: {', '.join(scene.cover.badges)}")
        
        # Items info
        st.write(f"**Items on the runway:** {len(scene.items)}")
        for item in scene.items:
            st.write(f"- {item.category}: {item.name}")
