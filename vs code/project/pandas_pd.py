# %%
import requests
import pandas as pd
from datetime import datetime
import sqlalchemy as sqlalchemy
from sqlalchemy import create_engine

# %%
url = "https://earthquake.usgs.gov/fdsnws/event/1/query"


# %%
start_year = datetime.now().year - 5 # last 5 years
end_year = datetime.now().year

# %%
all_records = []
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": 3
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"failed for{start_date}: {response.text[:200]}")
            continue
        try:
            data = response.json()
        except Exception as e:
            print(f"JSON error for {start_date}:{e}")
            continue

        for f in data["features"]: 
            p = f["properties"] 
            g = f["geometry"]["coordinates"]
            all_records.append({
                "id": f.get("id"),
                "time": p.get("time"),
                "updated": p.get("updated"),
                "latitude": g[1], 
                "longitude": g[0], 
                "depth_km": g[2],
                "mag": p.get("mag"),
                "magType": p.get("magType"),
                "place": p.get("place"),
                "status": p.get("status"),
                "tsunami": p.get("tsunami"),
                "alert": p.get("alert"),
                "felt": p.get("felt"),
                "cdi": p.get("cdi"),
                "mmi": p.get("mmi"),
                "sig": p.get("sig"),
                "net": p.get("net"),
                "code": p.get("code"),
                "ids": p.get("ids"),
                "sources": p.get("sources"),
                "types": p.get("types"),
                "nst": p.get("nst"),
                "dmin": p.get("dmin"),
                "rms": p.get("rms"),
                "gap": p.get("gap"),
                "type": p.get("type")
            })
df = pd.DataFrame(all_records)



# %%
#check data
df.head()

# %%
# shape
df.shape

# %%
# info
df.info()

# %%
# columns
df.columns

# %%
# duplicated
df.duplicated().sum()

# %%
# isnull
df.isnull().sum()

# %%
# convert datetime
df["time"] = pd.to_datetime(df["time"], unit="ms", errors = "coerce")
df["updated"] = pd.to_datetime(df["updated"], unit="ms", errors = "coerce")

# %%
# clean alert
if "alert" in df.columns:
    df["alert"] = (df["alert"].astype("string").str.lower().str.strip())

# %%
# clean string columns
string_columns = [
    "magType", 
    "status", 
    "type", 
    "net", 
    "sources", 
    "types"
]
for col in string_columns:
    if col in df.columns:
        df[col] = (df[col].astype("string").str.strip())

# %%
# Convert numeric columns
numeric_columns = [
    "mag",
    "depth_km",
    "nst",
    "dmin",
    "rms",
    "gap",
    "magError",
    "depthError",
    "magNst",
    "sig"
]
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(0)

# %%
# Add derived date columns
df["year"] = df["time"].dt.year
df["month"] = df["time"].dt.month
df["day"] = df["time"].dt.day
df["day_of_week"] = df["time"].dt.day_name()

# %%
# Shallow / Deep
depth_category = []

for x in df["depth_km"]:
    if x < 50:
        depth_category.append("shallow")
    else:
        depth_category.append("deep")

df["depth_category"] = depth_category


# %%
# Strong / Normal
strength_category = []

for x in df["mag"]:
    if x >= 7.0:
        strength_category.append("strong")
    else:
        strength_category.append("normal")

df["strength_category"] = strength_category

# %%
import pymysql


# %%
try:
    connection = pymysql.connect(
        host = "localhost",
        user = "root",
        password = "Guvi123",
        port = 3306,
        database = "project",
        )
    cursor = connection.cursor()
    print("connected to MySQL successfully!")
except Exception as e:
    print("connection failed:", e)

engine = create_engine("mysql+pymysql://root:Guvi123@localhost:3306/project")
with engine.connect() as conn:
    print("SQLAlchemy connected successfully!")

# %%
# insert df into sql
df.to_sql(
    name = "EQ",
    con = engine,
    if_exists="replace",
    index = False
)
print("Data inserted successfully!")

