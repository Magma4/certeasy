from django.shortcuts import render, get_object_or_404, redirect
from certifications.models import Certification
from django.contrib.auth.decorators import login_required
from accounts.models import Subscription, User, UserLogin
from quizzes.models import Quiz, QuizAttempt
from django.db.models import Avg, Count
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from resources.models import Resource, VideoView
from discussions.models import Post, Like, Comment
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from flashcards.models import Flashcard
from study_plans.models import StudyPlan
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import timedelta
from collections import defaultdict
import math
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

def landing_page(request):
    return render(request, 'landing_page.html')

def login_page(request):
    return render(request, 'login.html')

def signup_page(request):
    return render(request, 'signup.html')

@login_required
def dashboard_page(request):
    user = request.user
    # Get user's active certifications
    active_subscriptions = Subscription.objects.filter(
        user=user,
        active=True
    ).select_related('certification')
    active_certifications = [sub.certification for sub in active_subscriptions]
    active_cert_ids = [cert.id for cert in active_certifications]

    # Handle new study plan submission
    if request.method == "POST":
        StudyPlan.objects.create(
            user=user,
            certification_id=request.POST.get("certification"),
            title=request.POST.get("title"),
            activity_type=request.POST.get("activity_type"),
            scheduled_date=request.POST.get("scheduled_date"),
            scheduled_time=request.POST.get("scheduled_time"),
            duration=request.POST.get("duration"),
        )
        return redirect("dashboard")

    # Get ALL certifications
    all_certifications = Certification.objects.all()

    # Calculate progress for each active certification (quizzes + videos)
    for cert in active_certifications:
        # Quizzes
        cert_quizzes = Quiz.objects.filter(certification=cert)
        total_quizzes = cert_quizzes.count()
        completed_quizzes = QuizAttempt.objects.filter(
            quiz__in=cert_quizzes,
            user=request.user,
            completed=True
        ).values('quiz').distinct().count()
        # Videos
        total_videos = Resource.objects.filter(certification=cert, type='video').count()
        watched_videos = VideoView.objects.filter(user=request.user, resource__certification=cert).count()
        # Progress calculation
        total_items = total_quizzes + total_videos
        completed_items = completed_quizzes + watched_videos
        if total_items > 0:
            cert.progress = float(completed_items) / float(total_items) * 100
            if math.isnan(cert.progress) or cert.progress is None:
                cert.progress = 0.0
        else:
            cert.progress = 0.0

    # --- Calculate streak ---
    today = timezone.now().date()
    login_dates = set(UserLogin.objects.filter(
        user=user,
        login_date__gte=today - timedelta(days=30)  # Look back 30 days
    ).values_list('login_date', flat=True))

    streak = 0
    current_date = today
    while current_date in login_dates:
        streak += 1
        current_date -= timedelta(days=1)

    # If today's login hasn't been recorded yet, add it
    if today not in login_dates:
        UserLogin.objects.get_or_create(user=user, login_date=today)
        streak += 1

    # --- Get notifications ---
    notifications = _get_user_notifications(user)

    # --- Calculate overall progress ---
    total_items = 0
    completed_items = 0
    all_completed = True

    for cert in all_certifications:
        # Videos
        total_videos = Resource.objects.filter(certification=cert, type='video').count()
        watched_videos = VideoView.objects.filter(user=user, resource__certification=cert).count()

        # Quizzes
        total_quizzes = Quiz.objects.filter(certification=cert).count()
        completed_quizzes = QuizAttempt.objects.filter(
            user=user,
            quiz__certification=cert,
            completed=True
        ).values('quiz').distinct().count()

        if total_videos > 0 and watched_videos < total_videos:
            all_completed = False
        if total_quizzes > 0 and completed_quizzes < total_quizzes:
            all_completed = False

        total_items += total_videos + total_quizzes
        completed_items += watched_videos + completed_quizzes

    overall_progress = 100 if all_completed and total_items > 0 else int((completed_items / total_items) * 100) if total_items > 0 else 0

    # Calculate quiz average
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        completed=True
    ).select_related('quiz')
    quiz_average = quiz_attempts.aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0

    # Get user's custom study plans
    study_plans = StudyPlan.objects.filter(user=user)
    print('--- DEBUG: Today is', today)
    for plan in study_plans:
        print('StudyPlan:', plan.id, 'scheduled_date:', plan.scheduled_date)
    study_plans = study_plans.filter(scheduled_date=today).order_by('scheduled_time')
    today_tasks = []
    for plan in study_plans:
        scheduled_time = plan.scheduled_time
        if isinstance(scheduled_time, str):
            try:
                scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            except ValueError:
                try:
                    scheduled_time = datetime.strptime(scheduled_time, '%H:%M:%S').time()
                except Exception:
                    scheduled_time = None
        time_str = scheduled_time.strftime('%I:%M %p') if scheduled_time else str(plan.scheduled_time)
        today_tasks.append({
            'id': plan.id,
            'time': time_str,
            'title': plan.title,
            'duration': f"{plan.duration} min",
            'activity': plan.get_activity_type_display(),
            'status': plan.status.replace('_', ' ').title()
        })

    # Get recent activity: quizzes and videos
    recent_quiz_activity = QuizAttempt.objects.filter(
        user=user
    ).select_related('quiz').order_by('-start_time')[:4]
    recent_video_activity = VideoView.objects.filter(
        user=user
    ).select_related('resource').order_by('-watched_at')[:4]
    # Merge and sort by time (most recent first)
    recent_activity = list(recent_quiz_activity) + list(recent_video_activity)
    recent_activity.sort(key=lambda x: getattr(x, 'start_time', None) or getattr(x, 'watched_at', None), reverse=True)
    recent_activity = recent_activity[:7]
    # Annotate type for template logic
    for activity in recent_activity:
        if hasattr(activity, 'quiz'):
            activity.type = 'quiz'
        elif hasattr(activity, 'resource'):
            activity.type = 'video'

    # Get upcoming exams
    upcoming_exams = [
        {
            'date': '15',
            'month': 'May',
            'title': 'GRE Practice Test',
            'description': 'Full-length simulation with analytics',
            'days_left': '11',
            'priority': 'Critical',
            'priority_color': 'red'
        },
        {
            'date': '22',
            'month': 'May',
            'title': 'LSAT Logic Section',
            'description': 'Timed assessment',
            'days_left': '18',
            'priority': 'Important',
            'priority_color': 'amber'
        },
        {
            'date': '10',
            'month': 'Jun',
            'title': 'CFA Level I Mock Exam',
            'description': 'Full-length preparation',
            'days_left': '37',
            'priority': 'Planned',
            'priority_color': 'blue'
        }
    ]

    # Prepare user statistics
    user_stats = {
        'overall_progress': overall_progress,
        'tasks_total': len(today_tasks),
        'tasks_completed': len([task for task in today_tasks if task['status'] == 'Completed']),
        'streak': streak,
        'quiz_average': round(quiz_average, 1)
    }

    # Get 7 quizzes the user has not yet attempted (from active certifications)
    attempted_quiz_ids = QuizAttempt.objects.filter(user=user).values_list('quiz_id', flat=True)
    unattempted_quizzes = Quiz.objects.filter(certification__in=active_certifications).exclude(id__in=attempted_quiz_ids)[:7]

    return render(request, 'dashboard.html', {
        'user': request.user,
        'certifications': all_certifications,
        'active_certifications': active_certifications,
        'user_stats': user_stats,
        'notifications': notifications,
        'study_plan': today_tasks,
        'recent_activity': recent_activity,
        'upcoming_exams': upcoming_exams,
        'unattempted_quizzes': unattempted_quizzes,
    })

