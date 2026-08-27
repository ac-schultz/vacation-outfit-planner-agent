# Vacation Outfit Planner

Give it a city and a date, and it suggests what to wear based on the weather
forecast (temperature, rain, wind). Uses [Open-Meteo](https://open-meteo.com)
— free, no API key needed. Forecasts only work up to ~16 days out.

## Setup

```bash
pip install requests
```

## Usage

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
