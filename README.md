# Vacation Outfit Planner

Give it a city and a date, and it suggests what to wear based on the weather
forecast (temperature, rain, wind). Uses [Open-Meteo](https://open-meteo.com)
— free, no API key needed. Forecasts only work up to ~16 days out.

## Setup

```bash
pip install requests streamlit
```

## Web interface

```bash
streamlit run streamlit_app.py
```

Opens a form in your browser: city, arrival date, an "arriving midday or
late?" checkbox, departure date, and a "pack light?" checkbox (tighter
reuse ratio for pants/shirts). Submitting shows a color-coded forecast +
outfit suggestion for each day of the trip, plus a packing checklist at
the end.

## Command line

Same logic, run from the terminal instead.

### Usage

Single day:

```bash
python outfit_planner.py "Lisbon" 2026-09-10
```

Whole trip — add an end date and it gives you a single paragraph summarizing
the trip (temperature, rain risk, what to wear), plus a packing line at the
end (shirts, pants, underwear, socks, and rain/warm gear if needed):

```bash
python outfit_planner.py "Tokyo" 2026-08-24 through 2026-08-30
```

If it's your arrival day and you're landing midday or in the evening, add
`--arrival` to get travel-friendly layers instead of a full outfit change
(only applies to the first day):

```bash
python outfit_planner.py "Lisbon" 2026-09-10 --arrival midday
python outfit_planner.py "Tokyo" 2026-08-24 through 2026-08-30 --arrival midday
```
