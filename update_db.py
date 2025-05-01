from app import app, db
from sqlalchemy import text

with app.app_context():
    # This will add the new last_login column to the existing user table
    with db.engine.connect() as connection:
        connection.execute(text('ALTER TABLE user ADD COLUMN last_login DATETIME'))
        connection.commit()
    print("Database updated successfully with last_login column!") 