"""
Management command to create database backups
Usage: python manage.py backup_database
"""
from django.core.management.base import BaseCommand
from library.backup_restore import BackupManager


class Command(BaseCommand):
    help = 'Create a full backup of the database and media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-media',
            action='store_true',
            help='Skip media files backup',
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=10,
            help='Number of backups to keep (default: 10)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating backup...')
        
        backup_manager = BackupManager()
        include_media = not options['no_media']
        
        try:
            backup_file = backup_manager.create_full_backup(include_media=include_media)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Backup created successfully: {backup_file}')
            )
            
            # Clean up old backups
            keep_last = options['keep']
            backup_manager.delete_old_backups(keep_last=keep_last)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Cleaned up old backups (keeping last {keep_last})')
            )
            
            # List current backups
            backups = backup_manager.list_backups()
            self.stdout.write(f'\nCurrent backups: {len(backups)}')
            for backup in backups[:5]:  # Show last 5
                size_mb = backup['size'] / (1024 * 1024)
                self.stdout.write(f"  - {backup['name']} ({size_mb:.2f} MB)")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Backup failed: {str(e)}')
            )
