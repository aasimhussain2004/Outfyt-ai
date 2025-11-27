import os
import shutil
import glob

def cleanup_project():
    print("Starting project cleanup...")
    
    # Define patterns and paths to remove
    base_dir = os.getcwd()
    
    # 1. Python Cache (Recursive)
    print("\n--- Cleaning Python Cache ---")
    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d == "__pycache__" or d == ".pytest_cache":
                dir_path = os.path.join(root, d)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Deleted directory: {dir_path}")
                except Exception as e:
                    print(f"Error deleting {dir_path}: {e}")

    # 2. Legacy Database
    print("\n--- Cleaning Legacy Database ---")
    db_path = os.path.join(base_dir, "vogue_ai.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted file: {db_path}")
        except Exception as e:
            print(f"Error deleting {db_path}: {e}")
    else:
        print("vogue_ai.db not found.")

    # 3. Temp Files
    print("\n--- Cleaning Temp Files ---")
    temp_files = ["test_output.txt"]
    for f_name in temp_files:
        f_path = os.path.join(base_dir, f_name)
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                print(f"Deleted file: {f_path}")
            except Exception as e:
                print(f"Error deleting {f_path}: {e}")
    
    # Remove any .tmp files
    for tmp_file in glob.glob(os.path.join(base_dir, "*.tmp")):
        try:
            os.remove(tmp_file)
            print(f"Deleted file: {tmp_file}")
        except Exception as e:
            print(f"Error deleting {tmp_file}: {e}")

    # 4. Local Audio in static/
    print("\n--- Cleaning Local Audio ---")
    static_dir = os.path.join(base_dir, "static")
    if os.path.exists(static_dir):
        for f_name in os.listdir(static_dir):
            if f_name.endswith(".mp3"):
                f_path = os.path.join(static_dir, f_name)
                try:
                    os.remove(f_path)
                    print(f"Deleted file: {f_path}")
                except Exception as e:
                    print(f"Error deleting {f_path}: {e}")
    else:
        print("static/ directory not found.")

    print("\nCleanup complete!")

if __name__ == "__main__":
    cleanup_project()
