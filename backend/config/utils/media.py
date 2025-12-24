import os
from typing import Type
from shutil import move
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Model, QuerySet
from core.models import Multimedia


def move_files(media_qs: QuerySet[Multimedia], instance: Type[Model], field_name: str) -> None:
    media_dir = settings.MEDIA_ROOT
    model_name = instance.__class__.__name__.lower()
    for media in media_qs:
        new_path = f"{model_name}/{instance.id}/{field_name}/"
        if media.protected:
            new_path = f"protected/{new_path}"

        filename = media.file.name.split("/")[-1]
        old_media_path = os.path.join(media_dir, media.file.path)
        if not os.path.exists(os.path.join(media_dir, new_path)):
            os.makedirs(os.path.join(media_dir, new_path))

        new_media_path = os.path.join(media_dir, new_path, filename)
        try:
            move(old_media_path, new_media_path)
            media.file = new_path + filename
            media.save()
        except FileNotFoundError:
            media.file = None
            media.save()


def get_related_files_by_field_name(field_name: str, instance: Type[Model]):
    """
    Get related files for a given field name and instance from the Multimedia model.
    Args:
        field_name (str): name of the field used when uploading files.
        instance (Type[Model]): The instance of the model to get related files for.
    """

    try:
        model_ = instance.__class__
        content_type = ContentType.objects.get_for_model(model_)
        id_ = instance.id
        related_files = Multimedia.objects.filter(
            content_type=content_type,
            object_id=id_,
            field_name=field_name,
        )
        return related_files
    except ContentType.DoesNotExist:
        return None


def delete_associated_files(instance: Type[Model], field_name: str, files: list[int]) -> None:
    content_type = ContentType.objects.get_for_model(instance)
    Multimedia.objects.filter(
        content_type=content_type,
        object_id=instance.id,
        field_name=field_name,
    ).exclude(id__in=files).delete()


@transaction.atomic
def assign_files_to_instance(instance: Type[Model], field_name: str, files: list[int]) -> None:
    """
    Assign files to a given instance and field name.
    Args:
        instance (Type[Model]): instance of the model to which files will be assigned.
        field_name (str): name of the field
        files (list): list of file IDs to assign to the instance.
    """
    content_type = ContentType.objects.get_for_model(instance)
    delete_associated_files(instance, field_name, files)
    multimedia = Multimedia.objects.filter(id__in=files)
    multimedia.update(content_type=content_type, object_id=instance.id, field_name=field_name)
    move_files(multimedia, instance, field_name)


def get_uploaded_media(instance: Type[Model]) -> QuerySet[Multimedia] | None:
    """
    Get uploaded media for a given instance.
    Args:
        instance (Type[Model]): instance of the model to get uploaded media for.
    """
    try:
        content_type = ContentType.objects.get_for_model(instance)
        uploaded_media = Multimedia.objects.filter(
            content_type=content_type,
            object_id=instance.id,
        )
        return uploaded_media
    except ContentType.DoesNotExist:
        return None


def duplicate_media_queryset(files: list[int]) -> list[int]:
    """
    Create duplicate instance of media.
    Args:
        files (list): list of media IDs to duplicate.
    """
    result = []
    qs = Multimedia.objects.filter(id__in=files)
    for f in qs:
        f.pk = None
        f.save()
        result.append(f.id)
    return result
