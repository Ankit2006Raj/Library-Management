"""
Notification Service
Handle email, SMS, and in-app notifications
"""
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Notification, BorrowRecord, Reservation
from django.utils import timezone
from datetime import timedelta


class NotificationService:
    """Centralized notification management"""
    
    @staticmethod
    def send_email_notification(user, subject, template_name, context):
        """Send email notification to user"""
        context['user'] = user
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def create_in_app_notification(user, notification_type, title, message, link=None):
        """Create in-app notification"""
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        return notification
    
    @staticmethod
    def notify_due_soon(borrow_record):
        """Notify user that book is due soon"""
        user = borrow_record.user
        book = borrow_record.book
        
        # In-app notification
        NotificationService.create_in_app_notification(
            user=user,
            notification_type='DUE_SOON',
            title='Book Due Soon',
            message=f'"{book.title}" is due on {borrow_record.due_date}. Please return it on time.',
            link=f'/my-books/'
        )
        
        # Email notification
        context = {
            'book': book,
            'due_date': borrow_record.due_date,
            'borrow_record': borrow_record
        }
        NotificationService.send_email_notification(
            user=user,
            subject=f'Reminder: "{book.title}" is due soon',
            template_name='library/emails/due_soon.html',
            context=context
        )
    
    @staticmethod
    def notify_overdue(borrow_record):
        """Notify user that book is overdue"""
        user = borrow_record.user
        book = borrow_record.book
        
        # Calculate fine
        fine = borrow_record.calculate_fine()
        
        # In-app notification
        NotificationService.create_in_app_notification(
            user=user,
            notification_type='OVERDUE',
            title='Book Overdue',
            message=f'"{book.title}" is overdue. Fine: ${fine}. Please return immediately.',
            link=f'/my-books/'
        )
        
        # Email notification
        context = {
            'book': book,
            'due_date': borrow_record.due_date,
            'fine': fine,
            'borrow_record': borrow_record
        }
        NotificationService.send_email_notification(
            user=user,
            subject=f'Overdue: "{book.title}" - Fine: ${fine}',
            template_name='library/emails/overdue.html',
            context=context
        )
    
    @staticmethod
    def notify_book_available(reservation):
        """Notify user that reserved book is available"""
        user = reservation.user
        book = reservation.book
        
        # In-app notification
        NotificationService.create_in_app_notification(
            user=user,
            notification_type='AVAILABLE',
            title='Reserved Book Available',
            message=f'"{book.title}" is now available for pickup. Reservation expires on {reservation.expiry_date}.',
            link=f'/books/{book.id}/'
        )
        
        # Email notification
        context = {
            'book': book,
            'reservation': reservation,
            'expiry_date': reservation.expiry_date
        }
        NotificationService.send_email_notification(
            user=user,
            subject=f'"{book.title}" is now available!',
            template_name='library/emails/book_available.html',
            context=context
        )
        
        # Mark as notified
        reservation.notified = True
        reservation.save()
    
    @staticmethod
    def notify_reservation_confirmed(reservation):
        """Notify user that reservation is confirmed"""
        user = reservation.user
        book = reservation.book
        
        # In-app notification
        NotificationService.create_in_app_notification(
            user=user,
            notification_type='RESERVATION',
            title='Reservation Confirmed',
            message=f'Your reservation for "{book.title}" is confirmed. You will be notified when available.',
            link=f'/my-reservations/'
        )
        
        # Email notification
        context = {
            'book': book,
            'reservation': reservation
        }
        NotificationService.send_email_notification(
            user=user,
            subject=f'Reservation confirmed: "{book.title}"',
            template_name='library/emails/reservation_confirmed.html',
            context=context
        )
    
    @staticmethod
    def notify_fine_payment(user, amount):
        """Notify user about fine payment"""
        # In-app notification
        NotificationService.create_in_app_notification(
            user=user,
            notification_type='FINE',
            title='Fine Payment Due',
            message=f'You have an outstanding fine of ${amount}. Please pay to continue borrowing.',
            link=f'/profile/'
        )
        
        # Email notification
        context = {
            'amount': amount
        }
        NotificationService.send_email_notification(
            user=user,
            subject=f'Fine Payment Due: ${amount}',
            template_name='library/emails/fine_payment.html',
            context=context
        )
    
    @staticmethod
    def notify_welcome(user):
        """Send welcome email to new user"""
        context = {
            'username': user.username
        }
        NotificationService.send_email_notification(
            user=user,
            subject='Welcome to Library Management System',
            template_name='library/emails/welcome.html',
            context=context
        )
    
    @staticmethod
    def send_bulk_notifications(users, subject, message):
        """Send bulk notifications to multiple users"""
        # In-app notifications
        notifications = [
            Notification(
                user=user,
                notification_type='GENERAL',
                title=subject,
                message=message
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)
        
        # Bulk email
        messages = [
            (
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            for user in users if user.email
        ]
        
        try:
            send_mass_mail(messages, fail_silently=False)
            return True
        except Exception as e:
            print(f"Bulk email failed: {e}")
            return False
    
    @staticmethod
    def send_daily_digest():
        """Send daily digest to users with pending notifications"""
        from django.contrib.auth.models import User
        
        for user in User.objects.filter(is_active=True):
            unread_notifications = user.notifications.filter(is_read=False)
            
            if unread_notifications.exists():
                context = {
                    'notifications': unread_notifications,
                    'count': unread_notifications.count()
                }
                NotificationService.send_email_notification(
                    user=user,
                    subject=f'Daily Digest - {unread_notifications.count()} unread notifications',
                    template_name='library/emails/daily_digest.html',
                    context=context
                )