# %%
# SQL query
queries = {"1.Top 10 strongest earthquakes (mag)": """
              SELECT * FROM EQ ORDER BY mag DESC LIMIT 10
           """,
           "2. Top 10 deepest earthquakes (depth_km)": """
               SELECT * FROM EQ ORDER BY depth_km DESC LIMIT 10
           """,
           "3. Shallow earthquakes < 50 km and mag > 7.5": """
               SELECT * FROM EQ WHERE depth_km < 50 AND mag > 7.5
           """,
           "5. Average magnitude per magnitude type (magType)": """
               SELECT magType, AVG(mag) AS average_magnitude FROM EQ GROUP BY magType
           """,
           "6. Year with most earthquakes": """
               SELECT year, COUNT(*)as total 
               FROM EQ GROUP BY year 
               ORDER BY total DESC LIMIT 1
           """,
           "7. Month with highest number of earthquakes": """
               SELECT month, COUNT(*)as total 
               FROM EQ GROUP BY month 
               ORDER BY total DESC LIMIT 1
           """,
           "8. Day of week with most earthquakes":"""
               SELECT day_of_week, COUNT(*) AS total 
               FROM EQ GROUP BY day_of_week 
               ORDER BY total DESC LIMIT 1
           """,
           "9. Count of earthquakes per hour of day":"""
               SELECT time, COUNT(*) AS total
               FROM EQ GROUP BY time ORDER BY total
           """,
           "10. Most active reporting network (net)":"""
                SELECT net, COUNT(*) AS total 
                FROM EQ GROUP BY net
                ORDER BY total DESC LIMIT 1
           """,
           "11. Top 5 places with highest casualties":"""
                SELECT place, max(felt) as casualties 
                FROM EQ GROUP BY place 
                ORDER BY casualties DESC LIMIT 5
           """,
           "13. Average economic loss by alert level":"""
                SELECT alert, COUNT(*) as count 
                FROM EQ GROUP BY alert
           """,
           "14. Count of reviewed vs automatic earthquakes (status)":"""
                SELECT status, COUNT(*) as total 
                FROM EQ GROUP BY status
           """,
           "15. Count by earthquake type (type)":"""
                SELECT type, COUNT(*) as total 
                FROM EQ GROUP BY type
           """,
           "16. Number of earthquakes by data type (types)":"""
                SELECT types, count(*) as total_earthquakes
                FROM EQ GROUP BY types
           """,
           "18. Events with high station coverage (nst > threshold)":"""
                SELECT * FROM EQ WHERE nst > 50 ORDER BY nst DESC
           """,
           "19. Number of tsunamis triggered per year":"""
                SELECT year, COUNT(*) as total_tsunamis FROM EQ
                WHERE tsunamis = 1 GROUP BY year
           """,
           "20. Earthquakes by alert levels (red, orange, etc.)":"""
                SELECT alert, count(*) as earthquake_count 
                FROM EQ GROUP BY alert
           """,
           "21. Top 5 countries with the highest average magnitude (past 5 years)":"""
                SELECT place, AVG(mag) as avg_mag 
                FROM EQ GROUP BY place 
                ORDER BY avg_mag DESC LIMIT 5
           """,
           "22. countries with both shallow and deep earthquakes same month":"""
                SELECT place, year, month FROM EQ 
                GROUP BY place, year, month 
                HAVING SUM(depth_category = 'shallow') > 0 AND SUM(depth_category = 'deep') > 0
           """,
           "23. Year-over-year growth rate in the total number of earthquakes globally":"""
                SELECT year, total, lag(total) over (order by year) as previous_year,
                ROUND(((total - lag(total) over (order by year)) / 
                lag(total) over (order by year)) * 100, 2) as growth_rate
                FROM(SELECT year, COUNT(*) as total FROM EQ
                GROUP BY year) as yearly
           """,
           "24. Top 3 most seismically active region":"""
                SELECT place, COUNT(*) AS earthquake_frequency,
                AVG(mag) AS average_mag, (COUNT(*) * AVG(mag)) AS score
                FROM EQ GROUP BY place ORDER BY score DESC LIMIT 3
           """,
           "25. Average depth within ±5° of equato":"""
                SELECT place, AVG(depth_km) AS average_depth_km
                FROM EQ WHERE latitude BETWEEN -5 AND 5
                GROUP BY place
           """,
           "26. Countries with highest shallow to deep ratio":"""
                SELECT place, 
                SUM(depth_km < 70) as shallow,
                SUM(depth_km > 300) as deep,
                SUM(depth_km < 70) / NULLIF(SUM(depth_km > 300),0) as ratio 
                FROM EQ GROUP BY place ORDER BY ratio DESC
           """,
           "27. Average magnitude difference (tsunami and non-tsunami)":"""
                SELECT
               (SELECT AVG(mag) FROM EQ WHERE tsunami = 1) as tsunami_avg,
               (SELECT AVG(mag) FROM EQ WHERE tsunami = 0) as no_tsunami_avg,
               (SELECT AVG(mag) FROM EQ WHERE tsunami = 1) -
               (SELECT AVG(mag) FROM EQ WHERE tsunami = 0) as difference
           """,
           "28. Event with lowest data reliability (gap & rms)":"""
                SELECT * FROM EQ ORDER BY gap DESC, rms DESC LIMIT 10
           """,
           "30. Regions with the highest deep-focus EQ(>300 km)":"""
                SELECT place, COUNT(*) as deep_frequency
                FROM EQ WHERE depth_km > 300 GROUP BY place
                ORDER BY deep_frequency
           """
}


# %%
import streamlit as st
import pandas as pd
# streamlit
st.title("🌍Earthquake Data Analysis Dashboard")
st.write("select any problem statement (1-30) to run the corresponding SQL query.")

# Dropdown
task = st.selectbox("choose task number", list(queries.keys()))

# Run button
if st.button ("Run Query"):
    query = queries[task]
    df = pd.read_sql(query, engine)

    st.subheader(f"Results for: {task}")
    st.dataframe(df, use_container_width=True)


