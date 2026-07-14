from django.urls import include, path
from rest_framework import routers

from sga.views.associate import AssociateViewSet

router = routers.DefaultRouter()
router.register("associates", AssociateViewSet, basename="associate")

urlpatterns = [
    path("", include(router.urls)),
]
