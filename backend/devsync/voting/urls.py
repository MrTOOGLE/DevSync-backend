from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VotingViewSet, VotingOptionViewSet, VotingOptionChoiceViewSet, VotingCommentViewSet

router = DefaultRouter()
router.register(r'', VotingViewSet, basename='voting')
router.register(r'option', VotingOptionViewSet, basename='voting-option')
router.register(r'choice', VotingOptionChoiceViewSet, basename='voting-choice')
router.register(r'comment', VotingCommentViewSet, basename='voting-comment')

urlpatterns = [
    path('', include(router.urls)),
]
