from sqlalchemy import create_engine, text
from app.config import settings

# Change this line:
DATABASE_URL = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

SCHEMA_DEFINITION = """
Table: branches
- branch_id: INT (Primary Key)
- branch_name: VARCHAR(100) (e.g., 'Melbourne City Central Dealership', 'Eastern Suburbs Automotive Doncaster', 'South East Mega Yard Dandenong')
- suburb: VARCHAR(100) ('Melbourne CBD', 'Doncaster', 'Dandenong')
- postcode: VARCHAR(10)

Table: cars
- car_id: INT (Primary Key)
- branch_id: INT (Foreign Key referencing branches.branch_id)
- vin: VARCHAR(17)
- make: VARCHAR(50) (e.g., 'Toyota', 'Mazda', 'Ford', 'Tesla', 'BMW', etc.)
- model: VARCHAR(50)
- year: INT
- body_type: VARCHAR(30) ('Sedan', 'SUV', 'Hatchback', 'Ute', 'Coupe', etc.)
- fuel_type: VARCHAR(30) ('Petrol', 'Diesel', 'Hybrid', 'Electric', 'PHEV')
- transmission: VARCHAR(30) ('Automatic', 'Manual', 'CVT', 'Dual-Clutch')
- odometer_km: INT
- price_aud: NUMERIC(10,2)
- color: VARCHAR(30)
- status: VARCHAR(20) ('Available', 'Reserved', 'Sold')
"""

def execute_readonly_sql(query: str):
    sanitized = query.strip().rstrip(";")
    upper_query = sanitized.upper()
    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE"]
    if any(k in upper_query.split() for k in destructive_keywords):
        raise ValueError("Non-read query detected. Operations are limited strictly to SELECT statements.")
    
    with engine.connect() as connection:
        result = connection.execute(text(sanitized))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchmany(50)]
        return rows