from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import StudyPlan
from certifications.models import Certification
from quizzes.models import Quiz
from resources.models import Resource
from flashcards.models import FlashcardSet
from django.http import JsonResponse

@login_required
def study_plan_list(request):
    # Get user's active certifications
    active_subscriptions = request.user.subscriptions.filter(active=True)
    certifications = [sub.certification for sub in active_subscriptions]

    # Get study plans for these certifications
    study_plans = StudyPlan.objects.filter(
        user=request.user,
        certification__in=certifications
    ).select_related('certification', 'quiz', 'resource', 'flashcard_set')

    # Group study plans by date
    study_plans_by_date = {}
    for plan in study_plans:
        date_key = plan.scheduled_date
        if date_key not in study_plans_by_date:
            study_plans_by_date[date_key] = []
        study_plans_by_date[date_key].append(plan)

    return render(request, 'study_plans/list.html', {
        'study_plans_by_date': study_plans_by_date,
        'certifications': certifications,
        'user': request.user
    })

@login_required
def create_study_plan(request):
    if request.method == 'POST':
        certification_id = request.POST.get('certification')
        activity_type = request.POST.get('activity_type')
        title = request.POST.get('title')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        duration = request.POST.get('duration')
        notes = request.POST.get('notes', '')

        # Get the certification
        certification = get_object_or_404(Certification, id=certification_id)

        # Create the study plan
        study_plan = StudyPlan.objects.create(
            user=request.user,
            certification=certification,
            title=title,
            activity_type=activity_type,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration=duration,
            notes=notes
        )

        # Handle related content based on activity type
        if activity_type == 'quiz':
            quiz_id = request.POST.get('quiz')
            if quiz_id:
                study_plan.quiz = get_object_or_404(Quiz, id=quiz_id)
        elif activity_type == 'resource':
            resource_id = request.POST.get('resource')
            if resource_id:
                study_plan.resource = get_object_or_404(Resource, id=resource_id)
        elif activity_type == 'flashcard':
            flashcard_set_id = request.POST.get('flashcard_set')
            if flashcard_set_id:
                study_plan.flashcard_set = get_object_or_404(FlashcardSet, id=flashcard_set_id)
        elif activity_type == 'exam':
            study_plan.exam_date = request.POST.get('exam_date')
            study_plan.exam_time = request.POST.get('exam_time')
            study_plan.exam_location = request.POST.get('exam_location')

        study_plan.save()
        messages.success(request, 'Study plan created successfully!')
        return redirect('study_plan_list')

    # GET request - show form
    active_subscriptions = request.user.subscriptions.filter(active=True)
    certifications = [sub.certification for sub in active_subscriptions]

    return render(request, 'study_plans/create.html', {
        'certifications': certifications,
        'user': request.user
    })

@login_required
def update_study_plan(request, plan_id):
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)

    if request.method == 'POST':
        study_plan.title = request.POST.get('title')
        study_plan.scheduled_date = request.POST.get('scheduled_date')
        study_plan.scheduled_time = request.POST.get('scheduled_time')
        study_plan.duration = request.POST.get('duration')
        study_plan.notes = request.POST.get('notes', '')
        study_plan.status = request.POST.get('status')

        # Update related content
        if study_plan.activity_type == 'quiz':
            quiz_id = request.POST.get('quiz')
            if quiz_id:
                study_plan.quiz = get_object_or_404(Quiz, id=quiz_id)
        elif study_plan.activity_type == 'resource':
            resource_id = request.POST.get('resource')
            if resource_id:
                study_plan.resource = get_object_or_404(Resource, id=resource_id)
        elif study_plan.activity_type == 'flashcard':
            flashcard_set_id = request.POST.get('flashcard_set')
            if flashcard_set_id:
                study_plan.flashcard_set = get_object_or_404(FlashcardSet, id=flashcard_set_id)
        elif study_plan.activity_type == 'exam':
            study_plan.exam_date = request.POST.get('exam_date')
            study_plan.exam_time = request.POST.get('exam_time')
            study_plan.exam_location = request.POST.get('exam_location')

        study_plan.save()
        messages.success(request, 'Study plan updated successfully!')
        return redirect('study_plan_list')

    return render(request, 'study_plans/update.html', {
        'study_plan': study_plan,
        'user': request.user
    })

@login_required
def delete_study_plan(request, plan_id):
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
    study_plan.delete()
    messages.success(request, 'Study plan deleted successfully!')
    return redirect('study_plan_list')

@login_required
def get_activity_content(request):
    """AJAX endpoint to get content based on activity type and certification"""
    certification_id = request.GET.get('certification_id')
    activity_type = request.GET.get('activity_type')

    if not certification_id or not activity_type:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    certification = get_object_or_404(Certification, id=certification_id)

    if activity_type == 'quiz':
        content = Quiz.objects.filter(certification=certification)
        data = [{'id': q.id, 'title': q.title} for q in content]
    elif activity_type == 'resource':
        content = Resource.objects.filter(certification=certification)
        data = [{'id': r.id, 'title': r.title} for r in content]
    elif activity_type == 'flashcard':
        content = FlashcardSet.objects.filter(certification=certification)
        data = [{'id': f.id, 'title': f.title} for f in content]
    else:
        data = []

    return JsonResponse({'content': data})
