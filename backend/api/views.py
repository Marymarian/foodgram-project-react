from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (
    FavouriteRecipes,
    Ingredients,
    IngredientsInRecipe,
    Recipes,
    ShoppingLists,
    Tags,
)
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from users.models import Follow

from .filters import IngredientsSearchFilter, RecipesFilter
from .permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from .serializers import (
    FollowSerializer,
    IngredientsSerializer,
    RecipeAddingSerializer,
    RecipesReadSerializer,
    RecipesWriteSerializer,
    TagsSerializer,
)

User = get_user_model()

FILE_NAME = "shopping-list.txt"
TITLE_SHOP_LIST = "Список покупок с сайта Foodgram:\n\n"


class ListRetrieveViewSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    permission_classes = (IsAdminOrReadOnly,)


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
                is_favourited=Exists(
                    FavouriteRecipes.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef("pk")
                    )
                ),
                in_the_shop_list=Exists(
                    ShoppingLists.objects.filter(
                        user=self.request.user, recipe__pk=OuterRef("pk")
                    )
                ),
            )
        else:
            return Recipes.objects.annotate(
                is_favourited=Value(False, output_field=BooleanField()),
                n_the_shop_list=Value(False, output_field=BooleanField()),
            )

    @transaction.atomic()
    def add_object(self, model, user, pk):
        "Добавление объектов."
        recipe = get_object_or_404(Recipes, id=pk)
        try:
            model.objects.create(user=user, recipe=recipe)
        except IntegrityError:
            return Response(
                {"errors": "Рецепт уже добавлен!"},
                status=HTTPStatus.BAD_REQUEST,
            )
        serializer = RecipeAddingSerializer(recipe)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @transaction.atomic()
    def delete_object(self, model, user, pk):
        "Удаление объектов."
        object_list = model.objects.filter(user=user, recipe__id=pk)
        if not object_list.exists():
            return Response(
                {"errors": "Такого рецепта нет!"},
                status=HTTPStatus.BAD_REQUEST,
            )
        object_list.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        """Добавить в избранное избранное и удалить."""
        if request.method == "POST":
            return self.add_object(FavouriteRecipes, request.user, pk)
        return self.delete_object(FavouriteRecipes, request.user, pk)

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        """Добавить в список покупок и удалить."""
        if request.method == "POST":
            return self.add_object(ShoppingLists, request.user, pk)
        return self.delete_object(ShoppingLists, request.user, pk)

    @action(
        methods=["POST", "DELETE"],
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Получение списка покупок в файле."""
        shopping_list = ShoppingLists.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_list]
        buy_list = (
            IngredientsInRecipe.objects.filter(recipe__in=recipes)
            .values("ingredient")
            .annotate(amount=Sum("amount"))
        )

        result = TITLE_SHOP_LIST
        for item in buy_list:
            ingredient = Ingredients.objects.get(pk=item["ingredient"])
            amount = item["amount"]
            result += (
                f"{ingredient.name}, {amount} "
                f"{ingredient.measurement_unit}\n"
            )

        response = HttpResponse(result, content_type="text/plain")
        response["Content-Disposition"] = f"attachment; filename={FILE_NAME}"

        return response


class FollowViewSet(UserViewSet):
    """Класс взаимодействия с моделью Follow.Вьюсет подписок."""

    @action(
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        """Подписаться/отписаться."""
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            serializer = FollowSerializer(
                author, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            try:
                Follow.objects.create(user=user, author=author)
            except IntegrityError:
                return Response(
                    {"errors": "Вы уже подписаны!"},
                    status=HTTPStatus.BAD_REQUEST,
                )
            return Response(serializer.data, status=HTTPStatus.CREATED)

        subscription = Follow.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response(
                {"errors": "Подписка не найдена!"},
                status=HTTPStatus.BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Подписчики."""
        user = request.user
        queryset = Follow.objects.filter(following_user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, context={"request": request}, many=True
        )
        return self.get_paginated_response(serializer.data)
