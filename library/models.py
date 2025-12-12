from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal

class Book(models.Model):
    CATEGORY_CHOICES = [
        ('Fiction', 'Fiction'),
        ('Non-Fiction', 'Non-Fiction'),
        ('Science', 'Science'),
        ('Technology', 'Technology'),
        ('History', 'History'),
        ('Biography', 'Biography'),
        ('Self-Help', 'Self-Help'),
        ('Fantasy', 'Fantasy'),
        ('Mystery', 'Mystery'),
        ('Romance', 'Romance'),
        ('Business', 'Business'),
        ('Philosophy', 'Philosophy'),
        ('Psychology', 'Psychology'),
        ('Education', 'Education'),
    ]
    
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Borrowed', 'Borrowed'),
        ('Reserved', 'Reserved'),
        ('Maintenance', 'Maintenance'),
    ]
    
    LANGUAGE_CHOICES = [
        ('English', 'English'),
        ('Spanish', 'Spanish'),
        ('French', 'French'),
        ('German', 'German'),
        ('Chinese', 'Chinese'),
        ('Japanese', 'Japanese'),
        ('Hindi', 'Hindi'),
        ('Other', 'Other'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200, verbose_name="Book Title", db_index=True)
    author = models.CharField(max_length=100, verbose_name="Author Name", db_index=True)
    published_year = models.IntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(datetime.now().year)
        ],
        verbose_name="Publication Year"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Fiction',
        verbose_name="Category",
        db_index=True
    )
    
    # Additional Details
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True, verbose_name="ISBN")
    publisher = models.CharField(max_length=150, blank=True, null=True, verbose_name="Publisher")
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='English', verbose_name="Language")
    pages = models.PositiveIntegerField(blank=True, null=True, verbose_name="Number of Pages")
    edition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Edition")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Library Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available', verbose_name="Status")
    copies_available = models.PositiveIntegerField(default=1, verbose_name="Copies Available")
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Total Copies")
    shelf_location = models.CharField(max_length=50, blank=True, null=True, verbose_name="Shelf Location")
    
    # Rating and Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                                 validators=[MinValueValidator(0), MaxValueValidator(5)],
                                 verbose_name="Rating")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Book"
        verbose_name_plural = "Books"
        indexes = [
            models.Index(fields=['title', 'author']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    @property
    def is_available(self):
        return self.status == 'Available' and self.copies_available > 0
    
    @property
    def availability_percentage(self):
        if self.total_copies == 0:
            return 0
        return (self.copies_available / self.total_copies) * 100
    
    # New fields for enhanced features
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, verbose_name="Cover Image")
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Barcode")
    tags = models.CharField(max_length=200, blank=True, null=True, help_text="Comma-separated tags")
    
    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return self.rating
    
    def get_total_reviews(self):
        """Get total number of reviews"""
        return self.reviews.count()



class UserProfile(models.Model):
    """Extended user profile for library members"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    membership_date = models.DateField(auto_now_add=True)
    membership_type = models.CharField(
        max_length=20,
        choices=[
            ('Basic', 'Basic'),
            ('Premium', 'Premium'),
            ('Student', 'Student'),
            ('Faculty', 'Faculty'),
        ],
        default='Basic'
    )
    max_books_allowed = models.PositiveIntegerField(default=5)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active_member = models.BooleanField(default=True)
    total_fines = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.user.username} - {self.membership_type}"
    
    def get_borrowed_books_count(self):
        return self.user.borrowings.filter(status='Borrowed').count()
    
    def can_borrow_more(self):
        return self.get_borrowed_books_count() < self.max_books_allowed


class BorrowRecord(models.Model):
    """Track book borrowing history"""
    STATUS_CHOICES = [
        ('Borrowed', 'Borrowed'),
        ('Returned', 'Returned'),
        ('Overdue', 'Overdue'),
        ('Lost', 'Lost'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_history')
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Borrowed')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-borrow_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
    
    def calculate_fine(self, fine_per_day=Decimal('1.00')):
        """Calculate fine for overdue books"""
        if self.status == 'Returned' and self.return_date:
            days_overdue = (self.return_date.date() - self.due_date).days
        elif self.status in ['Borrowed', 'Overdue']:
            days_overdue = (timezone.now().date() - self.due_date).days
        else:
            return Decimal('0.00')
        
        if days_overdue > 0:
            return Decimal(days_overdue) * fine_per_day
        return Decimal('0.00')
    
    def is_overdue(self):
        """Check if book is overdue"""
        if self.status == 'Borrowed' and timezone.now().date() > self.due_date:
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Auto-update status if overdue
        if self.is_overdue() and self.status == 'Borrowed':
            self.status = 'Overdue'
        # Calculate fine
        if self.status in ['Returned', 'Overdue']:
            self.fine_amount = self.calculate_fine()
        super().save(*args, **kwargs)


class Reservation(models.Model):
    """Book reservation system"""
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Fulfilled', 'Fulfilled'),
        ('Cancelled', 'Cancelled'),
        ('Expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    notified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-reservation_date']
        unique_together = ['user', 'book', 'status']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
    
    def is_expired(self):
        return timezone.now() > self.expiry_date and self.status == 'Active'
    
    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.expiry_date = timezone.now() + timedelta(days=7)
        if self.is_expired():
            self.status = 'Expired'
        super().save(*args, **kwargs)


class Review(models.Model):
    """Book reviews and ratings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    helpful_count = models.PositiveIntegerField(default=0)
    is_verified_borrower = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        # Check if user has borrowed this book
        has_borrowed = BorrowRecord.objects.filter(
            user=self.user,
            book=self.book,
            status='Returned'
        ).exists()
        self.is_verified_borrower = has_borrowed
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    """User wishlist for books"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_date = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('Low', 'Low'),
            ('Medium', 'Medium'),
            ('High', 'High'),
        ],
        default='Medium'
    )
    notes = models.TextField(blank=True, null=True)
    notified_when_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-added_date']
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"


class AuditLog(models.Model):
    """Audit trail for important actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('BORROW', 'Borrow'),
        ('RETURN', 'Return'),
        ('RESERVE', 'Reserve'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} at {self.timestamp}"


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('DUE_SOON', 'Due Soon'),
        ('OVERDUE', 'Overdue'),
        ('AVAILABLE', 'Book Available'),
        ('RESERVATION', 'Reservation'),
        ('FINE', 'Fine'),
        ('GENERAL', 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