def _get_user_notifications(user):
    """Helper function to get user notifications"""
    notifications = []
    from quizzes.models import QuizAttempt
    from discussions.models import Like, Comment
    from accounts.models import Subscription
    from django.utils import timezone
    from datetime import timedelta

    # Quiz notifications
    recent_quiz_attempts = QuizAttempt.objects.filter(
        user=user,
        start_time__gte=timezone.now() - timedelta(days=7)
    ).select_related('quiz').order_by('-start_time')[:3]

    for attempt in recent_quiz_attempts:
        if attempt.completed:
            score = round(attempt.score, 1)
            notifications.append({
                'id': f'quiz_{attempt.id}',
                'title': f"Completed {attempt.quiz.title} (Score: {score}%)",
                'time': _humanize_time(timezone.now() - attempt.start_time),
                'type': 'quiz',
                'icon': 'clipboard-check',
            })

    # Streak notifications
    today = timezone.now().date()
    login_dates = set(UserLogin.objects.filter(
        user=user,
        login_date__gte=today - timedelta(days=30)
    ).values_list('login_date', flat=True))

    streak = 0
    current_date = today
    while current_date in login_dates:
        streak += 1
        current_date -= timedelta(days=1)

    if streak == 0:
        notifications.append({
            'id': 'streak_break',
            'title': 'Your streak has ended',
            'time': 'Just now',
            'type': 'streak',
            'icon': 'fire',
            'message': 'Log in tomorrow to start a new streak!'
        })

    # Post interaction notifications
    recent_likes = Like.objects.filter(
        post__user=user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('post', 'user').order_by('-created_at')[:3]

    for like in recent_likes:
        notifications.append({
            'id': f'like_{like.id}',
            'title': f'{like.user.get_full_name() or like.user.username} liked your post',
            'time': _humanize_time(timezone.now() - like.created_at),
            'type': 'like',
            'icon': 'thumbs-up',
            'post_title': like.post.title
        })

    recent_comments = Comment.objects.filter(
        post__user=user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('post', 'user').order_by('-created_at')[:3]

    for comment in recent_comments:
        notifications.append({
            'id': f'comment_{comment.id}',
            'title': f'{comment.user.get_full_name() or comment.user.username} commented on your post',
            'time': _humanize_time(timezone.now() - comment.created_at),
            'type': 'comment',
            'icon': 'comment',
            'post_title': comment.post.title
        })

    # Subscription notifications
    expiring_subscriptions = Subscription.objects.filter(
        user=user,
        active=True,
        end_date__isnull=False
    ).select_related('certification')

    for sub in expiring_subscriptions:
        days_left = (sub.end_date.date() - timezone.now().date()).days
        if days_left > 0:
            title = f"{sub.certification.title} subscription expires in {days_left} day{'s' if days_left != 1 else ''}"
            time_str = f"in {days_left} day{'s' if days_left != 1 else ''}"
        elif days_left == 0:
            title = f"{sub.certification.title} subscription expires today"
            time_str = "today"
        else:
            title = f"{sub.certification.title} subscription expired {abs(days_left)} day{'s' if abs(days_left) != 1 else ''} ago"
            time_str = f"{abs(days_left)} day{'s' if abs(days_left) != 1 else ''} ago"
        notifications.append({
            'id': f'sub_{sub.id}',
            'title': title,
            'time': time_str,
            'type': 'subscription',
            'icon': 'calendar',
        })

    return notifications

@login_required
def mycertifications(request):
    # Get active subscriptions for the current user
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        active=True
    ).select_related('certification')

    # Get the certifications from active subscriptions
    active_certifications = [sub.certification for sub in active_subscriptions]

    # Get all available certifications (excluding active ones)
    all_certifications = Certification.objects.exclude(
        id__in=[cert.id for cert in active_certifications]
    )

    # Calculate progress for each active certification (quizzes + videos)
    for cert in active_certifications:
        # Quizzes
        cert_quizzes = Quiz.objects.filter(certification=cert)
        total_quizzes = cert_quizzes.count()
        completed_quizzes = QuizAttempt.objects.filter(
            quiz__in=cert_quizzes,
            user=request.user,
            completed=True
        ).values('quiz').distinct().count()
        # Videos
        total_videos = Resource.objects.filter(certification=cert, type='video').count()
        watched_videos = VideoView.objects.filter(user=request.user, resource__certification=cert).count()
        # Progress calculation
        total_items = total_quizzes + total_videos
        completed_items = completed_quizzes + watched_videos
        if total_items > 0:
            cert.progress = float(completed_items) / float(total_items) * 100
            if math.isnan(cert.progress) or cert.progress is None:
                cert.progress = 0.0
        else:
            cert.progress = 0.0

    # --- Weekly study hours breakdown ---
    today = timezone.now().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]  # 7 days, oldest to newest
    weekly_study = {}
    for cert in active_certifications:
        cert_days = []
        for day in days:
            # --- Videos: sum durations from VideoView (if available), else estimate 5 min per video ---
            video_minutes = 0
            video_views = VideoView.objects.filter(
                user=request.user,
                resource__certification=cert,
                watched_at__date=day
            )
            for view in video_views:
                # If you have a duration field, use it. Otherwise, estimate 5 min per view.
                if hasattr(view, 'duration') and view.duration:
                    video_minutes += int(view.duration / 60)
                else:
                    video_minutes += 5

            # --- Quizzes: sum duration of completed QuizAttempts for this cert and day ---
            quiz_minutes = 0
            quiz_attempts = QuizAttempt.objects.filter(
                user=request.user,
                quiz__certification=cert,
                completed=True,
                start_time__date=day
            )
            for attempt in quiz_attempts:
                if attempt.end_time and attempt.start_time:
                    duration = (attempt.end_time - attempt.start_time).total_seconds() / 60
                    quiz_minutes += max(1, int(duration))  # At least 1 min per quiz

            # Flashcards: no tracking, set to 0
            flashcard_minutes = 0

            cert_days.append({
                'date': day.strftime('%Y-%m-%d'),
                'resources': video_minutes,
                'quizzes': quiz_minutes,
                'flashcards': flashcard_minutes,
            })
        weekly_study[cert.id] = {
            'title': cert.title,
            'days': cert_days
        }

    # Get notifications
    notifications = _get_user_notifications(request.user)

    return render(request, 'mycertifications.html', {
        'certifications': active_certifications,
        'all_certifications': all_certifications,
        'user': request.user,
        'weekly_study': weekly_study,
        'notifications': notifications,
    })

