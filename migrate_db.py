import streamlit as st
from sqlalchemy import text
from modules import database

def run_migration():
    st.write("Starting migration (SQLite Compatible)...")
    conn = database.get_connection()
    
    # SQLite doesn't support ALTER COLUMN. We must:
    # 1. Create new table with correct schema
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table
    
    with conn.session as s:
        # --- WARDROBE MIGRATION ---
        try:
            st.write("Migrating wardrobe table...")
            # 1. Rename old table
            s.execute(text("ALTER TABLE wardrobe RENAME TO wardrobe_old"))
            
            # 2. Create new table with user_id as TEXT
            s.execute(text('''
                CREATE TABLE wardrobe (
                    id TEXT PRIMARY KEY, 
                    user_id TEXT, 
                    category TEXT, 
                    gender TEXT, 
                    image_path TEXT, 
                    filename TEXT, 
                    added_at FLOAT
                )
            '''))
            
            # 3. Copy data (casting user_id to TEXT)
            s.execute(text('''
                INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at)
                SELECT id, CAST(user_id AS TEXT), category, gender, image_path, filename, added_at
                FROM wardrobe_old
            '''))
            
            # 4. Drop old table
            s.execute(text("DROP TABLE wardrobe_old"))
            st.success("Wardrobe table migrated successfully.")
            
        except Exception as e:
            st.error(f"Wardrobe migration failed: {e}")
            # Attempt rollback if possible (basic)
            try:
                s.execute(text("ALTER TABLE wardrobe_old RENAME TO wardrobe"))
            except: pass

        # --- PLANNER MIGRATION ---
        try:
            st.write("Migrating planner table...")
            # 1. Rename old table
            s.execute(text("ALTER TABLE planner RENAME TO planner_old"))
            
            # 2. Create new table with user_id as TEXT
            s.execute(text('''
                CREATE TABLE planner (
                    date TEXT PRIMARY KEY, 
                    user_id TEXT, 
                    outfit_data TEXT
                )
            '''))
            
            # 3. Copy data
            s.execute(text('''
                INSERT INTO planner (date, user_id, outfit_data)
                SELECT date, CAST(user_id AS TEXT), outfit_data
                FROM planner_old
            '''))
            
            # 4. Drop old table
            s.execute(text("DROP TABLE planner_old"))
            st.success("Planner table migrated successfully.")
            
        except Exception as e:
            st.error(f"Planner migration failed: {e}")
            try:
                s.execute(text("ALTER TABLE planner_old RENAME TO planner"))
            except: pass
            
        s.commit()
    st.write("Migration complete.")

if __name__ == "__main__":
    run_migration()
