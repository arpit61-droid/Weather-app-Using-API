import streamlit as st
import requests
from datetime import datetime

# 1. Page Configuration
# st.set_page_config(
#     page_title="Weather Dashboard",
#     page_icon="🌍",
#     layout="centered"
# )

st.set_page_config(
    page_title="Weather App",
    page_icon="⛅",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "⛅ Weather App — Real-time forecasts powered by OpenWeatherMap"
    }
)

# 2. API Key Configuration
API_KEY = "Your api key here"  # Replace with your actual OpenWeatherMap API key

# 3. Air Quality Index Category Definitions
AQI_MAPPING = {
    1: {"label": "🟢 Good", "color": "#2ECC71", "desc": "Air quality is satisfactory; minimal or no risk."},
    2: {"label": "🟡 Fair", "color": "#F1C40F", "desc": "Acceptable quality; minor moderate health concern for some."},
    3: {"label": "🟠 Moderate", "color": "#E67E22", "desc": "Sensitive groups may experience health effects."},
    4: {"label": "🔴 Poor", "color": "#E74C3C", "desc": "Everyone may begin to experience health impacts."},
    5: {"label": "💀 Very Poor", "color": "#9B59B6", "desc": "Health warning: emergency conditions likely."}
}

# 4. App Header UI
st.title("🌍 Real-Time Weather Dashboard")
st.markdown("Query synchronized global meteorological grids for real-time telemetry and forecasts.")
st.divider()

# 5. Input Field
city = st.text_input("Enter City Name", placeholder="e.g., London, New York, Tokyo, Mumbai")

