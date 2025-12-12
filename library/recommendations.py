"""
Book Recommendation Engine
ML-based and rule-based recommendation system
"""
from django.db.models import Count, Q, Avg
from collections import defaultdict, Counter
from .models import Book, BorrowRecord, Review, Wishlist


class RecommendationEngine:
    """Generate personalized book recommendations"""
    
    @staticmethod
    def get_recommendations_for_user(user, limit=10):
        """Get personalized recommendations for a user"""
        recommendations = []
        
        # 1. Collaborative filtering - users who borrowed similar books
        similar_users_books = RecommendationEngine._collaborative_filtering(user, limit)
        recommendations.extend(similar_users_books)
        
        # 2. Content-based - books in same categories user likes
        category_based = RecommendationEngine._content_based_filtering(user, limit)
        recommendations.extend(category_based)
        
        # 3. Popular books user hasn't read
        popular_books = RecommendationEngine._popular_books_not_read(user, limit)
        recommendations.extend(popular_books)
        
        # Remove duplicates and books user already borrowed
        user_borrowed_ids = user.borrowings.values_list('book_id', flat=True)
        seen = set()
        unique_recommendations = []
        
        for book in recommendations:
            if book.id not in seen and book.id not in user_borrowed_ids:
                seen.add(book.id)
                unique_recommendations.append(book)
                if len(unique_recommendations) >= limit:
                    break
        
        return unique_recommendations
    
    @staticmethod
    def _collaborative_filtering(user, limit):
        """Find books borrowed by users with similar taste"""
        # Get books user has borrowed
        user_books = user.borrowings.values_list('book_id', flat=True)
        
        if not user_books:
            return []
        
        # Find users who borrowed same books
        similar_users = BorrowRecord.objects.filter(
            book_id__in=user_books
        ).exclude(
            user=user
        ).values_list('user_id', flat=True).distinct()
        
        # Get books these users borrowed
        recommended_books = Book.objects.filter(
            borrow_history__user_id__in=similar_users
        ).exclude(
            id__in=user_books
        ).annotate(
            borrow_count=Count('borrow_history')
        ).order_by('-borrow_count')[:limit]
        
        return list(recommended_books)
    
    @staticmethod
    def _content_based_filtering(user, limit):
        """Recommend books based on user's preferred categories"""
        # Get user's favorite categories
        user_categories = BorrowRecord.objects.filter(
            user=user
        ).values_list('book__category', flat=True)
        
        if not user_categories:
            return []
        
        # Count category preferences
        category_counts = Counter(user_categories)
        top_categories = [cat for cat, _ in category_counts.most_common(3)]
        
        # Get highly rated books in these categories
        user_borrowed_ids = user.borrowings.values_list('book_id', flat=True)
        
        recommended_books = Book.objects.filter(
            category__in=top_categories
        ).exclude(
            id__in=user_borrowed_ids
        ).filter(
            rating__gte=3.5
        ).order_by('-rating', '-created_at')[:limit]
        
        return list(recommended_books)
    
    @staticmethod
    def _popular_books_not_read(user, limit):
        """Recommend popular books user hasn't read"""
        user_borrowed_ids = user.borrowings.values_list('book_id', flat=True)
        
        popular_books = Book.objects.exclude(
            id__in=user_borrowed_ids
        ).annotate(
            borrow_count=Count('borrow_history'),
            avg_rating=Avg('reviews__rating')
        ).filter(
            borrow_count__gt=0
        ).order_by('-borrow_count', '-avg_rating')[:limit]
        
        return list(popular_books)
    
    @staticmethod
    def get_similar_books(book, limit=5):
        """Find books similar to a given book"""
        similar_books = []
        
        # 1. Same category and author
        same_author = Book.objects.filter(
            author=book.author
        ).exclude(id=book.id)[:limit]
        similar_books.extend(same_author)
        
        # 2. Same category with high rating
        same_category = Book.objects.filter(
            category=book.category
        ).exclude(
            id=book.id
        ).filter(
            rating__gte=3.0
        ).order_by('-rating')[:limit]
        similar_books.extend(same_category)
        
        # 3. Books borrowed by same users
        users_who_borrowed = BorrowRecord.objects.filter(
            book=book
        ).values_list('user_id', flat=True)
        
        co_borrowed = Book.objects.filter(
            borrow_history__user_id__in=users_who_borrowed
        ).exclude(
            id=book.id
        ).annotate(
            count=Count('borrow_history')
        ).order_by('-count')[:limit]
        similar_books.extend(co_borrowed)
        
        # Remove duplicates
        seen = set()
        unique_similar = []
        for b in similar_books:
            if b.id not in seen:
                seen.add(b.id)
                unique_similar.append(b)
                if len(unique_similar) >= limit:
                    break
        
        return unique_similar
    
    @staticmethod
    def get_trending_books(days=7, limit=10):
        """Get trending books based on recent activity"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        trending = Book.objects.filter(
            Q(borrow_history__borrow_date__gte=start_date) |
            Q(reviews__created_at__gte=start_date) |
            Q(wishlisted_by__added_date__gte=start_date)
        ).annotate(
            activity_score=Count('borrow_history') + Count('reviews') + Count('wishlisted_by')
        ).order_by('-activity_score')[:limit]
        
        return list(trending)
    
    @staticmethod
    def get_recommendations_by_wishlist(user, limit=5):
        """Recommend books based on user's wishlist"""
        wishlist_books = user.wishlist.values_list('book', flat=True)
        
        if not wishlist_books:
            return []
        
        # Get categories from wishlist
        wishlist_categories = Book.objects.filter(
            id__in=wishlist_books
        ).values_list('category', flat=True)
        
        # Recommend similar books
        recommendations = Book.objects.filter(
            category__in=wishlist_categories
        ).exclude(
            id__in=wishlist_books
        ).filter(
            status='Available',
            rating__gte=3.0
        ).order_by('-rating')[:limit]
        
        return list(recommendations)
