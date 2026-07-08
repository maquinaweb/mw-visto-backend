from django.contrib import admin


class SoftDeleteAdminMixin:
    def get_queryset(self, request):
        return self.model.all_objects.all()

    def is_deleted(self, obj):
        if obj.deleted_at:
            return "Deletado"
        return ""

    is_deleted.short_description = "Status"

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if isinstance(list_display, tuple):
            list_display = list(list_display)
        if "is_deleted" not in list_display:
            list_display.append("is_deleted")
        return list_display

    def get_list_filter(self, request):
        list_filter = list(super().get_list_filter(request) or [])
        if "deleted_at" not in list_filter:
            list_filter.append("deleted_at")
        return list_filter

    actions = ["restore_selected", "hard_delete_selected"]

    @admin.action(description="Restaurar selecionados")
    def restore_selected(self, request, queryset):
        count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{count} objeto(s) restaurado(s).")

    @admin.action(description="Deletar permanentemente")
    def hard_delete_selected(self, request, queryset):
        count, _ = queryset.delete()
        self.message_user(request, f"{count} objeto(s) deletado(s) permanentemente.")
