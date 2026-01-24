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
# --- ваш бизнес-код ---
from stylist_core import generate_look, filter_dataset

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
    "LLM-модель", [ "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1"], index=0
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