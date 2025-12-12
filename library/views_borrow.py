"""Borrowing and reservation views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Book, BorrowRecord, Reservation, UserProfile, AuditLog, Notification
from .forms import BorrowBookForm


@login_required
def borrow_book(request, pk):
    """Borrow a book"""
    book = get_object_or_404(Book, pk=pk)
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    
    # Check if user can borrow more books
    if not profile.can_borrow_more():
        messages.error(request, f'You have reached your borrowing limit of {profile.max_books_allowed} books.')
        return redirect('book_detail', pk=pk)
    
    # Check if book is available
    if not book.is_available or book.copies_available < 1:
        messages.error(request, 'This book is not available for borrowing.')
        return redirect('book_detail', pk=pk)
    
    # Check if user already has this book
    existing_borrow = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        status__in=['Borrowed', 'Overdue']
    ).exists()
    
    if existing_borrow:
        messages.error(request, 'You already have this book borrowed.')
        return redirect('book_detail', pk=pk)
    
    if request.method == 'POST':
        form = BorrowBookForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['borrow_days']
            due_date = timezone.now().date() + timedelta(days=days)
            
            # Create borrow record
            borrow = BorrowRecord.objects.create(
                user=request.user,
                book=book,
                due_date=due_date,
                status='Borrowed'
            )
            
            # Update book availability
            book.copies_available -= 1
            if book.copies_available == 0:
                book.status = 'Borrowed'
            book.save()
            
            # Log action
            AuditLog.objects.create(
                user=request.user,
                action='BORROW',
                model_name='Book',
                object_id=book.id,
                description=f"Borrowed book: {book.title}"
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='GENERAL',
                title='Book Borrowed Successfully',
                message=f'You have borrowed "{book.title}". Due date: {due_date}',
                link=f'/my-books/'
            )
            
            messages.success(request, f'Book borrowed successfully! Due date: {due_date}')
            return redirect('my_books')
    else:
        form = BorrowBookForm()
    
    context = {
        'book': book,
        'form': form,
        'profile': profile
    }
    return render(request, 'library/borrow/borrow_book.html', context)


@login_required
def return_book(request, pk):
    """Return a borrowed book"""
    borrow = get_object_or_404(BorrowRecord, pk=pk, user=request.user)
    
    if borrow.status not in ['Borrowed', 'Overdue']:
        messages.error(request, 'This book has already been returned.')
        return redirect('my_books')
    
    if request.method == 'POST':
        # Update borrow record
        borrow.return_date = timezone.now()
        borrow.status = 'Returned'
        borrow.fine_amount = borrow.calculate_fine()
        borrow.save()
        
        # Update book availability
        book = borrow.book
        book.copies_available += 1
        if book.copies_available > 0:
            book.status = 'Available'
        book.save()
        
        # Update user profile fines
        if borrow.fine_amount > 0:
            profile = request.user.profile
            profile.total_fines += borrow.fine_amount
            profile.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='RETURN',
            model_name='Book',
            object_id=book.id,
            description=f"Returned book: {book.title}"
        )
        
        # Notify users with reservations
        notify_reserved_users(book)
        
        if borrow.fine_amount > 0:
            messages.warning(request, f'Book returned. Fine amount: ${borrow.fine_amount}')
        else:
            messages.success(request, 'Book returned successfully!')
        
        return redirect('my_books')
    
    context = {
        'borrow': borrow,
        'fine_amount': borrow.calculate_fine()
    }
    return render(request, 'library/borrow/return_book.html', context)


@login_required
def my_books(request):
    """View user's borrowed books"""
    borrowed_books = BorrowRecord.objects.filter(
        user=request.user,
        status__in=['Borrowed', 'Overdue']
    ).select_related('book')
    
    # Update overdue status
    for borrow in borrowed_books:
        if borrow.is_overdue():
            borrow.status = 'Overdue'
            borrow.save()
    
    context = {
        'borrowed_books': borrowed_books
    }
    return render(request, 'library/borrow/my_books.html', context)


@login_required
def borrow_history(request):
    """View borrowing history"""
    history = BorrowRecord.objects.filter(user=request.user).select_related('book').order_by('-borrow_date')
    
    context = {
        'history': history
    }
    return render(request, 'library/borrow/borrow_history.html', context)


@login_required
def reserve_book(request, pk):
    """Reserve a book"""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if already reserved
    existing_reservation = Reservation.objects.filter(
        user=request.user,
        book=book,
        status='Active'
    ).exists()
    
    if existing_reservation:
        messages.error(request, 'You already have an active reservation for this book.')
        return redirect('book_detail', pk=pk)
    
    # Create reservation
    reservation = Reservation.objects.create(
        user=request.user,
        book=book,
        expiry_date=timezone.now() + timedelta(days=7)
    )
    
    # Update book status
    if book.status == 'Available':
        book.status = 'Reserved'
        book.save()
    
    # Log action
    AuditLog.objects.create(
        user=request.user,
        action='RESERVE',
        model_name='Book',
        object_id=book.id,
        description=f"Reserved book: {book.title}"
    )
    
    messages.success(request, f'Book reserved successfully! Reservation expires on {reservation.expiry_date.date()}')
    return redirect('my_reservations')


@login_required
def my_reservations(request):
    """View user's reservations"""
    reservations = Reservation.objects.filter(user=request.user).select_related('book').order_by('-reservation_date')
    
    # Update expired reservations
    for reservation in reservations:
        if reservation.is_expired():
            reservation.status = 'Expired'
            reservation.save()
    
    context = {
        'reservations': reservations
    }
    return render(request, 'library/borrow/my_reservations.html', context)


@login_required
def cancel_reservation(request, pk):
    """Cancel a reservation"""
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    
    if reservation.status != 'Active':
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('my_reservations')
    
    reservation.status = 'Cancelled'
    reservation.save()
    
    messages.success(request, 'Reservation cancelled successfully.')
    return redirect('my_reservations')


def notify_reserved_users(book):
    """Notify users who have reserved a book when it becomes available"""
    active_reservations = Reservation.objects.filter(
        book=book,
        status='Active',
        notified=False
    ).order_by('reservation_date')
    
    for reservation in active_reservations[:1]:  # Notify first in queue
        Notification.objects.create(
            user=reservation.user,
            notification_type='AVAILABLE',
            title='Reserved Book Available',
            message=f'The book "{book.title}" you reserved is now available!',
            link=f'/books/{book.id}/'
        )
        reservation.notified = True
        reservation.save()
