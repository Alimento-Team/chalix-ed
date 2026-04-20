from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.course_home_api.reviews.models import CourseEmojiReview
from lms.djangoapps.course_home_api.reviews.serializers import (
    CourseEmojiReviewSerializer,
    CourseEmojiReviewSummarySerializer,
)


class CourseReviewView(CreateAPIView):
    """
    POST an emoji review for a course (and optional unit).
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseEmojiReviewSerializer

    def post(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        CourseKey.from_string(course_key_string)  # validate

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        unit_usage_key = data.get('unit_usage_key') or None
        rating = data['rating']

        existing_review = CourseEmojiReview.objects.filter(
            user=request.user,
            course_key=course_key_string,
            unit_usage_key=unit_usage_key,
        ).first()

        # Clicking the same emoji again removes the existing reaction.
        if existing_review and existing_review.rating == rating:
            existing_review.delete()
            return Response({'ok': True, 'removed': True, 'rating': None})

        CourseEmojiReview.objects.update_or_create(
            user=request.user,
            course_key=course_key_string,
            unit_usage_key=unit_usage_key,
            defaults={
                'rating': rating,
                'comment': data.get('comment', ''),
            }
        )

        return Response({'ok': True, 'removed': False, 'rating': rating})


class CourseReviewSummaryView(APIView):
    """
    GET aggregated emoji review counts for a course (and optional unit_usage_key via query param).
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        CourseKey.from_string(course_key_string)  # validate

        unit_usage_key = request.query_params.get('unit_usage_key')

        qs = CourseEmojiReview.objects.filter(course_key=course_key_string)
        if unit_usage_key:
            qs = qs.filter(unit_usage_key=unit_usage_key)

        aggregation = qs.values('rating').annotate(total=Count('id'))
        summary = {'like': 0, 'neutral': 0, 'dislike': 0}
        for row in aggregation:
            summary[row['rating']] = row['total']

        summary['my_rating'] = qs.filter(user=request.user).values_list('rating', flat=True).first()

        return Response(CourseEmojiReviewSummarySerializer(summary).data)
