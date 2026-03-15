import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
import os
import json

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_mock')

def pricing_page(request):
    return render(request, 'pricing.html')

@login_required
def record_lecture_page(request):
    return render(request, 'record_lecture.html')

@login_required
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        price_id = data.get('priceId')

        if stripe.api_key == 'sk_test_mock':
            return JsonResponse({'url': '/dashboard/'})

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('dashboard')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('pricing')),
        )
        return JsonResponse({'url': checkout_session.url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
