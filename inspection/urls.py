from django.urls import include, path
from rest_framework_nested import routers

from inspection.views.inspection import InspectionViewSet
from inspection.views.step import InspectionStepViewSet

router = routers.DefaultRouter()
router.register("inspections", InspectionViewSet, basename="inspection")
router.register("steps", InspectionStepViewSet, basename="step")

urlpatterns = [
    path("", include(router.urls)),
]
