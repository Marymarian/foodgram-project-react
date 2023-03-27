from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import (viewsets, mixins)
from rest_framework.decorators import action
from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from .filters import IngredientsSearchFilter, RecipesFilter
from .permissions import IsAdminOrReadOnly, IsAdminAuthorOrReadOnly
from users.models import Follow
from recipes.models import (Tags, Ingredients, Recipes, ShoppingLists,
                            IngredientsInRecipe, FavouriteRecipes)
from .serializers import (CheckFavouriteSerializer,
                          CheckFollowSerializer, FollowSerializer,
                          IngredientsSerializer, RecipeAddingSerializer,
                          RecipesReadSerializer, RecipesWriteSerializer,
                          TagsSerializer, CheckShoppingListsSerializer)

User = get_user_model()

FILE_NAME = 'shopping_list.txt'
TITLE_SHOP_LIST = 'Список покупок:\n\nНаименование - Кол-во/Ед.изм.\n'


class ListRetrieveViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                          mixins.RetrieveModelMixin):
    permission_classes = (IsAdminOrReadOnly, )


class TagsViewSet(ListRetrieveViewSet):
    """Класс взаимодействия с моделью Tags. Вьюсет для списка тегов."""
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = None


class IngredientsViewSet(ListRetrieveViewSet):
    """Класс взаимодействия с моделью Ingredients.Вьюсет для ингредиентов."""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_class = IngredientsSearchFilter


class RecipesViewSet(viewsets.ModelViewSet):
    """Класс взаимодействия с моделью Recipes. Вьюсет для рецептов."""
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_class = RecipesFilter

    def get_serializer_class(self):
        """Сериализаторы для рецептов."""
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    def get_queryset(self):
        """Резюме по объектам с помощью annotate()."""
        if self.request.user.is_authenticated:
            return Recipes.objects.annotate(
                is_favourited=Exists(FavouriteRecipes.objects.filter(
                    user=self.request.user, recipe__pk=OuterRef('pk'))
                ),
                in_the_shop_list=Exists(ShoppingLists.objects.filter(
                    user=self.request.user, recipe__pk=OuterRef('pk'))
                )
            )
        else:
            return Recipes.objects.annotate(
                is_favourited=Value(False, output_field=BooleanField()),
                n_the_shop_list=Value(False, output_field=BooleanField())
            )

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def favourite(self, request, pk=None):
        """В избранное."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckFavouriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(FavouriteRecipes, request.user, pk)

    @favourite.mapping.delete
    def del_favorite(self, request, pk=None):
        """Убрать из избранного."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckFavouriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.delete_object(FavouriteRecipes, request.user, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_list(self, request, pk=None):
        """В список покупок."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckShoppingListsSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.add_object(ShoppingLists, request.user, pk)

    @shopping_list.mapping.delete
    def del_shopping_list(self, request, pk=None):
        """Убрать из списка покупок."""
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        serializer = CheckShoppingListsSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return self.delete_object(ShoppingLists, request.user, pk)

    @transaction.atomic()
    def add_object(self, model, user, pk):
        "Создание и сохранение объектов."
        recipe = get_object_or_404(Recipes, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeAddingSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @transaction.atomic()
    def delete_object(self, model, user, pk):
        "Удаление объектов."
        model.objects.filter(user=user, recipe__id=pk).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=['get'], detail=False, permission_classes=(IsAuthenticated,)
    )
    def download_shopping_list(self, request):
        "Выгрузка списка покупок."
        ingredients = IngredientsInRecipe.objects.filter(
            recipe__list__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(total=Sum('amount'))
        result = TITLE_SHOP_LIST
        result += '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["total"]}/'
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        response = HttpResponse(result, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={FILE_NAME}'
        return


class FollowViewSet(UserViewSet):
    """Класс взаимодействия с моделью Follow.Вьюсет подписок."""
    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    @transaction.atomic()
    def follow(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = CheckFollowSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        result = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(result, context={'request': request})
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @follow.mapping.delete
    @transaction.atomic()
    def del_follow(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        serializer = CheckFollowSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user.follower.filter(author=author).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """"Подписчики."""
        user = request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
