from rest_framework import serializers
from .models import Certification

class CertificationSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Certification
        fields = ['id', 'title', 'description', 'category', 'progress', 'students', 'image_url']

    def get_image_url(self, obj):
        return obj.image_url()
