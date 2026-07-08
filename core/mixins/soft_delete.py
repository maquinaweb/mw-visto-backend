from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModelMixin(models.Model):
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Deletado em",
        help_text="Data e hora em que a instância foi deletada (soft delete)",
    )
    deleted_by_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Deletado por",
        help_text="Usuário que deletou a instância (soft delete)",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False, user_id=None):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        self.deleted_at = timezone.now()
        self.deleted_by_id = user_id
        self.save(update_fields=["deleted_at", "deleted_by_id"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by_id = None
        self.save(update_fields=["deleted_at", "deleted_by_id"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def deleted_by(self):
        if not self.deleted_by_id:
            return None
        if not hasattr(self, "_cached_user"):
            from shared_auth.utils import get_user_model

            User = get_user_model()
            self._cached_user = User.objects.get_or_fail(self.deleted_by_id)
        return self._cached_user


class SoftDeleteViewSetMixin:
    """Mixin para ViewSets que usam SoftDeleteModelMixin.

    Automaticamente passa o request.user.id ao método delete() do model.
    """

    def perform_destroy(self, instance):
        user_id = getattr(self.request.user, "id", None)
        instance.delete(user_id=user_id)
