from django.urls import include, path
from rest_framework_nested import routers

from inspection.views import (
    InspectionStepViewSet,
    InspectionTypeStepViewSet,
    InspectionTypeViewSet,
    InspectionViewSet,
)

router = routers.DefaultRouter()
router.register("inspections", InspectionViewSet, basename="inspection")
router.register("steps", InspectionStepViewSet, basename="step")
router.register(
    "inspection-types", InspectionTypeViewSet, basename="inspection-type"
)
router.register(
    "inspection-type-steps",
    InspectionTypeStepViewSet,
    basename="inspection-type-step",
)

urlpatterns = [
    path("", include(router.urls)),
]
