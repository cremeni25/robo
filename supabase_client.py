from supabase import create_client
import os

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise Exception("Supabase URL ou KEY não configurados no ambiente Render.")

    return create_client(url, key)
