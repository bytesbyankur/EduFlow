import os
import logging
from django.db import connection
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_COURSES = [
    "Advanced Neural Networks",
    "Ethics in AI",
    "Computer Vision 101"
]

_is_db_checked = False

def ensure_database_ready():
    """
    Checks if database tables exist. If attendance.db was deleted or tables are missing,
    automatically runs migrations and creates default course offerings.
    Does NOT seed fake/mock students. Only real registered students are stored.
    Also ensures known_faces directory is created.
    """
    global _is_db_checked
    
    # Ensure known_faces directory exists
    known_dir = getattr(settings, 'KNOWN_FACES_DIR', os.path.join(settings.BASE_DIR, 'known_faces'))
    os.makedirs(known_dir, exist_ok=True)

    try:
        table_names = connection.introspection.table_names()
        required_tables = {'students', 'courses', 'course_enrollments', 'attendance_logs'}

        # If any core table is missing, run migrations
        if not required_tables.issubset(set(table_names)):
            logger.info("Database tables missing. Running automatic migrations...")
            call_command('migrate', interactive=False, verbosity=0)

        # Ensure default courses exist
        from .models import Course
        for c_name in DEFAULT_COURSES:
            Course.objects.get_or_create(name=c_name)

        _is_db_checked = True

    except Exception as e:
        logger.error(f"Database auto-provisioning error: {e}")
