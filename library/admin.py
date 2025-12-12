from django.contrib import admin
from .models import (
    Book, UserProfile, BorrowRecord, Reservation, 
    Review, Wishlist, AuditLog, Notification
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'copies_available', 'rating', 'created_at')
    list_filter = ('category', 'status', 'language', 'published_year')
    search_fields = ('title', 'author', 'isbn', 'publisher')
    list_per_page = 25
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'published_year', 'category', 'cover_image')
        }),
        ('Publication Details', {
            'fields': ('isbn', 'publisher', 'language', 'pages', 'edition', 'barcode')
        }),
        ('Description', {
            'fields': ('description', 'tags')
        }),
        ('Library Management', {
            'fields': ('status', 'copies_available', 'total_copies', 'shelf_location')
        }),
        ('Rating', {
            'fields': ('rating',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_type', 'is_active_member', 'total_fines', 'membership_date')
    list_filter = ('membership_type', 'is_active_member', 'membership_date')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('membership_date',)
    list_editable = ('is_active_member',)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'borrow_date', 'due_date', 'status', 'fine_amount', 'fine_paid')
    list_filter = ('status', 'fine_paid', 'borrow_date', 'due_date')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('borrow_date',)
    list_editable = ('status', 'fine_paid')
    date_hierarchy = 'borrow_date'
    
    fieldsets = (
        ('Borrow Information', {
            'fields': ('user', 'book', 'borrow_date', 'due_date', 'return_date')
        }),
        ('Status & Fines', {
            'fields': ('status', 'fine_amount', 'fine_paid')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'reservation_date', 'expiry_date', 'status', 'notified')
    list_filter = ('status', 'notified', 'reservation_date')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('reservation_date',)
    list_editable = ('status', 'notified')
    date_hierarchy = 'reservation_date'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'title', 'is_verified_borrower', 'created_at')
    list_filter = ('rating', 'is_verified_borrower', 'created_at')
    search_fields = ('user__username', 'book__title', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at', 'is_verified_borrower')
    date_hierarchy = 'created_at'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'priority', 'added_date', 'notified_when_available')
    list_filter = ('priority', 'notified_when_available', 'added_date')
    search_fields = ('user__username', 'book__title')
    readonly_fields = ('added_date',)
    list_editable = ('priority',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'
