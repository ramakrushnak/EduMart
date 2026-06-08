from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from django.contrib.auth import get_user_model

User = get_user_model()


@require_http_methods(["GET", "POST"])
def login_page(request):
    """Login page and handler."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.email}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")
    
    return render(request, "login.html")


@require_http_methods(["GET", "POST"])
def register_page(request):
    """Register page and handler."""
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        
        if not all([email, first_name, password, password_confirm]):
            messages.error(request, "All fields are required.")
            return render(request, "register.html")
        
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "register.html")
        
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                password=password,
            )
            login(request, user)
            messages.success(request, f"Welcome, {first_name}! Your account has been created.")
            return redirect("product_list")
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
    
    return render(request, "register.html")


def logout_page(request):
    """Logout handler."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")
