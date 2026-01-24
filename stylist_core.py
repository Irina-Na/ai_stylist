# stylist_core.py
from __future__ import annotations
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import pandas as pd

import openai
import cerebras.cloud.sdk as cerebras
import prompts
from prompts import OneTotalLook, Item
from pydantic import parse_obj_as



# ---------- helpers ----------
def _get_cerebras_api_key() -> Optional[str]:
    return os.getenv("API_KEY_CEREBRAS") or os.getenv("CEREBRAS_API_KEY")

def _extract_message_content(response, attempt: int) -> str:
    if not response or not getattr(response, "choices", None):
        raise ValueError(f"API returned no choices (attempt {attempt})")
    message = response.choices[0].message
    if not message:
        raise ValueError(f"API returned no message (attempt {attempt})")
    content = message.content
    if content is None:
        raise ValueError(f"API returned None content (attempt {attempt})")
    if not isinstance(content, str):
        content = str(content)
    content = content.strip()
    if not content:
        raise ValueError(f"API returned empty content (attempt {attempt})")
    return content

# ---------- LLM call ----------
def generate_look(user_text: str, model: str = "zai-glm-4.7", max_retries: int = 2) -> OneTotalLook:
    """
    Запрашивает LLM и возвращает структурированный OneTotalLook.
    Использует Cerebras API.
    """
    
    load_dotenv()

    api_key = _get_cerebras_api_key()
    if not api_key:
        raise ValueError("API_KEY_CEREBRAS/CEREBRAS_API_KEY not found in environment variables")
    
    client = cerebras.Cerebras(api_key=api_key)
    
    messages = [
        {"role": "system", "content": prompts.TOTAL_CREATIONLOOK_PROMPT.format(request=user_text)},
    ]

    import json
    
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_tokens=1000,
            )

            content = _extract_message_content(response, attempt + 1)
            
            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            look_dict = json.loads(content)
            look = OneTotalLook(**look_dict)
            return look
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying...")
                continue
            else:
                # Fallback to a default look
                print("All retries failed, using fallback look")
                return _get_fallback_look(user_text)
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying...")
                continue
            else:
                # Fallback to a default look
                print("All retries failed, using fallback look")
                return _get_fallback_look(user_text)


def _get_fallback_look(user_text: str) -> OneTotalLook:
    """
    Returns a fallback OneTotalLook when API fails.
    """
    return OneTotalLook(
        sex="unisex",
        top=["shirt"],
        bottom=["pants"],
        shoes=["sneakers"],
        full=[],
        bag=[],
        outerwear=[],
        accessories=[]
    )


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


def _normalize_items(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def filter_dataset(
    df: pd.DataFrame,
    look: OneTotalLook,
    max_per_item: int = 1,
    use_unisex_choice: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Returns { '<part>_<category>_<idx>': DataFrame }.
    """

    sex_value = (look.sex or "").strip().lower()
    if sex_value in {"f", "female"}:
        sex_value = "female"
    elif sex_value in {"m", "male"}:
        sex_value = "male"
    elif sex_value in {"u", "unisex"}:
        sex_value = "unisex"

    if sex_value and use_unisex_choice:
        df_base = df[df["gender"].str.lower().isin({"unisex", sex_value})]
    elif sex_value:
        df_base = df[df["gender"].str.lower().isin({sex_value})]
    else:
        df_base = df.copy()

    results: Dict[str, pd.DataFrame] = {}
    part_fields = ("top", "bottom", "full", "shoes", "bag", "outerwear", "accessories")

    for part_name in part_fields:
        items = _normalize_items(getattr(look, part_name, None))
        if not items:
            continue

        for idx, itm in enumerate(items):
            if isinstance(itm, str):
                if not itm.strip():
                    continue
                itm = Item(category=itm)
            elif not isinstance(itm, Item):
                itm = Item.model_validate(itm)

            if not itm.category:
                continue

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
