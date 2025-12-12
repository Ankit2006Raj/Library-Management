"""Review and wishlist views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, Review, Wishlist, BorrowRecord
from .forms import ReviewForm


@login_required
def add_review(request, pk):
    """Add a review for a book"""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user already reviewed this book
    existing_review = Review.objects.filter(user=request.user, book=book).exists()
    if existing_review:
        messages.error(request, 'You have already reviewed this book.')
        return redirect('book_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book = book
            review.save()
            
            # Update book rating
            update_book_rating(book)
            
            messages.success(request, 'Review added successfully!')
            return redirect('book_detail', pk=pk)
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'book': book
    }
    return render(request, 'library/review/add_review.html', context)


@login_required
def edit_review(request, pk):
    """Edit a review"""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            
            # Update book rating
            update_book_rating(review.book)
            
            messages.success(request, 'Review updated successfully!')
            return redirect('book_detail', pk=review.book.pk)
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review
    }
    return render(request, 'library/review/edit_review.html', context)


@login_required
def delete_review(request, pk):
    """Delete a review"""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    book = review.book
    
    if request.method == 'POST':
        review.delete()
        
        # Update book rating
        update_book_rating(book)
        
        messages.success(request, 'Review deleted successfully!')
        return redirect('book_detail', pk=book.pk)
    
    context = {
        'review': review
    }
    return render(request, 'library/review/delete_review.html', context)


@login_required
def add_to_wishlist(request, pk):
    """Add a book to wishlist"""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if already in wishlist
    existing = Wishlist.objects.filter(user=request.user, book=book).exists()
    if existing:
        messages.info(request, 'This book is already in your wishlist.')
        return redirect('book_detail', pk=pk)
    
    Wishlist.objects.create(user=request.user, book=book)
    messages.success(request, 'Book added to wishlist!')
    return redirect('book_detail', pk=pk)


@login_required
def remove_from_wishlist(request, pk):
    """Remove a book from wishlist"""
    wishlist_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    wishlist_item.delete()
    messages.success(request, 'Book removed from wishlist!')
    return redirect('my_wishlist')


@login_required
def my_wishlist(request):
    """View user's wishlist"""
    wishlist = Wishlist.objects.filter(user=request.user).select_related('book').order_by('-added_date')
    
    context = {
        'wishlist': wishlist
    }
    return render(request, 'library/review/my_wishlist.html', context)


def update_book_rating(book):
    """Update book's average rating based on reviews"""
    reviews = Review.objects.filter(book=book)
    if reviews.exists():
        avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        book.rating = round(avg_rating, 2)
        book.save()


from django.db import models
