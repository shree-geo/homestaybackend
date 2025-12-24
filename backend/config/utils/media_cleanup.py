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
from django.db import transaction, DatabaseError, IntegrityError
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
    
    # Use values_list to get IDs efficiently
    orphaned_ids = list(orphaned.values_list('id', flat=True))
    count = len(orphaned_ids)
    
    # Calculate total size and find oldest in single pass
    total_size = 0
    oldest_timestamp = None
    
    # Use iterator() to avoid loading all objects into memory at once
    for media in orphaned.iterator():
        if oldest_timestamp is None:
            oldest_timestamp = media.created_at
            
        if media.file:
            try:
                file_path = media.file.path
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            except (OSError, IOError) as e:
                # File system errors are non-critical for statistics
                logger.debug(f"Could not get size for media {media.id}: {e}")
    
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
        if not os.path.exists(file_path):
            return True
            
        os.remove(file_path)
        logger.info(f"Deleted file: {file_path}")
        
        # Try to remove empty parent directories (only within MEDIA_ROOT)
        try:
            parent_dir = os.path.dirname(file_path)
            media_root_abs = os.path.abspath(settings.MEDIA_ROOT)
            parent_dir_abs = os.path.abspath(parent_dir)
            
            # Ensure parent directory is within MEDIA_ROOT and is empty
            if (parent_dir_abs.startswith(media_root_abs) and 
                parent_dir_abs != media_root_abs and
                not os.listdir(parent_dir_abs)):
                os.rmdir(parent_dir_abs)
                logger.info(f"Removed empty directory: {parent_dir_abs}")
        except (OSError, IOError) as e:
            # Directory not empty or permission issue - safe to ignore
            logger.debug(f"Could not remove directory {parent_dir}: {e}")
            
        return True
    except (OSError, IOError) as e:
        logger.error(f"Failed to delete file for media {media.id}: {str(e)}")
        return False
    
    return True


def cleanup_orphaned_media(
    grace_period_hours: int = 24,
    dry_run: bool = False,
    batch_size: int = 100
) -> Dict[str, any]:
    """
    Clean up orphaned media files from database and disk.
    
    NOTE: Transaction safety - file deletion occurs BEFORE database deletion
    to prevent orphaned files if DB transaction fails. Only DB operations
    are wrapped in transactions.
    
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
        # Just report what would be deleted (use iterator for efficiency)
        sample_count = 0
        for media in orphaned.iterator():
            if sample_count >= 10:
                break
            logger.info(f"Would delete: {media.file.name if media.file else 'No file'} (ID: {media.id})")
            sample_count += 1
        
        return {
            'dry_run': True,
            'identified_count': identified_count,
            'deleted_count': 0,
            'failed_count': 0,
            'total_size_freed_mb': 0,
            'errors': [],
        }
    
    # Process in batches to avoid memory issues with large datasets
    processed = 0
    
    # Use iterator() for efficient batch processing
    orphaned_batch = orphaned.iterator(chunk_size=batch_size)
    
    for media in orphaned_batch:
        try:
            # Calculate file size before deletion
            file_size = 0
            if media.file:
                try:
                    file_path = media.file.path
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                except (OSError, IOError) as e:
                    logger.warning(f"Could not get size for media {media.id}: {e}")
            
            # Delete the physical file FIRST (outside transaction)
            # This prevents orphaned files if DB transaction rolls back
            file_deleted = delete_media_file(media)
            
            # Delete the database record (wrapped in transaction)
            media_id = media.id
            try:
                with transaction.atomic():
                    media.delete()
            except (DatabaseError, IntegrityError) as e:
                logger.error(f"Database error deleting media {media_id}: {e}")
                failed_count += 1
                error_msg = f"Database error for media {media_id}: {str(e)}"
                errors.append(error_msg)
                continue
            
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
            # Catch any unexpected errors to continue processing
            failed_count += 1
            error_msg = f"Unexpected error deleting media {media.id}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        processed += 1
        if processed % batch_size == 0:
            logger.info(f"Processed {processed}/{identified_count} orphaned media files")
    
    if processed > 0:
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
    
    # Calculate storage size efficiently using iterator()
    total_size = 0
    orphaned_size = 0
    
    # Use iterator() to process records efficiently without loading all into memory
    for media in Multimedia.objects.iterator():
        if media.file:
            try:
                file_path = media.file.path
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    total_size += size
                    
                    # Check if this media is orphaned
                    if not media.content_type and not media.object_id:
                        orphaned_size += size
            except (OSError, IOError) as e:
                # File system errors are non-critical for statistics
                logger.debug(f"Could not get size for media {media.id}: {e}")
    
    return {
        'total_media_count': total_media,
        'linked_media_count': linked_media,
        'orphaned_media_count': orphaned_media,
        'orphaned_percentage': round((orphaned_media / total_media * 100), 2) if total_media > 0 else 0,
        'total_storage_mb': round(total_size / (1024 * 1024), 2),
        'orphaned_storage_mb': round(orphaned_size / (1024 * 1024), 2),
        'media_root': settings.MEDIA_ROOT,
    }
