import streamlit as st
from sqlalchemy import text
from modules import database

def run_migration():
    st.write("Starting migration...")
    conn = database.get_connection()
    with conn.session as s:
        # Wardrobe Table
        try:
            st.write("Altering wardrobe table...")
            # Postgres syntax to cast integer to text
            s.execute(text("ALTER TABLE wardrobe ALTER COLUMN user_id TYPE TEXT"))
            st.success("Wardrobe table altered successfully.")
        except Exception as e:
            st.error(f"Wardrobe migration failed: {e}")

        # Planner Table
        try:
            st.write("Altering planner table...")
            s.execute(text("ALTER TABLE planner ALTER COLUMN user_id TYPE TEXT"))
            st.success("Planner table altered successfully.")
        except Exception as e:
            st.error(f"Planner migration failed: {e}")
            
        s.commit()
    st.write("Migration complete.")

if __name__ == "__main__":
    run_migration()