if st.button("Analyze Location Data", use_container_width=True):
    if not city.strip():
        st.warning("Please type a city name first!")
    else:
        with st.spinner(f"Querying planetary weather grid for '{city}'..."):
            # --- PHASE 1: Fetch Current Weather to acquire Geo-Coordinates (Lat/Lon) ---
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            
            try:
                current_response = requests.get(current_url)
                current_data = current_response.json()
                
                if current_data.get("cod") == 200:
                    lat = current_data["coord"]["lat"]
                    lon = current_data["coord"]["lon"]
                    city_name = current_data["name"]
                    country = current_data["sys"]["country"]
                    
                    # --- PHASE 2: Query Air Pollution API via Geo-Coordinates ---
                    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
                    aqi_data = requests.get(aqi_url).json()
                    raw_aqi = aqi_data["list"][0]["main"]["aqi"]
                    aqi_info = AQI_MAPPING.get(raw_aqi, {"label": "Unknown", "color": "#7F8C8D", "desc": "N/A"})
                    
                    # --- PHASE 3: Query 5-Day / 3-Hour Forecast Engine ---
                    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
                    forecast_data = requests.get(forecast_url).json()
                    
                    st.success(f"Telemetry acquired successfully for {city_name}, {country} [Lat: {lat}, Lon: {lon}]")
                    
                    # ==========================================
                    # MONITOR LAYER 1: CURRENT STATE & AQI CARD
                    # ==========================================
                    col_metrics, col_aqi_card = st.columns([2, 1])
                    
                    with col_metrics:
                        st.markdown("### 📊 Live Meteorological Telemetry")
                        m_col1, m_col2, m_col3 = st.columns(3)
                        m_col1.metric("Temperature", f"{current_data['main']['temp']}°C", f"Feels like {current_data['main']['feels_like']}°C")
                        m_col2.metric("Humidity", f"{current_data['main']['humidity']}%")
                        m_col3.metric("Wind Velocity", f"{current_data['wind']['speed']} m/s")
                        
                    with col_aqi_card:
                        st.markdown("### 🍃 Atmospheric Quality")
                        st.markdown(
                            f"""
                            <div style="padding:18px; border-radius:10px; border-left: 8px solid {aqi_info['color']}; background-color:#1E2622; height:100%;">
                                <h4 style="margin:0; color:#A0A0A0; font-size:0.9rem; text-transform:uppercase;">Air Quality Index</h4>
                                <h2 style="margin:5px 0; color:{aqi_info['color']}; font-weight:bold;">{aqi_info['label']}</h2>
                                <p style="margin:0; font-size:0.85rem; color:#E0E0E0; line-height:1.3;">{aqi_info['desc']}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    st.divider()
                    
                    # ==========================================
                    # MONITOR LAYER 2: HOURLY TIMELINE (NEXT 24 HOURS)
                    # ==========================================
                    st.markdown("### ⏰ 24-Hour Timeline Breakdown (3-Hour Increments)")
                    hourly_intervals = forecast_data["list"][:8]  # 8 points * 3 hours = 24 hours
                    
                    h_cols = st.columns(8)
                    for idx, segment in enumerate(hourly_intervals):
                        time_obj = datetime.fromtimestamp(segment["dt"])
                        formatted_hour = time_obj.strftime("%I:%M %p")
                        seg_temp = segment["main"]["temp"]
                        seg_icon = segment["weather"][0]["icon"]
                        seg_condition = segment["weather"][0]["main"]
                        
                        with h_cols[idx]:
                            st.markdown(f"<div style='text-align:center; font-weight:600; color:#CAD7CE;'>{formatted_hour}</div>", unsafe_allow_html=True)
                            st.image(f"http://openweathermap.org/img/wn/{seg_icon}.png", use_container_width=True)
                            st.markdown(f"<div style='text-align:center; font-size:1.2rem; font-weight:700;'>{seg_temp:.1f}°C</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='text-align:center; font-size:0.8rem; color:#8A9A90;'>{seg_condition}</div>", unsafe_allow_html=True)
                            
                    st.divider()
                    
                    # ==========================================
                    # MONITOR LAYER 3: 5-DAY EXTENDED FORECAST
                    # ==========================================
                    st.markdown("### 📅 5-Day Extended Structural Outlook")
                    
                    # Extract midday metrics (12:00 PM UTC) to represent the daily macro snapshot safely
                    midday_forecasts = [item for item in forecast_data["list"] if "12:00:00" in item["dt_txt"]]
                    
                    # Fallback validation check
                    if not midday_forecasts:
                        midday_forecasts = forecast_data["list"][::8]
                        
                    d_cols = st.columns(len(midday_forecasts))
                    for idx, day_data in enumerate(midday_forecasts):
                        day_obj = datetime.fromtimestamp(day_data["dt"])
                        day_title = day_obj.strftime("%A")
                        date_sub = day_obj.strftime("%b %d")
                        max_t = day_data["main"]["temp_max"]
                        min_t = day_data["main"]["temp_min"]
                        day_icon = day_data["weather"][0]["icon"]
                        day_desc = day_data["weather"][0]["description"].title()
                        
                        with d_cols[idx]:
                            st.markdown(
                                f"""
                                <div style="background-color:#151F1B; padding:15px; border-radius:10px; text-align:center; border: 1px solid #23332D;">
                                    <div style="font-weight:700; color:#52B788; font-size:1.1rem;">{day_title}</div>
                                    <div style="color:#6C7A72; font-size:0.85rem; margin-bottom:5px;">{date_sub}</div>
                                    <img src="http://openweathermap.org/img/wn/{day_icon}@2x.png" width="75" style="margin:0 auto; display:block;"/>
                                    <div style="font-size:1.3rem; font-weight:800; margin-top:5px; color:#FFFFFF;">{max_t:.1f}°C</div>
                                    <div style="color:#8A9A90; font-size:0.85rem;">Min: {min_t:.1f}°C</div>
                                    <div style="font-size:0.8srem; color:#A3B19B; margin-top:8px; font-style:italic; min-height:35px; display:flex; align-items:center; justify-content:center;">{day_desc}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                            
                elif current_data.get("cod") == "404":
                    st.error(f"Geographic target '{city}' not recognized on OpenWeather grids.")
                else:
                    st.error(f"API Error Panel: {current_data.get('message')}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Telemetry stream interrupted: {e}")
