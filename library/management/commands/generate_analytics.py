"""
Management command to generate and display analytics
Usage: python manage.py generate_analytics
"""
from django.core.management.base import BaseCommand
from library.analytics import LibraryAnalytics
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Generate and display library analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for trend analysis (default: 30)',
        )

    def handle(self, *args, **options):
        days = options['days']
        
        self.stdout.write(self.style.SUCCESS('\n📊 LIBRARY ANALYTICS REPORT'))
        self.stdout.write('=' * 60)
        
        # Dashboard Metrics
        self.stdout.write('\n📈 Dashboard Metrics:')
        metrics = LibraryAnalytics.get_dashboard_metrics()
        
        self.stdout.write(f"  Total Books: {metrics['total_books']}")
        self.stdout.write(f"  Total Users: {metrics['total_users']}")
        self.stdout.write(f"  Active Members: {metrics['active_members']}")
        self.stdout.write(f"  Books Borrowed Today: {metrics['books_borrowed_today']}")
        self.stdout.write(f"  Books Due Today: {metrics['books_due_today']}")
        self.stdout.write(f"  Overdue Books: {metrics['overdue_books']}")
        self.stdout.write(f"  Total Fines Pending: ${metrics['total_fines_pending']:.2f}")
        self.stdout.write(f"  Books Borrowed (Last 30 days): {metrics['books_borrowed_last_30_days']}")
        self.stdout.write(f"  New Users (Last 30 days): {metrics['new_users_last_30_days']}")
        self.stdout.write(f"  Average Rating: {metrics['average_rating']:.2f}/5.0")
        
        # Category Distribution
        self.stdout.write('\n📚 Category Distribution:')
        categories = LibraryAnalytics.get_category_distribution()
        for cat in categories[:5]:
            self.stdout.write(
                f"  {cat['category']}: {cat['count']} books "
                f"(Available: {cat['available']}, Borrowed: {cat['borrowed']})"
            )
        
        # Popular Books
        self.stdout.write('\n⭐ Top 5 Popular Books:')
        popular = LibraryAnalytics.get_popular_books(limit=5)
        for i, book in enumerate(popular, 1):
            self.stdout.write(
                f"  {i}. {book.title} by {book.author} "
                f"({book.borrow_history.count()} borrows)"
            )
        
        # Top Readers
        self.stdout.write('\n👥 Top 5 Readers:')
        readers = LibraryAnalytics.get_top_readers(limit=5)
        for i, user in enumerate(readers, 1):
            self.stdout.write(
                f"  {i}. {user.username} ({user.borrowings.count()} books borrowed)"
            )
        
        # Borrowing Trends
        self.stdout.write(f'\n📈 Borrowing Trends (Last {days} days):')
        trends = LibraryAnalytics.get_borrowing_trends(days=days)
        if trends:
            total_borrows = sum(t['count'] for t in trends)
            avg_per_day = total_borrows / len(trends) if trends else 0
            self.stdout.write(f"  Total Borrows: {total_borrows}")
            self.stdout.write(f"  Average per Day: {avg_per_day:.1f}")
        else:
            self.stdout.write("  No borrowing data available")
        
        # Revenue Report
        self.stdout.write('\n💰 Revenue Report (Last 30 days):')
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        revenue = LibraryAnalytics.get_revenue_report(start_date, end_date)
        
        self.stdout.write(f"  Total Fines: ${revenue['total_fines']:.2f}")
        self.stdout.write(f"  Fines Paid: ${revenue['fines_paid']:.2f}")
        self.stdout.write(f"  Fines Pending: ${revenue['fines_pending']:.2f}")
        self.stdout.write(f"  Total Transactions: {revenue['total_transactions']}")
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✓ Analytics report generated successfully\n'))
