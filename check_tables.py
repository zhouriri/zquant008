from zquant.database import SessionLocal
from sqlalchemy import text
from loguru import logger

def check():
    db = SessionLocal()
    try:
        result = db.execute(text("SHOW TABLES LIKE 'zq_quant_factor_spacex_%'"))
        tables = [row[0] for row in result]
        print(f"Total spacex tables found: {len(tables)}")
        if tables:
            print("First 5 tables:")
            for t in tables[:5]:
                print(f"  - {t}")
        else:
            print("No tables found. This is why the view cannot be created.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()

