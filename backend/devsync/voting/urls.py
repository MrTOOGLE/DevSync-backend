from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import VotingViewSet, VotingOptionViewSet, VotingOptionChoiceViewSet

router = DefaultRouter()
router.register(r'', VotingViewSet, basename='voting')


urlpatterns = [
    path('', include(router.urls)),
    path('option/', VotingOptionViewSet.as_view(), name='voting_option'),
    path('option-choice/', VotingOptionChoiceViewSet.as_view(), name='voting_option_choice'),
    path('comment/', include(router.urls)),
]