@login_required
def resources(request):
    # Only show resources for certifications the user is subscribed to
    user_cert_ids = Subscription.objects.filter(user=request.user, active=True).values_list('certification_id', flat=True)
    resources = Resource.objects.select_related('certification').filter(certification__id__in=user_cert_ids).order_by('-created_at')
    certifications = Certification.objects.filter(id__in=user_cert_ids)
    # Restrict types to images, pdfs, and videos only
    types = [
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('image', 'Image'),
    ]

    cert_filter = request.GET.get('cert')
    type_filter = request.GET.get('type')
    if cert_filter:
        resources = resources.filter(certification__id=cert_filter)
    if type_filter:
        resources = resources.filter(type=type_filter)

    # Handle POST for marking video as watched
    if request.method == 'POST' and request.POST.get('mark_watched_id'):
        resource_id = request.POST.get('mark_watched_id')
        resource = get_object_or_404(Resource, id=resource_id, type='video')
        VideoView.objects.get_or_create(user=request.user, resource=resource)
        return JsonResponse({'status': 'ok'})

    # Get watched videos for this user
    watched_videos = set(VideoView.objects.filter(user=request.user).values_list('resource_id', flat=True))

    # Get notifications
    notifications = _get_user_notifications(request.user)

    return render(request, 'resources.html', {
        'resources': resources,
        'certifications': certifications,
        'types': types,
        'cert_filter': cert_filter,
        'type_filter': type_filter,
        'watched_videos': watched_videos,
        'notifications': notifications,
    })

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def reset_confirm_page(request, uidb64, token):
    return render(request, 'reset_confirm.html', context={
        'uidb64': uidb64,
        'token': token,
    })

