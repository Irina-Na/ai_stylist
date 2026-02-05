# Fashion Stylist - Streamlit App

LLM-powered demo that generates a complete total look from natural-language
requirements and searches your product catalog for matching items.

## Features
- LLM parses the user brief into a structured `OneTotalLook`.
- Pandas filters the catalog to suggest concrete SKUs for each outfit part.
- Streamlit UI with a "Runway Director" mode for cinematic presentation.

## Requirements
- Python 3.11+
- A Cerebras API key (`API_KEY_CEREBRAS` or `CEREBRAS_API_KEY`)
- A catalog file in CSV or Parquet format

## Quick start (local)
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Set your API key (or put it in `.env`):
   ```bash
   setx API_KEY_CEREBRAS "your_key_here"
   ```
   For the current session only (PowerShell):
   ```bash
   $env:API_KEY_CEREBRAS="your_key_here"
   ```
3. Place your catalog file in `data/` and, if needed, point the app to it:
   ```bash
   setx DATA_PATH "C:\path\to\your_catalog.csv"
   ```
4. Run the app:
   ```bash
   streamlit run app.py --server.port 8510
   ```
5. Open `http://localhost:8510`.

## Docker
Build and run:
```bash
docker build -t fashion-stylist:latest .

# Option A: pass env vars directly
docker run --rm -p 8510:8510 `
  -e API_KEY_CEREBRAS=your_key_here `
  fashion-stylist:latest

# Option B (recommended): load secrets from .env (not baked into image)
docker run --rm -p 8510:8510 --env-file .env fashion-stylist:latest

# Using your own catalog file:
docker run --rm -p 8510:8510 --env-file .env `
  -e DATA_PATH=/app/data/catalog.csv `
  -v "$PWD\\data\\catalog.csv":/app/data/catalog.csv `
  fashion-stylist:latest
```
Open `http://localhost:8510`.

### Docker Compose
If you prefer compose (recommended), edit `docker-compose.yml` (DATA_PATH + volume) and run:
```bash
docker compose up --build
```
Open `http://localhost:8510`.

## Data format
The app expects a catalog with columns used by the filter logic, such as:
`category_id`, `name`, `color`, `gender`, `image_external_url`, `good_id`,
`store_id`, and (optionally) `detailes`. If your schema differs, update
`match_item()` in `stylist_core.py`.
