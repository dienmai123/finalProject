from app import app, db
from sqlalchemy import text

def add_column_if_not_exists(connection, table, column, type_):
    try:
        connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {type_}'))
        print(f"Added column {column} to {table}")
    except Exception as e:
        print(f"Column {column} might already exist in {table}: {str(e)}")

with app.app_context():
    with db.engine.connect() as connection:
        # Add columns if they don't exist
        add_column_if_not_exists(connection, 'user', 'reset_token', 'VARCHAR(100) UNIQUE')
        add_column_if_not_exists(connection, 'user', 'reset_token_expiry', 'DATETIME')
        connection.commit()
    print("Database update completed!") 