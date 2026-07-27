from django.urls import include, path
from rest_framework_nested import routers

from inspection.views import (
    InspectionStepViewSet,
    InspectionTypeStepViewSet,
    InspectionTypeViewSet,
    InspectionViewSet,
    InspectionMotiveViewSet,
    ProviderViewSet,
    TorryTechQueryViewSet,
    AutomationRuleViewSet,
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
router.register(
    "inspection-motives",
    InspectionMotiveViewSet,
    basename="inspection-motive",
)
router.register("providers", ProviderViewSet, basename="provider")
router.register(
    "torry-tech-queries", TorryTechQueryViewSet, basename="torry-tech-query"
)
router.register(
    "automation-rules",
    AutomationRuleViewSet,
    basename="automation-rule",
)
router.register(
    "activator-automation-rules",
    AutomationRuleViewSet,
    basename="activator-automation-rule",
)

urlpatterns = [
    path("", include(router.urls)),
]
