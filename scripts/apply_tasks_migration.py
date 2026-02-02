import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    migration_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations", "create_tasks_table.sql")
    
    logger.info(f"Reading migration file: {migration_file}")
    
    try:
        with open(migration_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        logger.info("Connecting to database...")
        with engine.connect() as connection:
            logger.info("Executing migration...")
            # We use text() to wrap the SQL string
            # And execute it. 
            # Note: SQLAlchemy might wrap this in a transaction automatically.
            # The SQL file has BEGIN; ... COMMIT; which might conflict if SQLAlchemy is also managing transactions.
            # Let's try executing it directly.
            
            # Since the SQL file has explicit BEGIN/COMMIT, we should probably treat it as a single block.
            # However, SQLAlchemy's execute might fail with multiple statements if not configured right.
            # A safer way with SQLAlchemy is to rely on its transaction management.
            
            # Let's strip the BEGIN and COMMIT from the file if we want SQLAlchemy to handle it, 
            # OR execute it raw.
            
            # Trying raw execution of the whole block.
            connection.execute(text(sql_content))
            connection.commit()
            
        logger.info("Migration applied successfully!")
        
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        # Print more details if possible
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_migration()
