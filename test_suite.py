import sqlalchemy
from sqlalchemy import text
import toml
import time
import json
import os

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def print_pass(msg):
    print(f"{GREEN}{msg}{RESET}")

def print_fail(msg):
    print(f"{RED}{msg}{RESET}")

def load_secrets():
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        return secrets
    except Exception as e:
        print_fail(f"❌ Could not load secrets: {e}")
        return None

def get_db_connection(secrets):
    try:
        db_url = secrets["SUPABASE_DB_URL"]
        # Use sqlalchemy directly since we are not in streamlit
        engine = sqlalchemy.create_engine(db_url)
        conn = engine.connect()
        return conn
    except Exception as e:
        print_fail(f"❌ Connection Failed: {e}")
        return None

def run_tests():
    print("🚀 Starting System Health Check...\n")
    
    secrets = load_secrets()
    if not secrets:
        return

    # 1. Database Connection Test
    conn = get_db_connection(secrets)
    if conn:
        print_pass("✅ Database Connected")
    else:
        return # Stop if no connection

    try:
        # 2. Simulation: "Add to Closet" Button
        print("\nTesting 'Add to Closet'...")
        dummy_id = "test_9999"
        user_id = 9999
        category = "TestItem"
        gender = "Men's Fashion"
        
        # Clean up if exists from previous run
        conn.execute(text("DELETE FROM wardrobe WHERE id=:id"), {"id": dummy_id})
        conn.commit()

        insert_query = text("INSERT INTO wardrobe (id, user_id, category, gender, image_path, filename, added_at) VALUES (:id, :user_id, :category, :gender, :image_path, :filename, :added_at)")
        conn.execute(insert_query, {
            "id": dummy_id,
            "user_id": user_id,
            "category": category,
            "gender": gender,
            "image_path": "test.jpg",
            "filename": "test.jpg",
            "added_at": time.time()
        })
        conn.commit()
        
        # Verify
        result = conn.execute(text("SELECT * FROM wardrobe WHERE id=:id"), {"id": dummy_id}).fetchone()
        if result:
            print_pass("✅ 'Add to Closet' Logic works")
        else:
            print_fail("❌ Insert Failed")

        # 3. Simulation: "Remove" Button
        print("\nTesting 'Remove'...")
        delete_query = text("DELETE FROM wardrobe WHERE id=:id")
        conn.execute(delete_query, {"id": dummy_id})
        conn.commit()
        
        # Verify
        result = conn.execute(text("SELECT * FROM wardrobe WHERE id=:id"), {"id": dummy_id}).fetchone()
        if not result:
            print_pass("✅ 'Remove' Logic works")
        else:
            print_fail("❌ Delete Failed")

        # 4. Simulation: "Generate Plan" Button
        print("\nTesting 'Generate Plan'...")
        test_date = "2099-01-01"
        test_plan = {"Top": "test_shirt", "Bottom": "test_pants"}
        
        plan_query = text("INSERT INTO planner (date, user_id, outfit_data) VALUES (:date, :user_id, :outfit_data) ON CONFLICT (date) DO UPDATE SET outfit_data = EXCLUDED.outfit_data")
        conn.execute(plan_query, {
            "date": test_date,
            "user_id": 1,
            "outfit_data": json.dumps(test_plan)
        })
        conn.commit()
        
        # Verify
        result = conn.execute(text("SELECT outfit_data FROM planner WHERE date=:date"), {"date": test_date}).fetchone()
        if result and json.loads(result[0]) == test_plan:
            print_pass("✅ 'Generate Plan' Logic works")
            # Cleanup
            conn.execute(text("DELETE FROM planner WHERE date=:date"), {"date": test_date})
            conn.commit()
        else:
            print_fail("❌ Plan Save Failed")

        # 5. Simulation: "Sign In" Logic
        print("\nTesting 'Sign In' Logic...")
        # Ensure default user exists (id 1)
        user_query = text("SELECT * FROM users WHERE id=1")
        result = conn.execute(user_query).fetchone()
        if result:
            print_pass(f"✅ Login Retrieval works (Found User: {result[1]})")
        else:
            print_fail("❌ Login Retrieval Failed (User ID 1 not found)")

    except Exception as e:
        print_fail(f"❌ An error occurred during testing: {e}")
    finally:
        conn.close()
        print("\n🏁 Health Check Complete.")

if __name__ == "__main__":
    run_tests()
