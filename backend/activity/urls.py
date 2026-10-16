from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=True)
router.register("events", views.SessionEventViewSet, basename="event")

urlpatterns = [
    path("subtopics/<int:pk>/reading/", views.ReadingView.as_view()),
    path("", include(router.urls)),
]
