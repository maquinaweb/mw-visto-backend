from inspection.models import InspectionMotive, Inspector, TorryTechQuery
from inspection.models import InspectionTypeStep
from inspection.models import InspectionType
from django.contrib import admin

from core.mixins.soft_delete_admin import SoftDeleteAdminMixin
from inspection.models.inspection import Inspection
from inspection.models.step import InspectionStep


class InspectionAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = [
        "title",
        "status",
        "hash",
        "deleted_by",
    ]


class TorryTechQueryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = [
        "plate",
        "chassi",
        "cons",
        "status_consulta",
        "success",
        "created_at",
    ]
    search_fields = ["plate", "chassi", "id_pesquisa"]


admin.site.register(Inspection, InspectionAdmin)
admin.site.register(InspectionStep)
admin.site.register(InspectionType)
admin.site.register(InspectionTypeStep)
admin.site.register(InspectionMotive)
admin.site.register(Inspector)
admin.site.register(TorryTechQuery, TorryTechQueryAdmin)
