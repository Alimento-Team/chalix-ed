"""
URLs for the Studio API [Course Run]
"""


from rest_framework.routers import DefaultRouter


from .views.course_runs import CourseRunViewSet
from .views.organizations import OrganizationViewSet

app_name = 'cms.djangoapps.api.v1'


router = DefaultRouter()
router.register(r'course_runs', CourseRunViewSet, basename='course_run')
router.register(r'organizations', OrganizationViewSet, basename='organization')
urlpatterns = router.urls
