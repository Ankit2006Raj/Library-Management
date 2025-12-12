"""Management command to update overdue book status"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import BorrowRecord


class Command(BaseCommand):
    help = 'Update status of overdue books'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Find all borrowed books that are past due date
        overdue_books = BorrowRecord.objects.filter(
            status='Borrowed',
            due_date__lt=today
        )
        
        count = overdue_books.count()
        
        # Update status to overdue
        overdue_books.update(status='Overdue')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} overdue book(s)')
        )
