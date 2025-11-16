"""
URLs for the Studio API [Course Run]
"""


from rest_framework.routers import DefaultRouter


from .views.course_runs import CourseRunViewSet
from .views.organizations import OrganizationViewSet
from .views.professional_fields import ProfessionalFieldViewSet

app_name = 'cms.djangoapps.api.v1'


router = DefaultRouter()
router.register(r'course_runs', CourseRunViewSet, basename='course_run')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'professional_fields', ProfessionalFieldViewSet, basename='professional_field')
urlpatterns = router.urls
