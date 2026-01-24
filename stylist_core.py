# stylist_core.py
from __future__ import annotations
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import pandas as pd

import openai
import prompts
from prompts import OneTotalLook, Item
from pydantic import parse_obj_as



# ---------- LLM call ----------
def generate_look(user_text: str, model: str = "gpt-4.1-mini") -> OneTotalLook:
    """
    Запрашивает LLM и возвращает структурированный OneTotalLook.
    Ключ API можно передать напрямую или через переменную окружения OPENAI_API_KEY.
    """
    
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": prompts.TOTAL_CREATIONLOOK_PROMPT.format(request=user_text)},
    ]

    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        temperature=0.0,
        max_completion_tokens=1000,
        response_format=OneTotalLook,
    )

    # .parse() возвращает специальный объект, сама модель в .choices[0].message.parsed
    look = response.choices[0].message.parsed
    look = parse_obj_as(OneTotalLook, look)
    return look


# ---------- DF utilities ----------
def match_item(df: pd.DataFrame, itm: Item) -> pd.DataFrame:
    """
    Оставляет строки c совпадением по category_id[0] и (необязательно) другим признакам.
    Раскомментируйте фильтры, как только заполните соответствующие столбцы датасета.
    """
    df_f = df[df["category_id"].str[0] == itm.category]
    df_2 = df[df["name"].str.contains(itm.category)]
    df_f = pd.concat([df_f, df_2])

    if itm.color:  #and df_f.shape[0] >=4:
        df_c = df_f[df_f["color"].str.contains(itm.color)]
        df_2 = df_f[df_f["name"].str.contains(itm.color)]
        df_c = pd.concat([df_c, df_2])
        df_c.drop_duplicates(['image_external_url'], inplace=True)
        if df_c.shape[0] >=2:
            if itm.fabric: 
                df_ff = df_c[df_c["name"].str.contains(itm.fabric)]
                df_ff.drop_duplicates(['image_external_url'], inplace=True)
                if df_ff.shape[0] >=2:
                    if itm.pattern:
                        df_p = df_ff[df_ff["name"].str.contains(itm.pattern)]
                        df_p.drop_duplicates(['image_external_url'], inplace=True)
                        if df_p.shape[0] >=2:
                            if itm.detailes:
                                df_detailes = df_ff[df_ff["detailes"] == itm.detailes]
                                df_detailes.drop_duplicates(['image_external_url'], inplace=True)
                                if df_detailes.shape[0] >=2:
                                    return df_detailes
                                else:
                                    return df_p
                        else:
                            return df_ff
                    else:
                        return df_ff
                else:
                    return df_c
            else: 
                return df_c
        else:
            return df_f
    else:
        return df_f



def filter_dataset(
    df: pd.DataFrame,
    look: OneTotalLook,
    max_per_item: int = 1,
    use_unisex_choice: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Возвращает словарь { '<part>_<category>_<idx>': DataFrame }.
    """

    # 1️⃣ базовый срез по полу
    if look.sex and use_unisex_choice:
        df_base = df[df["gender"].str.lower().isin({"unisex", look.sex.lower()})]
    elif look.sex:
        df_base = df[df["gender"].str.lower().isin({look.sex})]
    else:
        df_base = df.copy()

    results: Dict[str, pd.DataFrame] = {}

    # 2️⃣ обходим все поля модели, кроме служебных
    for part_name in (f for f in OneTotalLook.model_fields if f not in {"sex", "season"}):
        items = getattr(look, part_name)
        if not items:                      # None или пустой список
            continue

        # 3️⃣ обрабатываем каждый Item отдельно
        for idx, itm in enumerate(items):
            if not isinstance(itm, Item):              # на всякий случай
                itm = Item.model_validate(itm)

            sub = match_item(df_base, itm)
            if sub is not None and not sub.empty:
                key = f"{part_name}_{itm.category}_{idx}"
                results[key] = sub.head(max_per_item)

    return results



'''
def filter_dataset(df: pd.DataFrame, look: OneTotalLook,
                   max_per_item: int = 1) -> Dict[str, pd.DataFrame]:
    """
    Возвращает словарь {part: dataframe} с подходящими позициями.
    """

    if look.sex:
        df_base = df[df["gender"].str.lower() == "unisex"]
        df_sex = df[df["gender"].str.lower() == look.sex.lower()]
        df_base = pd.concat([df_base, df_sex])

    parts = ['top', 'bottom', 'full', 'shoes', 'outerwear', 'accessories']
    results: Dict[str, pd.DataFrame] = {}

    for part in parts:
        items = getattr(look, part) or []
        selections = []
        for itm in items:
            sub = match_item(df_base, itm)
            if sub is not None and not sub.empty:
                selections.append(sub.head(max_per_item))
        results[part] = pd.concat(selections) if selections else pd.DataFrame()

    return results
'''