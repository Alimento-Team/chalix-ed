"""
Contentstore Application Configuration

Above-modulestore level signal handlers are connected here.
"""


from django.apps import AppConfig


class ContentstoreConfig(AppConfig):
    """
    Application Configuration for Contentstore.
    """
    name = 'cms.djangoapps.contentstore'

    def ready(self):
        """
        Connect handlers to signals.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from .signals import handlers  # pylint: disable=unused-import
        
        # Ensure default Bộ organization exists
        self._ensure_default_organization()
    
    def _ensure_default_organization(self):
        """
        Ensure the default Bộ organization exists.
        This is called when the CMS starts to guarantee the default org is available.
        """
        try:
            from django.db import connection
            from django.db.utils import OperationalError, ProgrammingError
            
            # Check if we can access the database (migrations might not have run yet)
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        "SELECT 1 FROM contentstore_chalixorganization WHERE code = 'BO_DEFAULT' LIMIT 1"
                    )
                    if cursor.fetchone():
                        # Default org already exists
                        return
                except (OperationalError, ProgrammingError):
                    # Table doesn't exist yet (migrations not run), skip
                    return
            
            # Import models only after checking database accessibility
            from .models import ChalixOrganization
            
            # Create the default organization if it doesn't exist
            ChalixOrganization.objects.get_or_create(
                code='BO_DEFAULT',
                defaults={
                    'name': 'bo_default',
                    'display_name': 'Bộ (Mặc định)',
                    'description': 'Tổ chức mặc định cho các chương trình học được tạo trước đây',
                    'is_active': True,
                }
            )
        except Exception as e:
            # Log the error but don't prevent the app from starting
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not ensure default Bộ organization exists: {e}")
