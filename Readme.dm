# 👗 Fashion Stylist — Streamlit App

LLM-powered demo that generates a complete **total look** from natural-language
requirements and immediately searches your product catalog for matching items.

---

## Features
* GPT-4o (or any GPT-4.x) parses the user brief into a structured `OneTotalLook`.
* Pandas filters your enriched catalog (`df_enriched.parquet`) to suggest
  concrete SKUs for every part of the outfit.
* One-click Streamlit UI, fully containerised.

---

## Getting started

### 1. Clone & prepare data

```bash
git clone https://github.com/you/fashion-stylist.git
cd fashion-stylist
# Put your df_enriched.parquet (or CSV) in ./data
mkdir data
mv /path/to/clothes_enriched.csv data/

#Build
docker build -t fashion-stylist:latest .

#Run
docker run --rm -d -p 8510:8510/tcp fashion-stylist:latest 

#Run with special df:
docker run --rm \
  -p 8510:8510 \
  -v "$(pwd)/data/clothes_enriched.csv":/data/clothes_enriched.csv \
  fashion-stylist:latest
Open http://localhost:8501 and start styling!