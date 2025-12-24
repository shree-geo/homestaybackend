"""
Management command to clean up orphaned media files.

Usage:
    # Dry run (see what would be deleted without actually deleting)
    python manage.py cleanup_orphaned_media --dry-run
    
    # Clean up files older than 24 hours (default)
    python manage.py cleanup_orphaned_media
    
    # Clean up files older than 48 hours
    python manage.py cleanup_orphaned_media --grace-period 48
    
    # Show statistics only
    python manage.py cleanup_orphaned_media --stats-only
    
    # Custom batch size
    python manage.py cleanup_orphaned_media --batch-size 50
"""
from django.core.management.base import BaseCommand
from config.utils.media_cleanup import (
    cleanup_orphaned_media,
    identify_orphaned_media,
    get_media_statistics
)


class Command(BaseCommand):
    help = 'Clean up orphaned media files that are not linked to any entity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--grace-period',
            type=int,
            default=24,
            help='Hours to wait before considering a file orphaned (default: 24)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Only show statistics without performing cleanup',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        grace_period = options['grace_period']
        batch_size = options['batch_size']
        stats_only = options['stats_only']

        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('Media Cleanup Utility'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        
        # Show overall statistics
        self.stdout.write(self.style.HTTP_INFO('\n📊 Overall Media Statistics:'))
        stats = get_media_statistics()
        self.stdout.write(f"  Total media files: {stats['total_media_count']}")
        self.stdout.write(f"  Linked media files: {stats['linked_media_count']}")
        self.stdout.write(f"  Orphaned media files: {stats['orphaned_media_count']} "
                         f"({stats['orphaned_percentage']}%)")
        self.stdout.write(f"  Total storage: {stats['total_storage_mb']} MB")
        self.stdout.write(f"  Orphaned storage: {stats['orphaned_storage_mb']} MB")
        self.stdout.write(f"  Media root: {stats['media_root']}")
        
        if stats_only:
            self.stdout.write(self.style.SUCCESS('\n✅ Statistics displayed.'))
            return
        
        # Identify orphaned files
        self.stdout.write(self.style.HTTP_INFO(f'\n🔍 Identifying orphaned media '
                                              f'(grace period: {grace_period} hours)...'))
        orphan_info = identify_orphaned_media(grace_period_hours=grace_period)
        
        self.stdout.write(f"  Found {orphan_info['orphaned_count']} orphaned files")
        self.stdout.write(f"  Total size: {orphan_info['total_size_mb']} MB")
        if orphan_info['oldest_orphan']:
            self.stdout.write(f"  Oldest orphan: {orphan_info['oldest_orphan']}")
        
        if orphan_info['orphaned_count'] == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ No orphaned media found!'))
            return
        
        # Perform cleanup
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔸 DRY RUN MODE - No files will be deleted'))
        else:
            self.stdout.write(self.style.WARNING('\n🗑️  Starting cleanup...'))
        
        result = cleanup_orphaned_media(
            grace_period_hours=grace_period,
            dry_run=dry_run,
            batch_size=batch_size
        )
        
        # Display results
        self.stdout.write(self.style.HTTP_INFO('\n📋 Cleanup Results:'))
        self.stdout.write(f"  Identified: {result['identified_count']}")
        self.stdout.write(f"  Deleted: {result['deleted_count']}")
        self.stdout.write(f"  Failed: {result['failed_count']}")
        self.stdout.write(f"  Space freed: {result['total_size_freed_mb']} MB")
        
        if result['errors']:
            self.stdout.write(self.style.ERROR('\n❌ Errors encountered:'))
            for error in result['errors'][:10]:  # Show first 10 errors
                self.stdout.write(f"  - {error}")
            if len(result['errors']) > 10:
                self.stdout.write(f"  ... and {len(result['errors']) - 10} more errors")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Dry run complete. '
                                                'Run without --dry-run to actually delete files.'))
        else:
            if result['failed_count'] == 0:
                self.stdout.write(self.style.SUCCESS('\n✅ Cleanup completed successfully!'))
            else:
                self.stdout.write(self.style.WARNING(f'\n⚠️  Cleanup completed with '
                                                    f'{result["failed_count"]} failures.'))
