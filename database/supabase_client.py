from supabase import Client, create_client

from config import settings

_supabase_admin: Client | None = None


def get_supabase_admin() -> Client:
    global _supabase_admin
    if not settings.supabase_configured:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )
    if _supabase_admin is None:
        _supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_admin


class _SupabaseProxy:
    def __getattr__(self, name):
        return getattr(get_supabase_admin(), name)


supabase_admin = _SupabaseProxy()


def fetch_one(query):
    """Run a postgrest query and return the first row or None.

    Replaces ``.single().execute()`` which throws on 0 rows. Use when the
    row may legitimately not exist and you want to handle 'not found' yourself.
    """
    result = query.limit(1).execute()
    rows = result.data or []
    return rows[0] if rows else None
