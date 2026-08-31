# Vacation Outfit Planner — Build Summary

A condensed record of how this project came together, for future reference.

## What it is

A Python tool (CLI + web) that takes a city and date(s), pulls a real weather
forecast from [Open-Meteo](https://open-meteo.com) (free, no API key), and
suggests what to pack/wear — with special handling for travel days.

Two files:
- **`outfit_planner.py`** — all core logic + CLI. No third-party framework, just `requests`.
- **`streamlit_app.py`** — a web front end over the same logic, via `streamlit`.

## Build timeline

1. **Single-day CLI** — `python outfit_planner.py "City" YYYY-MM-DD [--arrival midday|evening]`. Geocodes the city, fetches the forecast, buckets conditions (temp band / rain / wind), and prints one outfit suggestion. Arrival day gets travel-friendly layers instead of a full outfit if arriving midday/evening.

2. **Multi-day trips** — added an optional end date (`"City" START through END`), a shared `get_forecast_range` API call, and a packing list (`build_packing_list`) with a reuse ratio for pants (1 per 3 days) rather than 1-per-day.

3. **Output format iteration** — went through several shapes for multi-day output (per-day blocks → "Day X of N" headers → a single narrative paragraph) before landing on the narrative-paragraph version for the CLI specifically. This was reverted once and rebuilt per direct feedback.

4. **Connected to GitHub** — private repo at `github.com/ac-schultz/vacation-outfit-planner-agent`. No `gh` CLI or Homebrew on this machine, so it was set up with plain `git` + a Personal Access Token (entered by the user in their own terminal, since credential entry isn't something Claude does).

5. **Streamlit web interface** — built as a separate presentation layer reusing the CLI's core functions (`geocode_city`, `get_forecast_range`, `classify_conditions`, `suggest_outfit`, `build_packing_list`) unmodified. Form: City, Arrival Date, "Arriving midday or late?" checkbox, Departure Date, submit. Results: **per-day breakdown** (not the CLI's paragraph style — confirmed explicitly, since the two diverged). Also handled a real gotcha: several core functions call `sys.exit()` on bad input, which would kill the whole Streamlit server if uncaught — wrapped in `try/except SystemExit` instead of changing the functions.

6. **Visual styling** — pastel yellow→pink gradient background, bold "Bricolage Grotesque" Google Font on headers, tracked-caps tagline, spelled-out dates ("September 01, 2026"), and a weather emoji per day based on actual conditions — inspired by a shared brand mockup.

7. **Two real bugs found via live testing, both fixed**:
   - `MAX_FORECAST_DAYS` was `16`, but Open-Meteo's actual limit is 15 days out — confirmed directly against the API's own error message.
   - Precipitation data (and reportedly other fields) can come back `null` right at the edge of Open-Meteo's forecast window. Rather than patching every field defensively, pulled the boundary back to **14 days** so the app never requests that unreliable edge day, plus a defensive `rain_chance or 0` fallback in `classify_conditions`.

8. **Latest features**:
   - **Day counters** — "Day 1 - September 10, 2026" style headers.
   - **Temperature color coding** — each day's block is a styled card tinted by temp band (blues for cold/cool, cream for mild, oranges for warm/hot).
   - **"Pack light?" toggle** — extends `build_packing_list(daily_conditions, pack_light=False)` with looser ratios (shirts 1-per-2-days, pants 1-per-5-days) when checked. Default `False` keeps the CLI's output identical.
   - Along the way, fixed a subtle Streamlit bug: building the colored HTML cards as an indented multi-line f-string caused markdown to treat a blank-line-adjacent indented line as a code block, so "Suggestion: ..." rendered as literal `<p>` tags instead of styled text. Fixed by building each card as one unindented line.

9. **Committed and pushed** to GitHub (`668d859`), covering the Streamlit app, both bug fixes, and doc updates.

## Key design decisions

- **Packing math**: shirts/underwear/socks = 1 per day by default; pants reuse every 3 days (5 in "pack light" mode); shirts reuse every 2 days in "pack light" mode. Rain jacket/umbrella and an extra warm layer are added once each, only if any day in the trip needs them.
- **Arrival handling**: `--arrival midday` or `evening` only overrides the *first* day's suggestion with travel-friendly layers; every other day gets the normal full-outfit suggestion.
- **Streamlit stays a thin layer**: all real logic lives in `outfit_planner.py` and is reused, not duplicated, by the web app.

## Running it

```bash
# CLI
python3 outfit_planner.py "Tokyo" 2026-09-01 through 2026-09-07 --arrival midday

# Web
pip install requests streamlit
streamlit run streamlit_app.py
```

See [README.md](README.md) for full usage.