@login_required
def flashcards(request):
    # Get user's active certifications
    user_cert_ids = Subscription.objects.filter(
        user=request.user,
        active=True
    ).values_list('certification_id', flat=True)

    certifications = Certification.objects.filter(id__in=user_cert_ids)

    # Get all flashcards for user's certifications
    flashcards = Flashcard.objects.filter(
        certification__in=certifications
    ).select_related('certification').order_by('-created_at')

    # Get recent flashcards (last 6)
    recent_flashcards = flashcards[:6]

    # Get unique topics and their counts
    topics = flashcards.exclude(topic__isnull=True).values('topic').annotate(
        count=Count('id')
    ).order_by('-count')

    # Add flashcard counts and JSON to certifications
    for cert in certifications:
        cert.flashcards_count = cert.flashcards.count()
        cert.flashcards_json = json.dumps([
            {
                'id': card.id,
                'front_text': card.front_text,
                'back_text': card.back_text,
                'topic': card.topic or '',
            }
            for card in cert.flashcards.all()
        ], cls=DjangoJSONEncoder)
        # Get recent users studying this certification (last 3)
        cert.recent_users = User.objects.filter(
            subscriptions__certification=cert,  # Changed from subscription to subscriptions
            subscriptions__active=True
        ).distinct()[:3]
        cert.users_count = cert.recent_users.count()

    notifications = _get_user_notifications(request.user)
    return render(request, 'flashcards.html', {
        'certifications': certifications,
        'recent_flashcards': recent_flashcards,
        'topics': topics,
        'user': request.user,
        'notifications': notifications,
    })

@login_required
def quizzes(request):
    # Get all quizzes for certifications the user is subscribed to
    user_subscriptions = Subscription.objects.filter(
        user=request.user,
        active=True
    ).values_list('certification_id', flat=True)

    quizzes = Quiz.objects.filter(
        certification_id__in=user_subscriptions
    ).select_related('certification').prefetch_related('questions')

    # Get user's quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-start_time')

    # Calculate statistics for each quiz
    for quiz in quizzes:
        # Get user's attempts for this quiz
        user_quiz_attempts = quiz_attempts.filter(quiz=quiz)

        # Calculate average score
        quiz.avg_score = user_quiz_attempts.aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0

        # Get best attempt
        quiz.best_attempt = user_quiz_attempts.order_by('-score').first()

        # Get total attempts
        quiz.total_attempts = user_quiz_attempts.count()

        # Get completion rate
        quiz.completion_rate = (user_quiz_attempts.filter(
            completed=True
        ).count() / quiz.total_attempts * 100) if quiz.total_attempts > 0 else 0

        # Calculate last question index
        quiz.last_question_index = quiz.questions.count() - 1

        # Get recent attempts for this quiz
        quiz.recent_attempts = user_quiz_attempts[:5]

        # Calculate time taken for each attempt
        for attempt in quiz.recent_attempts:
            if attempt.end_time:
                attempt.time_taken = attempt.end_time - attempt.start_time
            else:
                attempt.time_taken = None

    # Get recent activity across all quizzes
    recent_activity = quiz_attempts[:5]
    for attempt in recent_activity:
        if attempt.end_time:
            attempt.time_taken = attempt.end_time - attempt.start_time
        else:
            attempt.time_taken = None

    # Get recommended quizzes based on user's performance
    recommended_quizzes = Quiz.objects.filter(
        certification_id__in=user_subscriptions
    ).exclude(
        id__in=quizzes.values_list('id', flat=True)
    ).select_related('certification')[:3]

    # Calculate user statistics
    user_stats = {
        'overall_progress': 65,  # This should be calculated based on all certifications
        'tasks_total': 7,
        'tasks_completed': 3,
        'streak': 14,
        'quiz_average': quiz_attempts.aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0
    }

    # Get study plan
    study_plan = [
        {
            'id': 1,
            'time': '09:00 AM',
            'title': 'GRE Verbal Practice',
            'duration': '45 min',
            'activity': 'Quiz',
            'status': 'Completed'
        },
        {
            'id': 2,
            'time': '11:00 AM',
            'title': 'LSAT Logic Games',
            'duration': '60 min',
            'activity': 'Practice',
            'status': 'In Progress'
        },
        {
            'id': 3,
            'time': '02:00 PM',
            'title': 'CFA Ethics Review',
            'duration': '30 min',
            'activity': 'Reading',
            'status': 'Upcoming'
        }
    ]

    notifications = _get_user_notifications(request.user)
    return render(request, 'quizzes.html', {
        'quizzes': quizzes,
        'quiz_attempts': quiz_attempts,
        'recent_activity': recent_activity,
        'recommended_quizzes': recommended_quizzes,
        'user': request.user,
        'user_stats': user_stats,
        'study_plan': study_plan,
        'notifications': notifications,
    })

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    ).order_by('-start_time')
    avg_score = quiz_attempts.aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0
    best_attempt = quiz_attempts.order_by('-score').first()
    notifications = _get_user_notifications(request.user)
    return render(request, 'quiz_detail.html', {
        'quiz': quiz,
        'quiz_attempts': quiz_attempts,
        'avg_score': avg_score,
        'best_attempt': best_attempt,
        'user': request.user,
        'notifications': notifications,
    })

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions'), id=quiz_id)
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        start_time=timezone.now()
    )
    notifications = _get_user_notifications(request.user)
    return render(request, 'quiz_take.html', {
        'quiz': quiz,
        'attempt': attempt,
        'user': request.user,
        'notifications': notifications,
    })

