from django.shortcuts import render

def landing_page(request):
    return render(request, 'landing_page.html')

def login_page(request):
    return render(request, 'login.html')

def signup_page(request):
    return render(request, 'signup.html')

def dashboard_page(request):
    return render(request, 'dashboard.html')

def forgot_password_page(request):
    return render(request, 'forgot_password.html')

def reset_confirm_page(request, uidb64, token):
    return render(request, 'reset_confirm.html', context={
        'uidb64': uidb64,
        'token': token,
    })
