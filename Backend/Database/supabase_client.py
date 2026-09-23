from Backend.config import get_env
from supabase import create_client, Client

url = get_env("SUPABASE_URL")
key = get_env("SUPABASE_KEY")
service_key = get_env("SUPABASE_SERVICE_ROLE_KEY", default=key)

supabase: Client = create_client(url, key) if url and key else None
supabase_admin: Client = create_client(url, service_key) if url and service_key else None
