from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME", "mydb"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "port": os.getenv("DB_PORT", "5432"),
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Hello world"}


@app.get("/data")
def get_data() -> List[Dict[str, Any]]:
    """
    Execute a query to PostgreSQL and return data as JSON.

    Returns:
        List of dictionaries containing the query results.
    """
    conn = None
    cursor = None

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Example query - modify this based on your actual table structure
        # This query will list all tables in the database as a demonstration
        query = """
            SELECT DISTINCT ON (cst) *
            FROM air_quality_clean
            ORDER BY cst;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Convert to list of dictionaries
        data = [dict(row) for row in results]

        return data

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    finally:
        # Clean up database resources
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
