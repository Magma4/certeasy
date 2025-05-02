from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Certification
from .serializers import CertificationSerializer
from rest_framework import filters

# Create your views here.
class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category']
