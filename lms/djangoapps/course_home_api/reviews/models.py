from django.conf import settings
from django.db import models


class CourseEmojiReview(models.Model):
    """
    Stores a simple emoji review from a learner for a course and optional unit.

    rating: one of 'like' | 'neutral' | 'dislike'
    """

    RATING_CHOICES = (
        ('like', 'Like'),
        ('neutral', 'Neutral'),
        ('dislike', 'Dislike'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emoji_reviews')
    course_key = models.CharField(max_length=255, db_index=True)
    unit_usage_key = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('user', 'course_key', 'unit_usage_key')
        indexes = [
            models.Index(fields=['course_key', 'unit_usage_key']),
        ]

    def __str__(self):
        return f"CourseEmojiReview<{self.pk}>"
