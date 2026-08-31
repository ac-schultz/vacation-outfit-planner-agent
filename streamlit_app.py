"""
Vacation Outfit Planner — web interface
-----------------------------------------
A thin Streamlit front end over outfit_planner.py. It reuses that module's
logic functions unmodified (geocode_city, get_forecast_range,
classify_conditions, suggest_outfit, build_packing_list) — this file only
handles the form, input validation, and rendering.

Run with:
    streamlit run streamlit_app.py
"""

from datetime import date, timedelta

import streamlit as st

from outfit_planner import (
    MAX_FORECAST_DAYS,
    build_packing_list,
    classify_conditions,
    geocode_city,
    get_forecast_range,
    suggest_outfit,
)

def format_display_date(d):
    """date object or 'YYYY-MM-DD' string -> 'September 01, 2026'."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%B %d, %Y")


def weather_emoji(conditions):
    """Pick an emoji from the same rain/temp buckets classify_conditions already computed."""
    if conditions["rain"] == "likely":
        return "🌧️"
    if conditions["rain"] == "possible":
        return "🌦️"
    if conditions["temp_band"] == "hot":
        return "☀️"
    if conditions["temp_band"] in ("cold", "cool"):
        return "❄️"
    return "⛅"


TEMP_BAND_COLORS = {
    "cold": ("#DCEBFF", "#3E6FA6"),
    "cool": ("#EAF3FF", "#6FA0D6"),
    "mild": ("#FFF9E6", "#D9B84A"),
    "warm": ("#FFE9D6", "#D9822B"),
    "hot": ("#FFDCC2", "#D94A29"),
}


st.set_page_config(page_title="Vacation Outfit Planner", page_icon="🧳")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&display=swap');

    .stApp {
        background: linear-gradient(100deg, #FFF6B7 0%, #FFD9E8 55%, #FFAEEB 100%);
    }

    h1, h2, h3, [data-testid="stHeading"] {
        font-family: 'Bricolage Grotesque', sans-serif !important;
        font-weight: 800 !important;
        color: #1a1a1a !important;
    }

    [data-testid="stCaptionContainer"] {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.75);
        border-radius: 12px;
        padding: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧳 Vacation Outfit Planner")
st.caption("Tell us where and when you're headed — we'll check the forecast and tell you what to pack.")

with st.form("trip_form"):
    city = st.text_input("City")
    arrival_date = st.date_input(
        "Arrival Date",
        value=date.today(),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=MAX_FORECAST_DAYS),
    )
    arriving_midday = st.checkbox("Arriving midday or late?")
    departure_date = st.date_input(
        "Departure Date",
        value=date.today(),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=MAX_FORECAST_DAYS),
    )
    pack_light = st.checkbox("Pack light?")
    submitted = st.form_submit_button("Plan my outfits")

if submitted:
    if not city.strip():
        st.error("Please enter a city.")
        st.stop()

    if departure_date < arrival_date:
        st.error("Departure date can't be before the arrival date.")
        st.stop()

    arrival = "midday" if arriving_midday else None

    try:
        lat, lon, place = geocode_city(city)
        daily_forecasts = get_forecast_range(lat, lon, arrival_date.isoformat(), departure_date.isoformat())
    except SystemExit as e:
        st.error(str(e.code))
        st.stop()

    all_conditions = [classify_conditions(f) for f in daily_forecasts]

    st.header(place)
    st.write(f"{format_display_date(arrival_date)} to {format_display_date(departure_date)}")

    for i, forecast in enumerate(daily_forecasts):
        conditions = all_conditions[i]
        day_arrival = arrival if i == 0 else None
        outfit = suggest_outfit(conditions, arrival=day_arrival)
        bg_color, border_color = TEMP_BAND_COLORS[conditions["temp_band"]]

        # Built as one unindented line, deliberately — st.markdown runs a markdown
        # parser before allowing raw HTML through, and a multi-line indented block
        # (especially with a blank line where arrival_line was empty) gets treated
        # as a markdown code fence instead of HTML.
        card_html = (
            f'<div style="background:{bg_color};border-left:5px solid {border_color};'
            f'border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;">'
            f'<h3 style="margin:0 0 0.4em 0;">Day {i + 1} - {format_display_date(forecast["date"])}</h3>'
            f'<p style="margin:0 0 0.3em 0;">{weather_emoji(conditions)} Forecast: '
            f'{forecast["temp_min"]:.0f}–{forecast["temp_max"]:.0f}°C, '
            f'{forecast["rain_chance"]:.0f}% chance of rain, '
            f'wind up to {forecast["wind_max"]:.0f} km/h</p>'
            + (f'<p style="margin:0 0 0.3em 0;">Arrival: {day_arrival}</p>' if day_arrival else "")
            + f'<p style="margin:0;">Suggestion: {outfit}</p>'
            + "</div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)

    packing_list = build_packing_list(all_conditions, pack_light=pack_light)
    st.subheader("Packing list")
    for item, count in packing_list.items():
        st.markdown(f"- {count} {item}")