@login_required
def submit_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)

    if request.method == 'POST':
        # Calculate score
        correct_answers = 0
        total_questions = attempt.quiz.questions.count()
        user_answers = {}

        for question in attempt.quiz.questions.all():
            user_answer = request.POST.get(f'question_{question.id}')
            user_answers[str(question.id)] = user_answer  # Store as string for JSON compatibility
            if user_answer == question.correct_answer:
                correct_answers += 1

        # Update attempt
        attempt.end_time = timezone.now()
        attempt.score = (correct_answers / total_questions) * 100
        attempt.completed = True
        attempt.user_answers = user_answers  # Save answers
        attempt.save()

        return redirect('quiz_results', attempt_id=attempt.id)

    return render(request, 'quiz_take.html', {
        'quiz': attempt.quiz,
        'attempt': attempt,
        'user': request.user
    })

@login_required
def certification_detail(request, cert_id):
    certification = get_object_or_404(Certification, id=cert_id)

    # Get all quizzes for this certification
    quizzes = Quiz.objects.filter(certification=certification).select_related('certification')

    # Get user's quiz attempts for this certification
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz__in=quizzes
    ).select_related('quiz').order_by('-start_time')

    # Calculate statistics
    total_quizzes = quizzes.count()
    completed_quizzes = quiz_attempts.filter(completed=True).values('quiz').distinct().count()
    progress = (completed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0

    # Get average score
    avg_score = quiz_attempts.aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0

    # Get recent attempts
    recent_attempts = quiz_attempts[:5]

    # Check if user is subscribed
    is_subscribed = Subscription.objects.filter(
        user=request.user,
        certification=certification,
        active=True
    ).exists()

    return render(request, 'certification_detail.html', {
        'certification': certification,
        'quizzes': quizzes,
        'progress': progress,
        'avg_score': avg_score,
        'recent_attempts': recent_attempts,
        'is_subscribed': is_subscribed,
        'user': request.user
    })

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    quiz = attempt.quiz
    questions = quiz.questions.all()
    user_answers = getattr(attempt, 'user_answers', {}) or {}
    notifications = _get_user_notifications(request.user)
    return render(request, 'quiz_results.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'user': request.user,
        'user_answers': user_answers,
        'notifications': notifications,
    })

def discussions(request):
    # Get notifications
    notifications = _get_user_notifications(request.user)

    # Get all posts with related user and certification
    posts_qs = Post.objects.select_related('user', 'certification').prefetch_related('comments', 'likes')

    # Only show posts from certifications the user is subscribed to
    if request.user.is_authenticated:
        user_cert_ids = Subscription.objects.filter(user=request.user, active=True).values_list('certification_id', flat=True)
        posts_qs = posts_qs.filter(certification_id__in=user_cert_ids)
        certifications = Certification.objects.filter(id__in=user_cert_ids)
        liked_posts = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    else:
        posts_qs = Post.objects.none()  # Return empty queryset for non-authenticated users
        certifications = Certification.objects.none()
        liked_posts = set()

    paginator = Paginator(posts_qs, 5)  # 5 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    user = request.user if request.user.is_authenticated else None
    return render(request, 'discussions.html', {
        'posts': posts,
        'certifications': certifications,
        'user': user,
        'liked_posts': liked_posts,
        'paginator': paginator,
        'notifications': notifications,
    })

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'like_count': post.likes.count()})

