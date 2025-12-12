"""Management command to expire old reservations"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from library.models import Reservation


class Command(BaseCommand):
    help = 'Expire old reservations'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find all active reservations that have expired
        expired_reservations = Reservation.objects.filter(
            status='Active',
            expiry_date__lt=now
        )
        
        count = expired_reservations.count()
        
        # Update status to expired
        expired_reservations.update(status='Expired')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully expired {count} reservation(s)')
        )
