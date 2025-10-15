import quantaq
from quantaq.utils import to_dataframe
import pandas as pd
import time
import logging
import os

# import signal
import psycopg2

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger("qapi_cronjob")
logger.setLevel(logging.DEBUG)

# ---------------------------
# Graceful Shutdown
# ---------------------------
running = True

QAPI_KEY = os.getenv("QAPI_KEY", None)


# ---------------------------
# Fetch Data from QuantAQ API
# ---------------------------
def fetch_api_data():
    logger.info("Fetching data from API")
    client = quantaq.QuantAQAPIClient(api_key=QAPI_KEY)
    data = client.data.list(sn="MOD-00086", limit=10, sort="timestamp,desc")
    for d in data:
        print(d["timestamp"])
    return [data[0]]


# ---------------------------
# Clean Data Function
# ---------------------------
def clean_data(raw_data):
    try:
        dataframe = to_dataframe(raw_data)

        # Drop unnecessary columns
        dataframe.drop(
            columns={
                "sn",
                "url",
                "model.gas.co",
                "model.gas.co2",
                "model.gas.no",
                "model.gas.no2",
                "model.gas.o3",
                "model.pm.pm1",
                "model.pm.pm10",
                "model.pm.pm25",
                "timestamp",
                "geo.lat",
                "geo.lon",
                "met.rh",
                "met.temp",
                "met.ws",
                "met.wd",
                "raw_data_id",
                "co2",
                "no",
                "pm1",
                "ws_scalar",
                "met.ws_scalar",
            },
            inplace=True,
            errors="ignore",
        )

        # Rename columns for readability
        dataframe.rename(
            columns={
                "co": "Carbon Monoxide",
                "no2": "Nitrogen Dioxide",
                "o3": "Ozone",
                "pm10": "Particulate Matter 10",
                "pm25": "Particulate Matter 2.5",
                "rh": "Relative Humidity",
                "temp": "Temperature",
                "timestamp_local": "CST",
                "wd": "Wind Direction",
                "ws": "Wind Speed",
            },
            inplace=True,
        )

        # Unit conversions
        dataframe["Carbon Monoxide"] = dataframe["Carbon Monoxide"].apply(
            lambda x: x / 1000 if pd.notnull(x) else x
        )
        dataframe["Ozone"] = dataframe["Ozone"].apply(
            lambda x: x / 1000 if pd.notnull(x) else x
        )

        # Rounding
        dataframe = dataframe.round(
            {
                "Carbon Monoxide": 1,
                "Nitrogen Dioxide": 0,
                "Ozone": 3,
                "Particulate Matter 10": 0,
                "Particulate Matter 2.5": 1,
            }
        )

        # Convert timestamps to proper timezone string
        if "CST" in dataframe.columns:
            dataframe["CST"] = pd.to_datetime(dataframe["CST"], errors="coerce")
            dataframe["CST"] = dataframe["CST"].astype(str)

        logger.info("Data cleaned successfully")
        return dataframe.to_dict(orient="records")

    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        return []


# ---------------------------
# Create PostgreSQL Table
# ---------------------------
def create_table_if_not_exists():
    logger.info("Creating database")
    conn = psycopg2.connect(
        dbname="mydb",
        user="postgres",
        password="password",  # <-- update this
        host="postgres",
        port="5432",
    )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS air_quality_clean (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        cst TIMESTAMPTZ,
                        carbon_monoxide REAL,
                        nitrogen_dioxide REAL,
                        ozone REAL,
                        particulate_matter_10 REAL,
                        particulate_matter_2_5 REAL,
                        relative_humidity REAL,
                        temperature REAL,
                        wind_direction REAL,
                        wind_speed REAL
                    );
                """)
        logger.info("Ensured table air_quality_clean exists")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
    finally:
        conn.close()


# ---------------------------
# Insert Clean Data as Columns
# ---------------------------
def save_clean_to_postgres(cleaned_data):
    conn = psycopg2.connect(
        dbname="mydb",
        user="postgres",
        password="password",  # <-- update this
        host="postgres",
        port="5432",
    )
    try:
        with conn:
            with conn.cursor() as cur:
                for row in cleaned_data:
                    cur.execute(
                        """
                        INSERT INTO air_quality_clean (
                            cst,
                            carbon_monoxide,
                            nitrogen_dioxide,
                            ozone,
                            particulate_matter_10,
                            particulate_matter_2_5,
                            relative_humidity,
                            temperature,
                            wind_direction,
                            wind_speed
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        [
                            row.get("CST"),
                            row.get("Carbon Monoxide"),
                            row.get("Nitrogen Dioxide"),
                            row.get("Ozone"),
                            row.get("Particulate Matter 10"),
                            row.get("Particulate Matter 2.5"),
                            row.get("Relative Humidity"),
                            row.get("Temperature"),
                            row.get("Wind Direction"),
                            row.get("Wind Speed"),
                        ],
                    )
        logger.info("Inserted cleaned data into PostgreSQL successfully")
    except Exception as e:
        logger.error(f"Error inserting cleaned data: {e}")
    finally:
        conn.close()


# ---------------------------
# Main Loop (Runs Every Minute)
# ---------------------------
if __name__ == "__main__":
    create_table_if_not_exists()

    while running:
        try:
            raw_data = fetch_api_data()
            cleaned_data = clean_data(raw_data)
            if cleaned_data:
                save_clean_to_postgres(cleaned_data)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")

        logger.info("Sleeping for 60 seconds...")
        time.sleep(60)
