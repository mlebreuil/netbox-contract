from psycopg2 import connect, extensions

# Connect to your postgres DB
conn = connect('host=db user=postgres password=postgres')

# set the isolation level for the connection's cursors
# will raise ActiveSqlTransaction exception otherwise
autocommit = extensions.ISOLATION_LEVEL_AUTOCOMMIT
conn.set_isolation_level(autocommit)

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a query
cur.execute('DROP DATABASE netbox;')
cur.execute('DROP USER netbox;')
cur.execute('CREATE DATABASE netbox;')
cur.execute("CREATE USER netbox WITH PASSWORD 'J5brHrAXFLQSif0K';")
cur.execute('GRANT ALL PRIVILEGES ON DATABASE netbox TO netbox;')
cur.execute('ALTER USER netbox CREATEDB;')

# Make the changes to the database persistent
conn.commit()

# Close communication with the database
cur.close()
conn.close()
