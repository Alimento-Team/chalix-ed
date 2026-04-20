from rest_framework import serializers


class CourseEmojiReviewSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=['like', 'neutral', 'dislike'])
    comment = serializers.CharField(allow_blank=True, required=False)
    unit_usage_key = serializers.CharField(allow_blank=True, required=False, allow_null=True)


class CourseEmojiReviewSummarySerializer(serializers.Serializer):
    like = serializers.IntegerField()
    neutral = serializers.IntegerField()
    dislike = serializers.IntegerField()
    my_rating = serializers.ChoiceField(
        choices=['like', 'neutral', 'dislike'],
        required=False,
        allow_null=True,
    )