"""
Utility functions for cleaning up orphaned media files.

Orphaned media files are those that have been uploaded but never linked 
to any entity (content_type and object_id are NULL).
"""
import os
import logging
from datetime import timedelta
from typing import Dict, List
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from core.models import Multimedia

logger = logging.getLogger(__name__)


def identify_orphaned_media(grace_period_hours: int = 24) -> Dict[str, any]:
    """
    Identify orphaned media files that are not linked to any entity.
    
    Args:
        grace_period_hours: Number of hours to wait before considering 
                          a file orphaned (default: 24 hours).
                          This allows time for uploads to be linked.
    
    Returns:
        Dictionary containing:
        - orphaned_count: Number of orphaned files
        - orphaned_ids: List of orphaned multimedia IDs
        - total_size_bytes: Estimated total size in bytes
        - oldest_orphan: Oldest orphaned file timestamp
    """
    cutoff_time = timezone.now() - timedelta(hours=grace_period_hours)
    
    # Find multimedia records where:
    # 1. content_type is NULL (not linked to any model)
    # 2. object_id is NULL (not linked to any object)
    # 3. Created before the grace period cutoff
    orphaned = Multimedia.objects.filter(
        content_type__isnull=True,
        object_id__isnull=True,
        created_at__lt=cutoff_time
    ).order_by('created_at')
    
    orphaned_ids = list(orphaned.values_list('id', flat=True))
    count = len(orphaned_ids)
    
    # Calculate total size
    total_size = 0
    for media in orphaned:
        if media.file and os.path.exists(media.file.path):
            try:
                total_size += os.path.getsize(media.file.path)
            except OSError:
                pass
    
    oldest = orphaned.first()
    oldest_timestamp = oldest.created_at if oldest else None
    
    return {
        'orphaned_count': count,
        'orphaned_ids': orphaned_ids,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_orphan': oldest_timestamp,
        'grace_period_hours': grace_period_hours,
    }


def delete_media_file(media: Multimedia) -> bool:
    """
    Safely delete a media file from disk.
    
    Args:
        media: Multimedia instance
        
    Returns:
        True if file was deleted successfully, False otherwise
    """
    if not media.file:
        return True
    
    try:
        file_path = media.file.path
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            
            # Try to remove empty parent directories
            try:
                parent_dir = os.path.dirname(file_path)
                if parent_dir and parent_dir != settings.MEDIA_ROOT:
                    # Only remove if directory is empty
                    if not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                        logger.info(f"Removed empty directory: {parent_dir}")
            except OSError:
                pass  # Directory not empty or other issue, ignore
                
            return True
    except Exception as e:
        logger.error(f"Failed to delete file for media {media.id}: {str(e)}")
        return False
    
    return True


@transaction.atomic
def cleanup_orphaned_media(
    grace_period_hours: int = 24,
    dry_run: bool = False,
    batch_size: int = 100
) -> Dict[str, any]:
    """
    Clean up orphaned media files from database and disk.
    
    Args:
        grace_period_hours: Hours to wait before considering a file orphaned (default: 24)
        dry_run: If True, only identify orphans without deleting (default: False)
        batch_size: Number of records to process in each batch (default: 100)
        
    Returns:
        Dictionary containing:
        - dry_run: Whether this was a dry run
        - identified_count: Number of orphaned files identified
        - deleted_count: Number of files successfully deleted
        - failed_count: Number of files that failed to delete
        - total_size_freed_mb: Size freed in MB
        - errors: List of error messages
    """
    cutoff_time = timezone.now() - timedelta(hours=grace_period_hours)
    
    orphaned = Multimedia.objects.filter(
        content_type__isnull=True,
        object_id__isnull=True,
        created_at__lt=cutoff_time
    )
    
    identified_count = orphaned.count()
    deleted_count = 0
    failed_count = 0
    total_size_freed = 0
    errors = []
    
    logger.info(
        f"{'[DRY RUN] ' if dry_run else ''}Found {identified_count} orphaned media files "
        f"older than {grace_period_hours} hours"
    )
    
    if dry_run:
        # Just report what would be deleted
        for media in orphaned[:10]:  # Show first 10 as sample
            logger.info(f"Would delete: {media.file.name if media.file else 'No file'} (ID: {media.id})")
        
        return {
            'dry_run': True,
            'identified_count': identified_count,
            'deleted_count': 0,
            'failed_count': 0,
            'total_size_freed_mb': 0,
            'errors': [],
        }
    
    # Process in batches
    processed = 0
    while processed < identified_count:
        batch = orphaned[processed:processed + batch_size]
        
        for media in batch:
            try:
                # Calculate file size before deletion
                file_size = 0
                if media.file and os.path.exists(media.file.path):
                    try:
                        file_size = os.path.getsize(media.file.path)
                    except OSError:
                        pass
                
                # Delete the physical file
                file_deleted = delete_media_file(media)
                
                # Delete the database record
                media_id = media.id
                media.delete()
                
                if file_deleted:
                    deleted_count += 1
                    total_size_freed += file_size
                    logger.info(f"Successfully deleted orphaned media: {media_id}")
                else:
                    failed_count += 1
                    error_msg = f"Failed to delete file for media: {media_id}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                failed_count += 1
                error_msg = f"Error deleting media {media.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        processed += len(batch)
        logger.info(f"Processed {processed}/{identified_count} orphaned media files")
    
    total_size_freed_mb = round(total_size_freed / (1024 * 1024), 2)
    
    logger.info(
        f"Cleanup complete: {deleted_count} deleted, {failed_count} failed, "
        f"{total_size_freed_mb} MB freed"
    )
    
    return {
        'dry_run': False,
        'identified_count': identified_count,
        'deleted_count': deleted_count,
        'failed_count': failed_count,
        'total_size_freed_mb': total_size_freed_mb,
        'errors': errors[:50],  # Limit errors in response
    }


def get_media_statistics() -> Dict[str, any]:
    """
    Get overall statistics about media storage.
    
    Returns:
        Dictionary containing various media statistics
    """
    total_media = Multimedia.objects.count()
    linked_media = Multimedia.objects.filter(
        content_type__isnull=False,
        object_id__isnull=False
    ).count()
    orphaned_media = Multimedia.objects.filter(
        content_type__isnull=True,
        object_id__isnull=True
    ).count()
    
    # Calculate storage size
    total_size = 0
    orphaned_size = 0
    
    for media in Multimedia.objects.all():
        if media.file:
            try:
                file_path = media.file.path
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    total_size += size
                    
                    if not media.content_type and not media.object_id:
                        orphaned_size += size
            except Exception:
                pass
    
    return {
        'total_media_count': total_media,
        'linked_media_count': linked_media,
        'orphaned_media_count': orphaned_media,
        'orphaned_percentage': round((orphaned_media / total_media * 100), 2) if total_media > 0 else 0,
        'total_storage_mb': round(total_size / (1024 * 1024), 2),
        'orphaned_storage_mb': round(orphaned_size / (1024 * 1024), 2),
        'media_root': settings.MEDIA_ROOT,
    }
