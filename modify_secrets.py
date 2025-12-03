import os

secrets_path = ".streamlit/secrets.toml"

with open(secrets_path, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "SUPABASE_DB_URL" in line:
        new_lines.append('SUPABASE_DB_URL = "sqlite:///vogue_ai.db"\n')
    else:
        new_lines.append(line)

with open(secrets_path, "w") as f:
    f.writelines(new_lines)

print("Updated secrets.toml to use SQLite.")
