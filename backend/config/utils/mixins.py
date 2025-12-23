from abc import abstractmethod
from rest_framework import decorators, permissions, serializers
from core import models
from .media import assign_files_to_instance, get_related_files_by_field_name


class MultimediaSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = models.Multimedia
        fields = "__all__"


class PublicRouteMixin:
    """Mixin that provides public route"""

    @abstractmethod
    def filter_public_qs(self):
        """return filtered queryset for public route"""
        raise NotImplementedError

    @decorators.action(["GET"], detail=False, permission_classes=[permissions.AllowAny])
    def public(self, request, *args, **kwargs):
        self.queryset = self.filter_public_qs()
        return self.list(request, *args, **kwargs)


class RetriveMediaMixin:
    """Mixin that retrieve media grouped by field name"""

    def to_representation(self, instance):
        """
        Override the to_representation method to include media files
        grouped by field name.
        """
        data = super().to_representation(instance)
        media_data = {}
        media_fields = getattr(self.Meta, "media_fields", [])
        for field in media_fields:
            qs = get_related_files_by_field_name(instance=instance, field_name=field)
            serializer = MultimediaSerializer(qs, many=True, context=self.context)
            media_data[field] = serializer.data
        # data.update(media_data)
        return {**data, **media_data}


class CreateMediaMixin:
    """
    Mixin that handles media fields in serializers.
    ---
    Create:
    1. Assigns addtional field `serializers.IntegerField` to its subclass.
    2. Extracts values from those fields and contentypes from model instance.
    3. Assigns contentypes to existing (uploaded) file instances.
    ---
    Update:
    Deletes existing file instances if not in the list of files.
    Performs create (same as above) for new files.
    ---
    Only works with `serializers.ModelSerializer` subclasses.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media_fields = getattr(self.Meta, "media_fields", [])
        for field in self.media_fields:
            self.fields[field] = serializers.ListField(write_only=True, required=False)

    def __extract_media_fields(self, validated_data):
        fields = {}
        for field_name in self.media_fields:
            try:
                value = validated_data.pop(field_name)
                fields[field_name] = value
            except KeyError:
                ...
        return fields

    def __handle_media_fields(self, instance, media_fields):
        """
        Handle media fields by assigning files to the instance.
        """
        for field_name, value in media_fields.items():
            value = value if isinstance(value, list) else [value]
            assign_files_to_instance(instance, field_name=field_name, files=value)
        return instance

    def create(self, validated_data):
        """
        Override the create method to handle media fields.
        """
        media_fields = self.__extract_media_fields(validated_data)
        instance = super().create(validated_data)
        self.__handle_media_fields(instance, media_fields)
        return instance

    def update(self, instance, validated_data):
        """
        Override the update method to handle media fields.

        """
        media_fields = getattr(self.Meta, "media_fields", [])
        for field in media_fields:
            media = validated_data.pop(field, None)
            if media is not None:
                media_fields = media if isinstance(media, list) else [media]
                assign_files_to_instance(instance, field_name=field, files=media)
        return super().update(instance, validated_data)


class GenericMediaMixin(CreateMediaMixin, RetriveMediaMixin): ...
