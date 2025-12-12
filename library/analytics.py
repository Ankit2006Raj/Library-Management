"""
Advanced Analytics Module for Library Management System
Provides data analysis, insights, and reporting capabilities
"""
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from .models import Book, BorrowRecord, Review, Reservation, UserProfile, User


class LibraryAnalytics:
    """Comprehensive analytics for library operations"""
    
    @staticmethod
    def get_dashboard_metrics():
        """Get key performance indicators for dashboard"""
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        return {
            'total_books': Book.objects.count(),
            'total_users': User.objects.count(),
            'active_members': UserProfile.objects.filter(is_active_member=True).count(),
            'books_borrowed_today': BorrowRecord.objects.filter(
                borrow_date__date=today
            ).count(),
            'books_due_today': BorrowRecord.objects.filter(
                due_date=today,
                status='Borrowed'
            ).count(),
            'overdue_books': BorrowRecord.objects.filter(status='Overdue').count(),
            'total_fines_pending': BorrowRecord.objects.filter(
                fine_paid=False
            ).aggregate(total=Sum('fine_amount'))['total'] or 0,
            'books_borrowed_last_30_days': BorrowRecord.objects.filter(
                borrow_date__gte=last_30_days
            ).count(),
            'new_users_last_30_days': User.objects.filter(
                date_joined__gte=last_30_days
            ).count(),
            'average_rating': Book.objects.aggregate(
                avg=Avg('rating')
            )['avg'] or 0,
        }
    
    @staticmethod
    def get_borrowing_trends(days=30):
        """Get borrowing trends over time"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        trends = BorrowRecord.objects.filter(
            borrow_date__gte=start_date
        ).annotate(
            date=TruncDate('borrow_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return list(trends)
    
    @staticmethod
    def get_category_distribution():
        """Get book distribution by category"""
        return Book.objects.values('category').annotate(
            count=Count('id'),
            available=Count('id', filter=Q(status='Available')),
            borrowed=Count('id', filter=Q(status='Borrowed'))
        ).order_by('-count')
    
    @staticmethod
    def get_popular_books(limit=10):
        """Get most borrowed books"""
        return Book.objects.annotate(
            borrow_count=Count('borrow_history')
        ).order_by('-borrow_count')[:limit]
    
    @staticmethod
    def get_top_readers(limit=10):
        """Get users who borrowed most books"""
        return User.objects.annotate(
            books_borrowed=Count('borrowings')
        ).order_by('-books_borrowed')[:limit]
    
    @staticmethod
    def get_monthly_statistics(months=12):
        """Get monthly statistics for the past N months"""
        start_date = timezone.now().date() - timedelta(days=months*30)
        
        monthly_data = BorrowRecord.objects.filter(
            borrow_date__gte=start_date
        ).annotate(
            month=TruncMonth('borrow_date')
        ).values('month').annotate(
            borrowed=Count('id'),
            returned=Count('id', filter=Q(status='Returned')),
            overdue=Count('id', filter=Q(status='Overdue'))
        ).order_by('month')
        
        return list(monthly_data)
    
    @staticmethod
    def get_user_activity_score(user):
        """Calculate user engagement score"""
        profile = user.profile
        
        # Factors: books borrowed, reviews written, active membership
        books_borrowed = user.borrowings.count()
        reviews_written = user.reviews.count()
        wishlist_items = user.wishlist.count()
        on_time_returns = user.borrowings.filter(
            status='Returned',
            return_date__lte=F('due_date')
        ).count()
        
        # Calculate score (0-100)
        score = min(100, (
            books_borrowed * 5 +
            reviews_written * 10 +
            wishlist_items * 2 +
            on_time_returns * 3
        ))
        
        return {
            'score': score,
            'books_borrowed': books_borrowed,
            'reviews_written': reviews_written,
            'wishlist_items': wishlist_items,
            'on_time_returns': on_time_returns,
            'level': 'Gold' if score >= 80 else 'Silver' if score >= 50 else 'Bronze'
        }
    
    @staticmethod
    def get_book_performance(book):
        """Get detailed performance metrics for a book"""
        return {
            'total_borrows': book.borrow_history.count(),
            'current_borrows': book.borrow_history.filter(status='Borrowed').count(),
            'average_rating': book.get_average_rating(),
            'total_reviews': book.get_total_reviews(),
            'reservation_count': book.reservations.filter(status='Active').count(),
            'wishlist_count': book.wishlisted_by.count(),
            'return_rate': book.borrow_history.filter(status='Returned').count() / 
                          max(book.borrow_history.count(), 1) * 100,
        }
    
    @staticmethod
    def predict_book_demand(book):
        """Predict future demand for a book"""
        # Simple prediction based on recent activity
        last_30_days = timezone.now().date() - timedelta(days=30)
        
        recent_borrows = book.borrow_history.filter(
            borrow_date__gte=last_30_days
        ).count()
        
        active_reservations = book.reservations.filter(status='Active').count()
        wishlist_count = book.wishlisted_by.count()
        
        # Demand score (0-100)
        demand_score = min(100, (
            recent_borrows * 10 +
            active_reservations * 15 +
            wishlist_count * 5
        ))
        
        return {
            'demand_score': demand_score,
            'recent_borrows': recent_borrows,
            'active_reservations': active_reservations,
            'wishlist_count': wishlist_count,
            'recommendation': 'High Demand' if demand_score >= 70 else 
                            'Medium Demand' if demand_score >= 40 else 'Low Demand',
            'suggested_copies': max(book.total_copies, demand_score // 20)
        }
    
    @staticmethod
    def get_revenue_report(start_date=None, end_date=None):
        """Calculate revenue from fines"""
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        records = BorrowRecord.objects.filter(
            borrow_date__date__gte=start_date,
            borrow_date__date__lte=end_date
        )
        
        return {
            'total_fines': records.aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0,
            'fines_paid': records.filter(fine_paid=True).aggregate(
                Sum('fine_amount')
            )['fine_amount__sum'] or 0,
            'fines_pending': records.filter(fine_paid=False).aggregate(
                Sum('fine_amount')
            )['fine_amount__sum'] or 0,
            'total_transactions': records.filter(fine_amount__gt=0).count(),
        }
