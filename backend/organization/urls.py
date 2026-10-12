from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=True)
router.register("areas", views.AreaViewSet)
router.register("concepts", views.ConceptViewSet)
router.register("subtopics", views.SubtopicViewSet)
router.register("tracks", views.TrackViewSet)
router.register("steps", views.StepViewSet)

urlpatterns = [
    path("settings/", views.SettingsView.as_view()),
    path("", include(router.urls)),
]
