"""REST API Views"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from .models import Book, BorrowRecord, Reservation, Review, UserProfile, Wishlist
from .serializers import (
    BookSerializer, BookListSerializer, BorrowRecordSerializer,
    ReservationSerializer, ReviewSerializer, UserProfileSerializer, WishlistSerializer
)


class BookViewSet(viewsets.ModelViewSet):
    """API endpoint for books"""
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'language', 'published_year']
    search_fields = ['title', 'author', 'isbn', 'publisher', 'description']
    ordering_fields = ['title', 'author', 'published_year', 'rating', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BookSerializer
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available books"""
        books = self.queryset.filter(status='Available', copies_available__gt=0)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular books based on ratings and reviews"""
        books = self.queryset.filter(rating__gte=4.0).order_by('-rating')[:10]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for a specific book"""
        book = self.get_object()
        reviews = book.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get book statistics"""
        total_books = self.queryset.count()
        available_books = self.queryset.filter(status='Available').count()
        borrowed_books = self.queryset.filter(status='Borrowed').count()
        
        category_stats = self.queryset.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_books': total_books,
            'available_books': available_books,
            'borrowed_books': borrowed_books,
            'category_distribution': category_stats
        })


class BorrowRecordViewSet(viewsets.ModelViewSet):
    """API endpoint for borrow records"""
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'user', 'book']
    ordering = ['-borrow_date']
    
    def get_queryset(self):
        """Users can only see their own borrow records unless staff"""
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_borrowed(self, request):
        """Get current user's borrowed books"""
        records = self.queryset.filter(
            user=request.user,
            status__in=['Borrowed', 'Overdue']
        )
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue books"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        records = self.queryset.filter(status='Overdue')
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ModelViewSet):
    """API endpoint for reservations"""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'user', 'book']
    ordering = ['-reservation_date']
    
    def get_queryset(self):
        """Users can only see their own reservations unless staff"""
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Get current user's active reservations"""
        reservations = self.queryset.filter(user=request.user, status='Active')
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """API endpoint for reviews"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'user', 'rating']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class WishlistViewSet(viewsets.ModelViewSet):
    """API endpoint for wishlist"""
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own wishlist"""
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """Get user dashboard data"""
    user = request.user
    profile = UserProfile.objects.get_or_create(user=user)[0]
    
    borrowed_count = BorrowRecord.objects.filter(user=user, status='Borrowed').count()
    overdue_count = BorrowRecord.objects.filter(user=user, status='Overdue').count()
    reservations_count = Reservation.objects.filter(user=user, status='Active').count()
    wishlist_count = Wishlist.objects.filter(user=user).count()
    reviews_count = Review.objects.filter(user=user).count()
    
    return Response({
        'profile': UserProfileSerializer(profile).data,
        'borrowed_books': borrowed_count,
        'overdue_books': overdue_count,
        'active_reservations': reservations_count,
        'wishlist_items': wishlist_count,
        'total_reviews': reviews_count,
        'total_fines': float(profile.total_fines)
    })
