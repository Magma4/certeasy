from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from certifications.models import Certification

@login_required
def generate_mock_exam(request):
    if request.method == 'GET':
        certifications = Certification.objects.all()
        return render(request, 'generate_mock_exam.html', {'certifications': certifications})
