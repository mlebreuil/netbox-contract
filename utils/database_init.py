import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg2 import connect, extensions

dotenv_path = Path('.devcontainer/env/postgres.env')
load_dotenv(dotenv_path=dotenv_path)

db = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')


# Connect to your postgres DB
conn = connect('host=db user=postgres password=postgres')

# set the isolation level for the connection's cursors
# will raise ActiveSqlTransaction exception otherwise
autocommit = extensions.ISOLATION_LEVEL_AUTOCOMMIT
conn.set_isolation_level(autocommit)

# Open a cursor to perform database operations
cur = conn.cursor()

# The below 2 lines are required if the database already exists
# cur.execute(f"DROP DATABASE {db};")
# cur.execute(f"DROP USER {user};")

cur.execute(f'CREATE DATABASE {db};')
cur.execute(f"CREATE USER netbox WITH PASSWORD '{password}';")
cur.execute(f'ALTER DATABASE {db} OWNER TO {user};')

# Required to run unittest as the django user need to create the test db
cur.execute(f'ALTER ROLE {user} CREATEDB;')

# Make the changes to the database persistent
conn.commit()

# Close communication with the database
cur.close()
conn.close()

# required on postgres v15 or later
conn = connect(host='db', user='postgres', password='postgres', database=db)
autocommit = extensions.ISOLATION_LEVEL_AUTOCOMMIT
conn.set_isolation_level(autocommit)
cur = conn.cursor()
cur.execute(f'GRANT CREATE ON SCHEMA public TO {user};')
conn.commit()
cur.close()
conn.close()
