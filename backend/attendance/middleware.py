from django.db import connection
from .services import ensure_db_initialized

class AutoMigrateMiddleware:
    """
    Middleware that ensures database tables exist on every request.
    If attendance.db was deleted, it automatically triggers auto-migration and seeding.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        ensure_db_initialized()

    def __call__(self, request):
        try:
            table_names = connection.introspection.table_names()
            if 'students' not in table_names or 'courses' not in table_names:
                ensure_db_initialized()
        except Exception:
            ensure_db_initialized()

        response = self.get_response(request)
        return response
