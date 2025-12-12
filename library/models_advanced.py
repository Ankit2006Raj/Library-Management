"""
Advanced Models for Industry-Level Features
Multi-tenancy, Activity Feed, Payment, and more
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class LibraryBranch(models.Model):
    """Support for multiple library branches (Multi-tenancy)"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_branches')
    is_active = models.BooleanField(default=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Library Branches"
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ActivityFeed(models.Model):
    """Social activity feed for user actions"""
    ACTIVITY_TYPES = [
        ('BORROW', 'Borrowed a book'),
        ('RETURN', 'Returned a book'),
        ('REVIEW', 'Reviewed a book'),
        ('WISHLIST', 'Added to wishlist'),
        ('ACHIEVEMENT', 'Earned achievement'),
        ('FOLLOW', 'Followed user'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    book = models.ForeignKey('Book', on_delete=models.CASCADE, null=True, blank=True)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='targeted_activities')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"


class UserFollowing(models.Model):
    """User following system for social features"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Achievement(models.Model):
    """Gamification - User achievements and badges"""
    ACHIEVEMENT_TYPES = [
        ('BOOKS_READ', 'Books Read'),
        ('REVIEWS_WRITTEN', 'Reviews Written'),
        ('ON_TIME_RETURNS', 'On-Time Returns'),
        ('STREAK', 'Reading Streak'),
        ('CATEGORY_MASTER', 'Category Master'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    icon = models.CharField(max_length=50, help_text="Icon class or emoji")
    requirement = models.IntegerField(help_text="Number required to unlock")
    points = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Track user achievements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)
    is_unlocked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class Payment(models.Model):
    """Payment tracking for fines and fees"""
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_METHOD = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('ONLINE', 'Online Payment'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField()
    borrow_record = models.ForeignKey('BorrowRecord', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.status}"


class ReadingList(models.Model):
    """Curated reading lists"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_lists')
    books = models.ManyToManyField('Book', related_name='in_reading_lists')
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class BookRequest(models.Model):
    """Users can request books not in library"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_requests')
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    publisher = models.CharField(max_length=150, blank=True, null=True)
    reason = models.TextField(help_text="Why do you want this book?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True, null=True)
    votes = models.IntegerField(default=0, help_text="Number of users who want this book")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-votes', '-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.author} - {self.status}"


class BookRequestVote(models.Model):
    """Users can vote for book requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_request = models.ForeignKey(BookRequest, on_delete=models.CASCADE, related_name='user_votes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'book_request']
    
    def __str__(self):
        return f"{self.user.username} voted for {self.book_request.title}"


class LibraryEvent(models.Model):
    """Library events and programs"""
    EVENT_TYPES = [
        ('WORKSHOP', 'Workshop'),
        ('BOOK_CLUB', 'Book Club'),
        ('AUTHOR_MEET', 'Author Meet'),
        ('READING_SESSION', 'Reading Session'),
        ('EXHIBITION', 'Exhibition'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    max_participants = models.IntegerField(null=True, blank=True)
    is_registration_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.date()}"


class EventRegistration(models.Model):
    """Track event registrations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    event = models.ForeignKey(LibraryEvent, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'category']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


class SystemSettings(models.Model):
    """Configurable system settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(max_length=20, choices=[
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
    ], default='STRING')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"{self.key}: {self.value}"
