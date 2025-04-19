from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Certification
from .serializers import CertificationSerializer

# Create your views here.
class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAdminUser]
