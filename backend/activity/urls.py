from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=True)
# No ".json" suffix routes: nothing uses them, and actions such as `complete` would 500.
router.include_format_suffixes = False
router.register("events", views.SessionEventViewSet, basename="event")

urlpatterns = [
    path("subtopics/<int:pk>/reading/", views.ReadingView.as_view()),
    path("subtopics/<int:pk>/practice/", views.PracticeView.as_view()),
    path("attempts/", views.AttemptView.as_view()),
    path("reviews/", views.ReviewView.as_view()),
    path("home/", views.HomeView.as_view()),
    path("", include(router.urls)),
]
