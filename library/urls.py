from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_auth, views_borrow, views_review, views_api

# API Router
router = DefaultRouter()
router.register(r'api/books', views_api.BookViewSet, basename='api-book')
router.register(r'api/borrows', views_api.BorrowRecordViewSet, basename='api-borrow')
router.register(r'api/reservations', views_api.ReservationViewSet, basename='api-reservation')
router.register(r'api/reviews', views_api.ReviewViewSet, basename='api-review')
router.register(r'api/wishlist', views_api.WishlistViewSet, basename='api-wishlist')

urlpatterns = [
    # Home and Books
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/edit/<int:pk>/', views.book_edit, name='book_edit'),
    path('books/delete/<int:pk>/', views.book_delete, name='book_delete'),
    path('statistics/', views.statistics, name='statistics'),
    
    # Authentication
    path('register/', views_auth.register_view, name='register'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('profile/', views_auth.profile_view, name='profile'),
    
    # Borrowing
    path('borrow/<int:pk>/', views_borrow.borrow_book, name='borrow_book'),
    path('return/<int:pk>/', views_borrow.return_book, name='return_book'),
    path('my-books/', views_borrow.my_books, name='my_books'),
    path('borrow-history/', views_borrow.borrow_history, name='borrow_history'),
    
    # Reservations
    path('reserve/<int:pk>/', views_borrow.reserve_book, name='reserve_book'),
    path('my-reservations/', views_borrow.my_reservations, name='my_reservations'),
    path('cancel-reservation/<int:pk>/', views_borrow.cancel_reservation, name='cancel_reservation'),
    
    # Reviews
    path('review/add/<int:pk>/', views_review.add_review, name='add_review'),
    path('review/edit/<int:pk>/', views_review.edit_review, name='edit_review'),
    path('review/delete/<int:pk>/', views_review.delete_review, name='delete_review'),
    
    # Wishlist
    path('wishlist/add/<int:pk>/', views_review.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:pk>/', views_review.remove_from_wishlist, name='remove_from_wishlist'),
    path('my-wishlist/', views_review.my_wishlist, name='my_wishlist'),
    
    # Export
    path('export/books/excel/', views.export_books_excel, name='export_books_excel'),
    path('export/books/pdf/', views.export_books_pdf, name='export_books_pdf'),
    
    # API
    path('', include(router.urls)),
    path('api/dashboard/', views_api.user_dashboard, name='api_dashboard'),
]
