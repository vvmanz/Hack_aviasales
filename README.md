# Hack_aviasales

**Flight-search and price-history prototype with a Streamlit UI, Flask API and SQLite database.**

English | [Русский](README.ru.md)

This hackathon-style application helps compare outbound and return flight combinations for a selected trip. A Flask backend queries the bundled SQLite database, while the Streamlit frontend displays available options and visualizes historical ticket prices. A separate script contains an experimental Amadeus API import workflow.

## Features

- **Trip search** by origin, destination, departure date and trip duration.
- **Outbound + return combinations** sorted by total price and waiting time.
- **Interactive Streamlit frontend** with ticket-price charts (Plotly).
- **Price-history visualization and illustrative forecasting** using interpolation / an adjustment coefficient.
- **SQLite data storage** and separate scripts for import from external flight data.

> **What the forecast means:** the original project notes describe an interpolation-based projection of stored price observations; this is **not** a validated machine-learning fare prediction model. Results depend on the age and completeness of the historical records.

## Requirements

- Python 3.10+ recommended.
- `flask`, `streamlit`, `requests`, `pandas`, `scipy`, `plotly`, `mplcursors` and Matplotlib (the latter may be installed as a transitive dependency, but can be installed explicitly).
- The supplied `AirTickets.db` file in the project root.

There is no pinned `requirements.txt` in this snapshot.

## Quick start

Install packages in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
python -m pip install flask streamlit requests pandas scipy plotly mplcursors matplotlib
```

Open two terminals **from the repository root**. Terminal 1:

```bash
python main.py
```

Terminal 2:

```bash
streamlit run streamlit_front.py
```

The Flask server runs locally (by default at `http://127.0.0.1:5000`), and Streamlit opens its interface in the browser. The frontend requests the API at `http://localhost:5000`.

## How it works

```text
Streamlit UI (streamlit_front.py)
        │ HTTP requests
        ▼
Flask (main.py)
        │ /api/flights, /api/price_forecast
        ▼
SQLite (AirTickets.db)
        ▲
        └── optional data preparation / Amadeus import scripts
```

| Endpoint | Purpose |
|---|---|
| `GET /api/flights` | Flight combinations matching cities, departure date and business-trip duration |
| `GET /api/price_forecast` | Stored `(departure date, price)` points for the route |

## Repository layout

```text
main.py                     Flask API and SQL queries
streamlit_front.py          browser interface and charts
AirTickets.db               sample SQLite flight database
amadeus_api.py              Amadeus API experiment / CSV preparation
sqlite_import_from_api.py   CSV-to-SQLite import helper
readme.txt                  original project overview
Инструкция к запуску.txt   original short startup guide
*.mp4                       demonstration videos
```

See the MP4 files in the repository for recordings of the prototype.
