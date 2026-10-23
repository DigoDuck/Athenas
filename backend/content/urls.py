from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=True)
# No ".json" suffix routes: nothing uses them, and actions such as `complete` would 500.
router.include_format_suffixes = False
router.register("flashcards", views.FlashcardViewSet, basename="flashcard")

urlpatterns = [
    path("subtopics/<int:pk>/content/", views.ContentView.as_view()),
    path("subtopics/<int:pk>/content/preview/", views.ContentPreviewView.as_view()),
    path("reviews/today/", views.ReviewTodayView.as_view()),
    path("images/<str:name>/", views.ImageView.as_view()),
    path("themes/", views.ThemeView.as_view()),
    path("themes/preview/", views.ThemeView.as_view(save=False)),
    path("", include(router.urls)),
]
