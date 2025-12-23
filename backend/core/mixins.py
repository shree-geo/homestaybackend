from rest_framework import exceptions

class ProtectedModelMixin:
    protected_field = "protected"

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            is_protected = getattr(original, self.protected_field)
            if is_protected:
                raise exceptions.ValidationError({"detail": "Cannot update protected object"})
            elif not is_protected and getattr(self, self.protected_field):
                changed_fields = {
                    field.name
                    for field in self._meta.fields
                    if getattr(original, field.name) != getattr(self, field.name)
                }
                if changed_fields - {self.protected_field}:
                    raise exceptions.ValidationError(
                        {"detail": f"Only '{self.protected_field}' can be changed when locking object."}
                    )
        return super().save(*args, **kwargs)