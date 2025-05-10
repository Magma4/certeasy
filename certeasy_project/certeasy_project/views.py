from django.shortcuts import render, get_object_or_404, redirect
from certifications.models import Certification
from django.contrib.auth.decorators import login_required
from accounts.models import Subscription
from quizzes.models import Quiz, QuizAttempt
from django.db.models import Avg, Count
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from resources.models import Resource, VideoView
from discussions.models import Post, Like, Comment
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

def landing_page(request):
    return render(request, 'landing_page.html')

def login_page(request):
    return render(request, 'login.html')

def signup_page(request):
    return render(request, 'signup.html')

@login_required
def dashboard_page(request):
    # Get user's active certifications
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        active=True
    ).select_related('certification')

    # Get all certifications for the slider
    certifications = Certification.objects.all()

    # Calculate overall progress based on quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        completed=True
    ).select_related('quiz')

    # Calculate progress for each certification
    total_progress = 0
    for sub in active_subscriptions:
        # Get all quizzes for this certification
        cert_quizzes = Quiz.objects.filter(certification=sub.certification)
        total_quizzes = cert_quizzes.count()

        if total_quizzes > 0:
            # Get completed quizzes for this certification
            completed_quizzes = quiz_attempts.filter(
                quiz__in=cert_quizzes
            ).values('quiz').distinct().count()

            # Calculate progress percentage
            cert_progress = (completed_quizzes / total_quizzes) * 100
            total_progress += cert_progress

    # Calculate average progress across all certifications
    overall_progress = (total_progress / len(active_subscriptions)) if active_subscriptions else 0

    # Calculate quiz average
    quiz_average = quiz_attempts.aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0

    # Get user's study streak (consecutive days of activity)
    today = timezone.now().date()
    streak = 0
    current_date = today
    while True:
        has_activity = quiz_attempts.filter(
            start_time__date=current_date
        ).exists()
        if not has_activity:
            break
        streak += 1
        current_date -= timezone.timedelta(days=1)

    # Get today's tasks
    today_tasks = [
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

    # Get notifications
    notifications = [
        {
            'id': 1,
            'title': 'New quiz available',
            'time': '2 hours ago',
            'type': 'resource',
            'icon': 'book-open'
        },
        {
            'id': 2,
            'title': 'Study group meeting',
            'time': 'Yesterday',
            'type': 'calendar',
            'icon': 'calendar'
        },
        {
            'id': 3,
            'title': 'New flashcards added',
            'time': '2 days ago',
            'type': 'resource',
            'icon': 'brain'
        }
    ]

    # Get recent activity
    recent_activity = quiz_attempts.order_by('-start_time')[:4]

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
        'overall_progress': round(overall_progress, 1),
        'tasks_total': len(today_tasks),
        'tasks_completed': len([task for task in today_tasks if task['status'] == 'Completed']),
        'streak': streak,
        'quiz_average': round(quiz_average, 1)
    }

    # Add progress to each certification for the slider
    for cert in certifications:
        cert_quizzes = Quiz.objects.filter(certification=cert)
        total_quizzes = cert_quizzes.count()
        if total_quizzes > 0:
            completed_quizzes = quiz_attempts.filter(
                quiz__in=cert_quizzes,
                completed=True
            ).values('quiz').distinct().count()
            cert.progress = (completed_quizzes / total_quizzes) * 100
        else:
            cert.progress = 0

    return render(request, 'dashboard.html', {
        'user': request.user,
        'certifications': certifications,
        'user_stats': user_stats,
        'notifications': notifications,
        'study_plan': today_tasks,
        'recent_activity': recent_activity,
        'upcoming_exams': upcoming_exams
    })

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

    return render(request, 'mycertifications.html', {
        'certifications': active_certifications,
        'all_certifications': all_certifications,
        'user': request.user
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

    return render(request, 'resources.html', {
        'resources': resources,
        'certifications': certifications,
        'types': types,
        'cert_filter': cert_filter,
        'type_filter': type_filter,
        'watched_videos': watched_videos,
    })

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def reset_confirm_page(request, uidb64, token):
    return render(request, 'reset_confirm.html', context={
        'uidb64': uidb64,
        'token': token,
    })

def flashcards(request):
    return render(request, 'flashcards.html')

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

    # Get notifications
    notifications = [
        {
            'id': 1,
            'title': 'New quiz available',
            'time': '2 hours ago',
            'type': 'resource',
            'icon': 'book-open'
        },
        {
            'id': 2,
            'title': 'Study group meeting',
            'time': 'Yesterday',
            'type': 'calendar',
            'icon': 'calendar'
        },
        {
            'id': 3,
            'title': 'New flashcards added',
            'time': '2 days ago',
            'type': 'resource',
            'icon': 'brain'
        }
    ]

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

    return render(request, 'quizzes.html', {
        'quizzes': quizzes,
        'quiz_attempts': quiz_attempts,
        'recent_activity': recent_activity,
        'recommended_quizzes': recommended_quizzes,
        'user': request.user,
        'user_stats': user_stats,
        'notifications': notifications,
        'study_plan': study_plan
    })

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Get user's previous attempts for this quiz
    quiz_attempts = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    ).order_by('-start_time')

    # Get average score for this quiz
    avg_score = quiz_attempts.aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0

    # Get best attempt
    best_attempt = quiz_attempts.order_by('-score').first()

    return render(request, 'quiz_detail.html', {
        'quiz': quiz,
        'quiz_attempts': quiz_attempts,
        'avg_score': avg_score,
        'best_attempt': best_attempt,
        'user': request.user
    })

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions'), id=quiz_id)

    # Create a new quiz attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        start_time=timezone.now()
    )

    return render(request, 'quiz_take.html', {
        'quiz': quiz,
        'attempt': attempt,
        'user': request.user
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
    # Assume user_answers is a dict: {question_id: answer}
    user_answers = getattr(attempt, 'user_answers', {}) or {}
    return render(request, 'quiz_results.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'user': request.user,
        'user_answers': user_answers,
    })

def discussions(request):
    # Get all posts with related user and certification
    posts_qs = Post.objects.select_related('user', 'certification').prefetch_related('comments', 'likes')
    paginator = Paginator(posts_qs, 5)  # 5 posts per page
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    # Only certifications the user is subscribed to
    if request.user.is_authenticated:
        user_cert_ids = Subscription.objects.filter(user=request.user, active=True).values_list('certification_id', flat=True)
        certifications = Certification.objects.filter(id__in=user_cert_ids)
        liked_posts = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    else:
        certifications = Certification.objects.none()
        liked_posts = set()

    user = request.user if request.user.is_authenticated else None
    notifications = [
        {
            'id': 1,
            'title': 'New reply to your post',
            'time': '1 hour ago',
            'type': 'comment',
            'icon': 'comment'
        },
        {
            'id': 2,
            'title': 'Your post was upvoted',
            'time': 'Yesterday',
            'type': 'like',
            'icon': 'thumbs-up'
        },
        {
            'id': 3,
            'title': 'New post in GRE',
            'time': '2 days ago',
            'type': 'resource',
            'icon': 'book-open'
        }
    ]
    return render(request, 'discussions.html', {
        'posts': posts,
        'certifications': certifications,
        'user': user,
        'notifications': notifications,
        'liked_posts': liked_posts,
        'paginator': paginator,
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
        if title and body and certification_id:
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
