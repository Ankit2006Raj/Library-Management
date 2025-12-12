from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from .models import Book
from .forms import BookForm

def book_list(request):
    """Display all books with search, filter, and pagination"""
    books = Book.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(publisher__icontains=search_query)
        )
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        books = books.filter(category=category_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        books = books.filter(status=status_filter)
    
    # Filter by language
    language_filter = request.GET.get('language', '')
    if language_filter:
        books = books.filter(language=language_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    books = books.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(books, 10)  # 10 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories, statuses, and languages for filters
    categories = Book.CATEGORY_CHOICES
    statuses = Book.STATUS_CHOICES
    languages = Book.LANGUAGE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'total_books': books.count(),
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'language_filter': language_filter,
        'sort_by': sort_by,
        'categories': categories,
        'statuses': statuses,
        'languages': languages,
    }
    return render(request, 'library/book_list_final.html', context)

def book_detail(request, pk):
    """Display detailed information about a book"""
    book = get_object_or_404(Book, pk=pk)
    context = {
        'book': book
    }
    return render(request, 'library/book_detail.html', context)

def book_add(request):
    """Add a new book"""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm()
    
    return render(request, 'library/book_form.html', {'form': form, 'action': 'Add'})

def book_edit(request, pk):
    """Edit an existing book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'library/book_form.html', {'form': form, 'action': 'Edit', 'book': book})

def book_delete(request, pk):
    """Delete a book"""
    book = get_object_or_404(Book, pk=pk)
    
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" deleted successfully!')
        return redirect('book_list')
    
    return render(request, 'library/book_confirm_delete.html', {'book': book})

def home(request):
    """Home page with statistics and analytics"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='Available').count()
    borrowed_books = Book.objects.filter(status='Borrowed').count()
    
    # Category statistics
    category_stats = Book.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent books
    recent_books = Book.objects.all()[:6]
    
    # Top rated books
    top_rated_books = Book.objects.filter(rating__gt=0).order_by('-rating')[:5]
    
    # Language distribution
    language_stats = Book.objects.values('language').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_categories': len(Book.CATEGORY_CHOICES),
        'recent_books': recent_books,
        'top_rated_books': top_rated_books,
        'category_stats': category_stats,
        'language_stats': language_stats,
    }
    return render(request, 'library/home.html', context)

def statistics(request):
    """Display detailed statistics and analytics"""
    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='Available').count()
    borrowed_books = Book.objects.filter(status='Borrowed').count()
    reserved_books = Book.objects.filter(status='Reserved').count()
    
    # Category distribution
    category_distribution = Book.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Language distribution
    language_distribution = Book.objects.values('language').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Average rating
    avg_rating = Book.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Books by year
    year_distribution = Book.objects.values('published_year').annotate(
        count=Count('id')
    ).order_by('-published_year')[:10]
    
    context = {
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'reserved_books': reserved_books,
        'category_distribution': category_distribution,
        'language_distribution': language_distribution,
        'avg_rating': round(avg_rating, 2),
        'year_distribution': year_distribution,
    }
    return render(request, 'library/statistics.html', context)



from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import export_books_to_excel, export_books_to_pdf


def is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def export_books_excel(request):
    """Export books to Excel"""
    books = Book.objects.all()
    
    # Apply filters if any
    category = request.GET.get('category')
    status_filter = request.GET.get('status')
    
    if category:
        books = books.filter(category=category)
    if status_filter:
        books = books.filter(status=status_filter)
    
    return export_books_to_excel(books)


@login_required
@user_passes_test(is_staff)
def export_books_pdf(request):
    """Export books to PDF"""
    books = Book.objects.all()
    
    # Apply filters if any
    category = request.GET.get('category')
    status_filter = request.GET.get('status')
    
    if category:
        books = books.filter(category=category)
    if status_filter:
        books = books.filter(status=status_filter)
    
    return export_books_to_pdf(books)
