# Intentionally left blank to avoid importing models at package import time.
# Models should be registered via their application modules (for example,
# import Organization from cms.djangoapps.models.organization within
# cms.djangoapps.contentstore.models) so Django loads them under the
# correct app in INSTALLED_APPS.

# Provide a small compatibility alias for callers importing Organization from
# `cms.djangoapps.models`. Import from the contentstore app where the model
# is actually defined. Import is optional to avoid hard import-time side effects
# in some test/bootstrap paths.
try:
    from cms.djangoapps.contentstore.models import Organization  # noqa: F401
except Exception:
    # If import fails (test/partial bootstrap), don't raise here — callers
    # should import directly from contentstore.models where possible.
    pass
