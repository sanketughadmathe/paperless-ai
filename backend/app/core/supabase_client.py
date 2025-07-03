from supabase import Client, create_client

from .config import settings


def get_supabase_client() -> Client:
    supabase_url: str = settings.supabase_url
    supabase_key: str = (
        settings.supabase_anon_key
    )  # Use anon key for client-side/public access
    return create_client(supabase_url, supabase_key)


def get_authenticated_supabase_client(access_token: str) -> Client:
    """
    Create a Supabase client with the user's authentication context.
    This ensures RLS policies work correctly with auth.uid().
    """
    supabase_url: str = settings.supabase_url
    supabase_key: str = settings.supabase_anon_key

    client = create_client(supabase_url, supabase_key)

    # Set the authorization header for RLS context
    # This header will be sent with all database requests
    client.postgrest.auth(access_token)

    return client


# def get_supabase_service_client() -> Client:
#     supabase_url: str = settings.supabase_url
#     supabase_key: str = (
#         settings.supabase_service_key
#     )  # Use service key for backend operations
#     return create_client(supabase_url, supabase_key)


supabase_client = get_supabase_client()
# supabase_service_client = get_supabase_service_client()
