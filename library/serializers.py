"""REST API Serializers"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, BorrowRecord, Reservation, Review, UserProfile, Wishlist


class BookSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = '__all__'
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_total_reviews(self, obj):
        return obj.get_total_reviews()


class BookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category', 'status', 'rating', 'cover_image']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'


class BorrowRecordSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    fine_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = BorrowRecord
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Reservation
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'


class WishlistSerializer(serializers.ModelSerializer):
    book = BookListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = '__all__'
