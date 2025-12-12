"""Management command to send due date reminders"""
from django.core.management.base import BaseCommand
from library.utils import send_due_date_reminders, send_overdue_notifications


class Command(BaseCommand):
    help = 'Send due date reminders and overdue notifications'

    def handle(self, *args, **options):
        self.stdout.write('Sending due date reminders...')
        send_due_date_reminders()
        
        self.stdout.write('Sending overdue notifications...')
        send_overdue_notifications()
        
        self.stdout.write(self.style.SUCCESS('Successfully sent all notifications'))