@login_required
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        certification_id = request.POST.get('certification')

        if not (title and body and certification_id):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required.'
                }, status=400)
            return redirect('discussions')

        post = Post.objects.create(
            user=request.user,
            title=title,
            body=body,
            certification_id=certification_id
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Post created successfully!',
                'post_id': post.id
            })

        return redirect('discussions')
    return redirect('discussions')

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user', 'certification').prefetch_related('comments__user'), id=post_id)
    return render(request, 'post_detail.html', {'post': post, 'user': request.user})

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    body = request.POST.get('body')
    if body:
        comment = Comment.objects.create(post=post, user=request.user, body=body)
        html = render_to_string('partials/comment.html', {'comment': comment, 'user': request.user})
        return JsonResponse({'success': True, 'html': html, 'comment_id': comment.id})
    return JsonResponse({'success': False, 'error': 'No content'})

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    return JsonResponse({'success': True})

@login_required
@require_POST
def update_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    title = request.POST.get('title')
    body = request.POST.get('body')
    if title and body:
        post.title = title
        post.body = body
        post.save()
        return JsonResponse({'success': True, 'title': post.title, 'body': post.body})
    return JsonResponse({'success': False, 'error': 'Missing fields'})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return JsonResponse({'success': True})

@login_required
@require_POST
def update_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    body = request.POST.get('body')
    if body:
        comment.body = body
        comment.save()
        return JsonResponse({'success': True, 'body': comment.body})
    return JsonResponse({'success': False, 'error': 'Missing body'})

