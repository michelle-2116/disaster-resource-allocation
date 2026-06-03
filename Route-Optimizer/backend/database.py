import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client | None = None

if url and key and not url.startswith("your_") and not key.startswith("your_"):
    supabase = create_client(url, key)
