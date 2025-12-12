"""
Backup and Restore System
Automated database backup and restore functionality
"""
import os
import json
import shutil
from django.core import serializers
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import zipfile


class BackupManager:
    """Handle database backups and restores"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_full_backup(self, include_media=True):
        """Create a complete backup of database and media files"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}'
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Backup database
        db_file = backup_path / 'database.json'
        with open(db_file, 'w') as f:
            call_command('dumpdata', stdout=f, indent=2, natural_foreign=True)
        
        # Backup media files
        if include_media and hasattr(settings, 'MEDIA_ROOT'):
            media_backup = backup_path / 'media'
            if Path(settings.MEDIA_ROOT).exists():
                shutil.copytree(settings.MEDIA_ROOT, media_backup)
        
        # Create metadata
        metadata = {
            'timestamp': timestamp,
            'django_version': self._get_django_version(),
            'database': settings.DATABASES['default']['ENGINE'],
            'includes_media': include_media,
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create zip archive
        zip_path = self.backup_dir / f'{backup_name}.zip'
        self._create_zip(backup_path, zip_path)
        
        # Clean up temporary directory
        shutil.rmtree(backup_path)
        
        return zip_path
    
    def restore_backup(self, backup_file, restore_media=True):
        """Restore from a backup file"""
        # Extract backup
        extract_path = self.backup_dir / 'temp_restore'
        extract_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Read metadata
        with open(extract_path / 'metadata.json', 'r') as f:
            metadata = json.load(f)
        
        # Restore database
        db_file = extract_path / 'database.json'
        call_command('loaddata', str(db_file))
        
        # Restore media files
        if restore_media and (extract_path / 'media').exists():
            if Path(settings.MEDIA_ROOT).exists():
                shutil.rmtree(settings.MEDIA_ROOT)
            shutil.copytree(extract_path / 'media', settings.MEDIA_ROOT)
        
        # Clean up
        shutil.rmtree(extract_path)
        
        return metadata
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        for backup_file in self.backup_dir.glob('backup_*.zip'):
            backups.append({
                'name': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'created': backup_file.stat().st_mtime,
            })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def delete_old_backups(self, keep_last=10):
        """Delete old backups, keeping only the most recent ones"""
        backups = self.list_backups()
        if len(backups) > keep_last:
            for backup in backups[keep_last:]:
                Path(backup['path']).unlink()
    
    def _create_zip(self, source_dir, output_file):
        """Create a zip archive from a directory"""
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    def _get_django_version(self):
        """Get Django version"""
        import django
        return django.get_version()
    
    def export_model_data(self, model_name, output_format='json'):
        """Export specific model data"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{model_name}_{timestamp}.{output_format}'
        output_path = self.backup_dir / filename
        
        with open(output_path, 'w') as f:
            call_command('dumpdata', model_name, stdout=f, indent=2, format=output_format)
        
        return output_path
    
    def create_scheduled_backup(self):
        """Create a backup for scheduled tasks"""
        backup_file = self.create_full_backup(include_media=True)
        self.delete_old_backups(keep_last=10)
        return backup_file


class DataExporter:
    """Export data in various formats"""
    
    @staticmethod
    def export_to_csv(queryset, fields, filename):
        """Export queryset to CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(fields)
        
        # Write data
        for obj in queryset:
            row = [getattr(obj, field) for field in fields]
            writer.writerow(row)
        
        output.seek(0)
        return output
    
    @staticmethod
    def export_to_json(queryset):
        """Export queryset to JSON"""
        data = serializers.serialize('json', queryset, indent=2)
        return data
    
    @staticmethod
    def export_to_xml(queryset):
        """Export queryset to XML"""
        data = serializers.serialize('xml', queryset, indent=2)
        return data
