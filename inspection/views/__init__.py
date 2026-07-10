from inspection.views.inspection import InspectionViewSet
from inspection.views.step import InspectionStepViewSet
from inspection.views.inspection_type import InspectionTypeViewSet
from inspection.views.inspection_type_step import InspectionTypeStepViewSet
from inspection.views.inspection_motive import InspectionMotiveViewSet

__all__ = [
    "InspectionViewSet",
    "InspectionStepViewSet",
    "InspectionTypeViewSet",
    "InspectionTypeStepViewSet",
    "InspectionMotiveViewSet",
]
