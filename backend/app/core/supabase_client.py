from supabase import Client, create_client

from .config import settings


def get_supabase_client() -> Client:
    supabase_url: str = settings.supabase_url
    supabase_key: str = (
        settings.supabase_anon_key
    )  # Use anon key for client-side/public access
    return create_client(supabase_url, supabase_key)


# def get_supabase_service_client() -> Client:
#     supabase_url: str = settings.supabase_url
#     supabase_key: str = (
#         settings.supabase_service_key
#     )  # Use service key for backend operations
#     return create_client(supabase_url, supabase_key)


supabase_client = get_supabase_client()
# supabase_service_client = get_supabase_service_client()
