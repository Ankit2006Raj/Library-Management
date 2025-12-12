"""Authentication and user management views"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, AuditLog
from .forms import UserProfileForm, UserRegistrationForm


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                membership_type='Basic',
                max_books_allowed=5
            )
            # Log action
            AuditLog.objects.create(
                user=user,
                action='CREATE',
                model_name='User',
                object_id=user.id,
                description=f"New user registered: {user.username}",
                ip_address=get_client_ip(request)
            )
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'library/auth/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Log action
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    model_name='User',
                    object_id=user.id,
                    description=f"User logged in: {user.username}",
                    ip_address=get_client_ip(request)
                )
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'library/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout"""
    AuditLog.objects.create(
        user=request.user,
        action='LOGOUT',
        model_name='User',
        object_id=request.user.id,
        description=f"User logged out: {request.user.username}",
        ip_address=get_client_ip(request)
    )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    # Get user statistics
    from .models import BorrowRecord, Review, Wishlist
    borrowed_books = BorrowRecord.objects.filter(user=request.user, status='Borrowed')
    borrow_history = BorrowRecord.objects.filter(user=request.user).order_by('-borrow_date')[:10]
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')[:5]
    wishlist = Wishlist.objects.filter(user=request.user).order_by('-added_date')[:5]
    
    context = {
        'form': form,
        'profile': profile,
        'borrowed_books': borrowed_books,
        'borrow_history': borrow_history,
        'reviews': reviews,
        'wishlist': wishlist,
    }
    return render(request, 'library/auth/profile.html', context)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
