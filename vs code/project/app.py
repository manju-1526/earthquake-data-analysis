import streamlit as st
import pandas as pd
import pymysql 
from sqlalchemy import create_engine, URL

st.title("🌍 Earthquake Data Analysis Dashboard")

st.write("Streamlit is working successfully!")


connection_url = URL.create(
    "mysql+pymysql",
    username=st.secrets["mysql"]["user"],
    password=st.secrets["mysql"]["password"],
    host=st.secrets["mysql"]["host"],
    port=st.secrets["mysql"]["port"],
    database=st.secrets["mysql"]["database"]
)

engine = create_engine(connection_url)
# Last 5 years data 
query = """ SELECT * FROM EQ WHERE time >= DATE_SUB(NOW(), INTERVAL 5 YEAR) 
ORDER BY time DESC """
try:
    df = pd.read_sql(query, engine)

    # Magnitude Filter
    st.sidebar.header("🎛️ Filters")

    min_magnitude = st.sidebar.slider(
        "Minimum Magnitude",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1
   )

    df = df[df["mag"] >= min_magnitude]

    st.subheader("🌍 Last 5 Years Earthquake Data")
   
    # KPI Metrics
    total_earthquakes = len(df)
    max_magnitude = df["mag"].max()
    avg_magnitude = df["mag"].mean()
    tsunami_events = df["tsunami"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🌍 Total Earthquakes", total_earthquakes)
    col2.metric("📈 Highest Magnitude", round(max_magnitude, 2))
    col3.metric("📊 Average Magnitude", round(avg_magnitude, 2))
    col4.metric("🌊 Tsunami Events", tsunami_events)

    # Year-wise Earthquake Trend
    df["year"] = df["time"].dt.year

    # Year Filter
    st.sidebar.header("📅 Year Filter")

    available_years = sorted(df["year"].unique(), reverse=True)

    selected_year = st.sidebar.selectbox(
        "Select Year",
        ["All"] + available_years
   )

    if selected_year != "All":
        df = df[df["year"] == selected_year]

    # Location Filter
    st.sidebar.header("📍 Location Filter")

    locations = sorted(df["place"].dropna().unique())

    selected_location = st.sidebar.selectbox(
        "Select Location",
        ["All"] + locations
    )

    if selected_location != "All":
         df = df[df["place"] == selected_location]

    yearly_data = df.groupby("year").size().reset_index(name="earthquake_count")

    st.subheader("📈 Year-wise Earthquake Trend")

    st.line_chart(
        yearly_data.set_index("year")["earthquake_count"]
    )

     # Magnitude Distribution
    st.subheader("📊 Magnitude Distribution")

    magnitude_data = df["mag"].dropna()

    st.bar_chart(
        magnitude_data.value_counts().sort_index()
    )

     # Top 10 Highest Magnitude Earthquakes
    st.subheader("🔥 Top 10 Highest Magnitude Earthquakes")

    top_10 = df.nlargest(10, "mag")[
        ["time", "mag", "place", "depth_km"]
    ]

     # Earthquake Depth Analysis
    st.subheader("🌍 Earthquake Depth Analysis")

    depth_data = df["depth_km"].dropna()

    st.line_chart(depth_data)

    # Tsunami Analysis
    st.subheader("🌊 Tsunami Events Analysis")

    tsunami_data = df["tsunami"].value_counts()

    st.bar_chart(tsunami_data)

    # Monthly Earthquake Trend
    st.subheader("📅 Monthly Earthquake Trend")

    df["month"] = df["time"].dt.to_period("M").astype(str)

    monthly_data = df.groupby("month").size().reset_index(name="earthquake_count")

    st.line_chart(
         monthly_data.set_index("month")["earthquake_count"]
    )

    # Magnitude vs Depth Analysis
    st.subheader("📊 Magnitude vs Depth Analysis")

    magnitude_depth = df[["mag", "depth_km"]].dropna()

    st.scatter_chart(
        magnitude_depth,
        x="depth_km",
        y="mag"
   )

    # Earthquake by Hour Analysis
    st.subheader("🕐 Earthquake by Hour")

    df["hour"] = df["time"].dt.hour

    hourly_data = df.groupby("hour").size().reset_index(name="earthquake_count")

    st.bar_chart(
         hourly_data.set_index("hour")["earthquake_count"]
    )

    # Alert Level Analysis
    st.subheader("🚨 Earthquake Alert Level Analysis")

    alert_data = df["alert"].fillna("Unknown").value_counts()

    st.bar_chart(alert_data)

    # 🌍 World Map
    st.subheader("🗺️ Earthquake World Map")

    map_data = df[["latitude", "longitude"]].dropna()

    st.map(
       map_data,
       latitude="latitude",
       longitude="longitude"
   )

    # 💡 Key Insights
    st.subheader("💡 Key Insights")

    highest_magnitude = df["mag"].max()
    average_magnitude = df["mag"].mean()
    total_earthquakes = len(df)
    tsunami_events = df["tsunami"].sum()

    most_active_year = df["year"].value_counts().idxmax()

    st.write(f"🔥 Highest Magnitude: {highest_magnitude:.2f}")
    st.write(f"📊 Average Magnitude: {average_magnitude:.2f}")
    st.write(f"🌍 Total Earthquakes: {total_earthquakes}")
    st.write(f"🌊 Tsunami Events: {tsunami_events}")
    st.write(f"📅 Most Active Year: {most_active_year}")

    st.dataframe(df, use_container_width=True)

    # Download CSV
    csv = df.to_csv(index=False)

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="earthquake_data.csv",
        mime="text/csv"
   )
    st.bar_chart(
        top_10.set_index("place")["mag"]
    )

except Exception as e:
    st.error(f"Data loading failed: {e}")