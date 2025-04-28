from django.urls import path, include
from rest_framework_nested import routers
from .views import VotingViewSet, VotingOptionViewSet, VotingOptionChoiceViewSet, VotingCommentViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'projects/(?P<project_pk>[^/.]+)/votings', VotingViewSet, basename='voting')

voting_router = routers.NestedDefaultRouter(router, r'projects/(?P<project_pk[^/.]+)/votings', lookup='voting')
voting_router.register(r'options', VotingOptionViewSet, basename='voting-option')

voting_router = routers.NestedDefaultRouter(router, r'votings', lookup='voting')
voting_router.register(r'options', VotingOptionViewSet, basename='voting-option')
voting_router.register(r'choices', VotingOptionChoiceViewSet, basename='voting-choice')
voting_router.register(r'comments', VotingCommentViewSet, basename='voting-comment')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(voting_router.urls)),
]