@login_required
@csrf_exempt
@require_POST
def create_study_plan(request):
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['title', 'certification', 'activity_type', 'scheduled_date', 'scheduled_time', 'duration']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required.'
                }, status=400)

        # Create study plan
        study_plan = StudyPlan.objects.create(
            user=request.user,
            certification_id=data['certification'],
            title=data['title'],
            activity_type=data['activity_type'],
            scheduled_date=data['scheduled_date'],
            scheduled_time=data['scheduled_time'],
            duration=data['duration'],
            notes=data.get('notes', ''),
            status='scheduled'
        )

        # Ensure scheduled_time is a time object before calling strftime
        scheduled_time = study_plan.scheduled_time
        if isinstance(scheduled_time, str):
            try:
                scheduled_time = datetime.strptime(scheduled_time, '%H:%M').time()
            except ValueError:
                try:
                    scheduled_time = datetime.strptime(scheduled_time, '%H:%M:%S').time()
                except Exception:
                    scheduled_time = None
        time_str = scheduled_time.strftime('%I:%M %p') if scheduled_time else str(study_plan.scheduled_time)

        return JsonResponse({
            'success': True,
            'message': 'Study plan created successfully!',
            'study_plan': {
                'id': study_plan.id,
                'title': study_plan.title,
                'time': time_str,
                'duration': f"{study_plan.duration} min",
                'activity': study_plan.get_activity_type_display(),
                'status': study_plan.status.replace('_', ' ').title()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

def _humanize_time(delta):
    if isinstance(delta, str):
        return delta
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    minutes = delta.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    return "Just now"

@login_required
@require_http_methods(["GET", "POST"])
def certification_view(request, cert_id):
    certification = get_object_or_404(Certification, id=cert_id)
    if request.method == "POST":
        # Subscribe the user if not already subscribed
        from accounts.models import Subscription
        if not Subscription.objects.filter(user=request.user, certification=certification, active=True).exists():
            Subscription.objects.create(user=request.user, certification=certification, plan='monthly', active=True)
        return redirect('mycertifications')
    return render(request, 'certification.html', {
        'certification': certification,
        'user': request.user
    })

def notification_dropdown_view(request):
    user = request.user
    # --- Get notifications (same as dashboard) ---
    notifications = _get_user_notifications(user)
    return render(request, 'partials/notification_dropdown.html', {'notifications': notifications})

@login_required
def create_flashcard(request):
    if request.method == 'POST':
        certification_id = request.POST.get('certification')
        front_text = request.POST.get('front_text')
        back_text = request.POST.get('back_text')
        topic = request.POST.get('topic', '')

        try:
            cert = Certification.objects.get(id=certification_id)
            # Ensure user is subscribed
            if not Subscription.objects.filter(user=request.user, certification=cert, active=True).exists():
                return JsonResponse({'success': False, 'message': 'You must be subscribed to this certification.'})

            Flashcard.objects.create(
                certification=cert,
                front_text=front_text,
                back_text=back_text,
                topic=topic
            )
            return JsonResponse({'success': True, 'message': 'Flashcard created successfully.'})
        except Certification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Certification not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # GET request
    user_cert_ids = Subscription.objects.filter(
        user=request.user,
        active=True
    ).values_list('certification_id', flat=True)

    certifications = Certification.objects.filter(id__in=user_cert_ids)
    notifications = _get_user_notifications(request.user)

    return render(request, 'create_flashcard.html', {
        'certifications': certifications,
        'user': request.user,
        'notifications': notifications,
    })

import random
import os
import json
from django.conf import settings
try:
    from openai import OpenAI
    client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', 'dummy'))
except ImportError:
    client = None

@login_required
@require_POST
def ai_generate(request):
    """
    A generic endpoint for AI generation.
    Expects JSON data:
    {
        "type": "flashcards", # or "quiz", "resource", "study_plan", etc.
        "prompt": "Create flashcards about AWS S3.",
        "certification_id": 1, # optional context
        "count": 5 # optional
    }
    """
    import PyPDF2

    try:
        # Check if form data is used (for file uploads)
        if request.content_type.startswith('multipart/form-data'):
            gen_type = request.POST.get('type')
            prompt = request.POST.get('prompt', '')
            cert_id = request.POST.get('certification_id')
            count = int(request.POST.get('count', 3))

            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                if uploaded_file.name.endswith('.pdf'):
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in pdf_reader.pages[:5]: # limiting to first 5 pages for brevity
                        text += page.extract_text()
                    prompt = f"Based on this document text: {text[:2000]}... generate flashcards."
                else:
                    return JsonResponse({"success": False, "message": "Only PDF files are supported currently."})
            data = {"type": gen_type, "prompt": prompt, "certification_id": cert_id, "count": count}
        else:
            data = json.loads(request.body)
            gen_type = data.get('type')
            prompt = data.get('prompt', '')
            cert_id = data.get('certification_id')

        context_cert = ""
        if cert_id:
            try:
                cert = Certification.objects.get(id=cert_id)
                context_cert = f" Context: The user is studying for {cert.title} certification."
            except Certification.DoesNotExist:
                pass

        if client and client.api_key and client.api_key != "dummy_key_for_tests" and client.api_key != "dummy":
            try:
                # Real OpenAI Integration
                if gen_type == 'flashcards':
                    count = data.get('count', 3)
                    sys_prompt = f"You are an expert tutor.{context_cert} Generate {count} flashcards based on this prompt: {prompt}. Return ONLY a JSON array of objects with keys: 'front_text', 'back_text', 'topic'."
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": sys_prompt}],
                        temperature=0.7
                    )
                    content = response.choices[0].message.content
                    cards = json.loads(content)
                    return JsonResponse({"success": True, "data": cards})

                elif gen_type == 'resource':
                    sys_prompt = f"You are an expert tutor.{context_cert} Create a comprehensive study guide in HTML format for the topic: {prompt}. Do not include ```html blocks, just raw HTML."
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": sys_prompt}],
                        temperature=0.7
                    )
                    html_content = response.choices[0].message.content
                    if cert_id:
                        cert = Certification.objects.get(id=cert_id)
                        resource = Resource.objects.create(
                            certification=cert,
                            title=f"{prompt[:30]} Study Guide",
                            type='pdf',
                            created_by_ai=True
                        )
                        # We would normally save HTML to PDF here or just save as text/html resource.
                        # For now, we will just return success.
                        return JsonResponse({"success": True, "message": "Resource created successfully", "resource_id": resource.id, "content": html_content})
                    return JsonResponse({"success": True, "content": html_content})

                elif gen_type == 'quiz':
                    sys_prompt = f"You are an expert tutor.{context_cert} Generate a multiple-choice quiz question for the topic: {prompt}. Return ONLY a JSON object with keys: 'question_text', 'options' (array of 4 strings), 'correct_answer' (one of the options), 'explanation'."
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": sys_prompt}],
                        temperature=0.7
                    )
                    content = response.choices[0].message.content
                    question = json.loads(content)
                    return JsonResponse({"success": True, "data": [question]})

                else:
                    return JsonResponse({"success": False, "message": "Unsupported generation type."})
            except Exception as e:
                # Fallback to mock if API fails
                pass

        # Fallback Mock Logic (When API key is dummy or request fails)
        if gen_type == 'flashcards':
            count = data.get('count', 3)
            cards = []
            for i in range(count):
                cards.append({
                    "front_text": f"[AI Generated] What is the primary concept of {prompt}?",
                    "back_text": f"The answer to {prompt} is fundamental to {context_cert.replace('Context: ', '') if context_cert else 'the topic'}.",
                    "topic": "AI Concept"
                })
            return JsonResponse({"success": True, "data": cards})

        elif gen_type == 'resource':
            content = f"<h1>{prompt} Study Guide</h1><p>This is a detailed AI-generated guide for {prompt}.{context_cert}</p>"
            if cert_id:
                cert = Certification.objects.get(id=cert_id)
                resource = Resource.objects.create(
                    certification=cert,
                    title=f"Study Guide: {prompt}",
                    type='pdf',
                    created_by_ai=True
                )
                return JsonResponse({"success": True, "message": "Resource created successfully", "resource_id": resource.id})
            return JsonResponse({"success": True, "content": content})

        elif gen_type == 'quiz':
            questions = [
                {
                    "question_text": f"Which of the following best describes {prompt}?",
                    "options": ["A core component", "A deprecated feature", "An external library", "None of the above"],
                    "correct_answer": "A core component",
                    "explanation": f"This is the accepted industry standard regarding {prompt}."
                }
            ]
            return JsonResponse({"success": True, "data": questions})

        else:
            return JsonResponse({"success": False, "message": "Unsupported generation type."})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@login_required
def record_lecture_view(request):
    notifications = _get_user_notifications(request.user)
    return render(request, 'record_lecture.html', {
        'user': request.user,
        'notifications': notifications,
    })

