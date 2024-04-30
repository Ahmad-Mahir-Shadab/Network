from .models import Post, User
from rest_framework import serializers

class PostSerializer(serializers.ModelSerializer):

  author = serializers.StringRelatedField()
  liked_by = serializers.StringRelatedField(many=True)
  timestamp = serializers.DateTimeField(format="%I:%M %p, %a %d %B %Y")

  class Meta:
    model = Post
    fields = ['id', 'author', 'message', 'timestamp', 'liked_by']

