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
    get_preset_description
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
if 'runway_preset' not in st.session_state:
    st.session_state.runway_preset = "minimal"

# Create tabs
tab1, tab2 = st.tabs(["👗 Look Generator", "🎬 Runway Director"])

with tab1:
    st.title("👗 Total-Look Stylist")

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
    "Опишите образ (любой свободный текст)",
    "Мне нужен образ на выпускной в нежных пастельных тонах, лето, женский.",
    height=120,
)


model_choice = st.sidebar.selectbox(
    "LLM-модель", ["zai-glm-4.7"], index=0
)
use_unisex_choice = st.sidebar.selectbox(
    "Можно ли использовать в образе вещи, помеченные как Unisex?", [ "Можно", "Не использовать"], index=0
)
use_unisex_choice = True if use_unisex_choice == "Можно" else False

# --- обработка запроса ---
if st.button("Сгенерировать лук"):
    with st.spinner("Запрашиваем стилиста-ИИ…"):
        look = generate_look(user_query, model=model_choice)

    st.success("Образ сгенерирован")
    st.write("### Структура полученного лука")
    st.json(look.model_dump(), expanded=False)

    
    # --- фильтрация датасета ---
    with st.spinner("Подбираем вещи из каталога…"):
        results = filter_dataset(df_enriched, look, max_per_item=100, use_unisex_choice=use_unisex_choice)

    # --- вывод таблиц ---
    for part, df_part in results.items():
        if df_part.empty:
            st.write(f"_{part}: подходящих вещей не найдено_")
        else:
            st.subheader(part.capitalize())
            st.dataframe(df_part, use_container_width=True)

    # --- визуализация top-2 луков ---
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
    
    st.markdown("### Выберите понравившийся образ")
    selected = st.radio(
        "Какой образ вам нравится больше?",
        ["Look 1", "Look 2"],
        horizontal=True,
        key="look_choice",
    )
    comment = st.text_input("Комментарий", key="look_comment")
    
    col_save, col_runway = st.columns(2)
    with col_save:
        if st.button("Сохранить отзыв", key="save_feedback"):
            new_row = {
                "user_query": user_query,
                "selected_look": selected,
                "comment": comment,
            }
            users_feedback = pd.concat(
                [users_feedback, pd.DataFrame([new_row])], ignore_index=True
            )
            users_feedback.to_csv(FEEDBACK_PATH, index=False)
            st.success("Спасибо за отзыв!")
    
    with col_runway:
        if st.button("🎬 Показать на подиуме", key="go_to_runway"):
            # Store selected look items for runway
            selected_idx = 0 if selected == "Look 1" else 1
            selected_items = []
            for part, df_part in results.items():
                if df_part is not None and len(df_part) > selected_idx:
                    row = df_part.iloc[selected_idx].to_dict()
                    row['category'] = part
                    selected_items.append(row)
            
            st.session_state.selected_look_items = selected_items
            st.success("Образ сохранён! Перейдите на вкладку Runway Director")

# Runway Director Tab
with tab2:
    st.title("🎬 AI Runway Director")
    st.markdown("""
    Превратите выбранный образ в кинематографичное шоу на подиуме. 
    Управляйте светом, камерой и атмосферой с помощью текстовых команд.
    """)
    
    # Check if we have items to display
    if not st.session_state.selected_look_items:
        st.info("👈 Сначала сгенерируйте образ на вкладке Look Generator и выберите понравившийся вариант")
    else:
        # Scene preset selection
        st.subheader("🎨 Настройки сцены")
        
        col_preset, col_director = st.columns([1, 2])
        
        with col_preset:
            st.write("**Выберите пресет:**")
            presets = get_available_presets()
            selected_preset = st.selectbox(
                "Стиль сцены",
                presets,
                index=presets.index(st.session_state.runway_preset),
                format_func=lambda x: f"{x.replace('_', ' ').title()}"
            )
            
            # Show preset description
            desc = get_preset_description(selected_preset)
            if desc:
                st.caption(desc)
            
            if st.button("Применить пресет", key="apply_preset"):
                st.session_state.runway_preset = selected_preset
                st.rerun()
        
        with col_director:
            st.write("**Режиссёрская команда:**")
            director_command = st.text_area(
                "Опишите, как должен выглядеть показ",
                placeholder='Примеры:\n- "Сделай показ как Paris Fashion Week, минимализм, мягкий свет"\n- "Теперь cyberpunk Tokyo, дождь, неон, камера ближе"\n- "Сделай редакционную обложку 90s: крупный шрифт, белый фон"',
                height=100,
                key="director_command"
            )
            
            if st.button("🎬 Применить команду", key="apply_director"):
                if director_command.strip():
                    with st.spinner("Режиссёр настраивает сцену..."):
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
                            st.success("✨ Сцена обновлена!")
                        else:
                            st.warning("Не удалось распознать команду. Используется текущий пресет.")
        
        # Build and display runway scene
        st.subheader("🌟 Подиум")
        
        with st.spinner("Подготовка сцены..."):
            # Build runway scene
            scene = build_runway_scene(
                items_data=st.session_state.selected_look_items,
                preset=st.session_state.runway_preset,
                cover_title="VOGUE",
                cover_subtitle="Collection 2026",
                cover_badges=["Total Look", "AI Styled"]
            )
            
            st.session_state.runway_scene = scene
            
            # Generate HTML
            html = generate_runway_html(scene)
            
            # Display runway
            components.html(
                html,
                height=650,
                scrolling=False
            )
        
        # Scene info
        st.subheader("📋 Информация о сцене")
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("Тема", scene.scene.theme)
        with col_info2:
            st.metric("Освещение", scene.scene.lighting)
        with col_info3:
            st.metric("Атмосфера", scene.scene.atmosphere)
        
        # Cover info
        st.write("**Обложка:**")
        st.write(f"- Заголовок: {scene.cover.title}")
        st.write(f"- Подзаголовок: {scene.cover.subtitle}")
        if scene.cover.badges:
            st.write(f"- Бейджи: {', '.join(scene.cover.badges)}")
        
        # Items info
        st.write(f"**Товары на подиуме:** {len(scene.items)}")
        for item in scene.items:
            st.write(f"- {item.category}: {item.name}")
