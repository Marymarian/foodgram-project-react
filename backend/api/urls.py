from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (TagsViewSet, IngredientsViewSet, RecipesViewSet,
                    FollowViewSet, UserViewSet, signup, get_token)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('users', FollowViewSet)
router_v1.register('recipes', RecipesViewSet, basename='recipes')
router_v1.register('tags', TagsViewSet)
router_v1.register('ingredients', IngredientsViewSet)
router_v1.register('users', UserViewSet, basename='users')

auth_path = [
    path('auth/signup/', signup),
    path('auth/token/', get_token)
]

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/', include(auth_path))
]