@login_required
@require_POST
def ai_transcribe(request):
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({"success": False, "message": "No audio file uploaded."})

        audio_file = request.FILES['audio']

        # Determine if we can use real API
        if client and client.api_key and client.api_key != "dummy_key_for_tests" and client.api_key != "dummy":
            try:
                # Save file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    for chunk in audio_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # Transcribe with Whisper
                with open(tmp_path, "rb") as f:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
                transcription = transcript_response.text
                os.unlink(tmp_path)

                # Process with GPT to get notes, quiz, resources
                sys_prompt = "You are an AI teaching assistant. Extract key notes, create one multiple-choice quiz question, and suggest 2 real external web resources (with title and URL) based on the following lecture transcript. Return ONLY a JSON object with keys: 'key_notes' (array of strings), 'quiz' (array with one object containing 'question', 'options' array, 'answer'), and 'resources' (array of objects with 'title' and 'url')."

                gpt_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": transcription}
                    ],
                    temperature=0.7
                )

                analysis = json.loads(gpt_response.choices[0].message.content)

                return JsonResponse({
                    "success": True,
                    "transcription": transcription,
                    "key_notes": analysis.get('key_notes', []),
                    "quiz": analysis.get('quiz', []),
                    "resources": analysis.get('resources', [])
                })
            except Exception as e:
                # Fallback to mock if API fails
                print(f"OpenAI API failed: {e}")
                pass

        # Fallback Mock Logic
        mock_transcription = (
            "This is a mocked transcription of the uploaded lecture. "
            "The key concept discussed today is the OSI model, specifically the Network layer "
            "and how routers use IP addresses. We also covered security protocols."
        )

        mock_notes = [
            "Network layer is responsible for packet forwarding.",
            "Routers operate at the Network layer.",
            "Always check IP addressing schemas."
        ]

        mock_quiz = [
            {
                "question": "What layer do routers operate at?",
                "options": ["Physical", "Data Link", "Network", "Transport"],
                "answer": "Network"
            }
        ]

        mock_resources = [
            {"title": "Cisco OSI Model Guide", "url": "https://www.cisco.com"},
            {"title": "Wikipedia: Network Layer", "url": "https://en.wikipedia.org/wiki/Network_layer"}
        ]

        return JsonResponse({
            "success": True,
            "transcription": mock_transcription,
            "key_notes": mock_notes,
            "quiz": mock_quiz,
            "resources": mock_resources
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

def pricing_view(request):
    return render(request, 'pricing.html', {'settings': settings})

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@require_POST
def create_checkout_session(request):
    try:
        domain_url = 'http://127.0.0.1:8000/'
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=request.user.id if request.user.is_authenticated else None,
            success_url=domain_url + 'dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + 'pricing/',
            payment_method_types=['card'],
            mode='subscription',
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Pro Subscription',
                            'description': 'Unlimited AI Study Tools',
                        },
                        'unit_amount': 1900, # $19.00
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }
            ]
        )
        return JsonResponse({'id': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=403)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_dummy')
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get("client_reference_id")
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.is_subscribed = True # assuming User model has is_subscribed or we add it
                user.save()
            except User.DoesNotExist:
                pass
    return HttpResponse(status=200)

from quizzes.models import Question

@login_required
@require_POST
def generate_mock_exam(request):
    try:
        data = json.loads(request.body)
        cert_id = data.get('certification_id')
        question_count = int(data.get('count', 5))

        cert = Certification.objects.get(id=cert_id)

        sys_prompt = f"You are an expert tutor. Create a {question_count}-question multiple choice mock exam for the {cert.title} certification. Return ONLY a JSON array of objects, where each object has keys: 'question_text', 'options' (array of 4 strings), 'correct_answer', and 'explanation'."

        if client and client.api_key and client.api_key not in ["dummy_key_for_tests", "dummy"]:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": sys_prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content
            questions_data = json.loads(content)
        else:
            # Mock fallback
            questions_data = []
            for i in range(question_count):
                questions_data.append({
                    "question_text": f"Mock Exam Q{i+1} for {cert.title}?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Because it's a mock."
                })

        # Create a new Quiz
        quiz = Quiz.objects.create(
            title=f"AI Mock Exam: {cert.title}",
            description="Automatically generated mock exam.",
            certification=cert,
            time_limit=1800,
            passing_score=70
        )

        for idx, q in enumerate(questions_data):
            Question.objects.create(
                quiz=quiz,
                question_text=q['question_text'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation', ''),
                order=idx+1
            )

        return JsonResponse({"success": True, "quiz_id": quiz.id})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

import csv
from django.http import HttpResponse

@login_required
def export_flashcards(request, cert_id):
    try:
        cert = Certification.objects.get(id=cert_id)
        flashcards = Flashcard.objects.filter(certification=cert)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="flashcards_{cert.title}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Front', 'Back', 'Topic'])

        for fc in flashcards:
            writer.writerow([fc.front_text, fc.back_text, fc.topic])

        return response
    except Exception as e:
        return HttpResponse(str(e), status=400)
