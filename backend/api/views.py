from http import HTTPStatus
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import (viewsets, status, serializers, mixins)
from rest_framework.decorators import action, api_view, permission_classes
from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.db import IntegrityError
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated, AllowAny
from .filters import IngredientsSearchFilter, RecipesFilter
from .permissions import IsAdmin, IsAdminOrReadOnly, IsAdminAuthorOrReadOnly
from users.models import User, Follow
from recipes.models import (Tags, Ingredients, Recipes, ShoppingLists,
                            IngredientsInRecipe, FavouriteRecipes)
from .serializers import (CheckFavouriteSerializer, GetTokenSerializer,
                          CheckFollowSerializer, FollowSerializer,
                          IngredientsSerializer, RecipeAddingSerializer,
                          RecipesReadSerializer, RecipesWriteSerializer,
                          TagsSerializer, UserSerializer, SignUpSerializer,
                          CheckShoppingListsSerializer)
from foodgram.settings import DOMAIN_NAME


FILE_NAME = 'shopping_list.txt'
TITLE_SHOP_LIST = 'Список покупок:\n\nНаименование - Кол-во/Ед.изм.\n'


class ListRetrieveViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                          mixins.RetrieveModelMixin):
    permission_classes = (IsAdminOrReadOnly, )


class UserViewSet(viewsets.ModelViewSet):
    """
    Администратор получает список пользователей, может создавать
    пользователя. Пользователь по url 'users/me/' может получать и изменять
    свои данные, кроме поля 'Роль'.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin, )
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    pagination_class = PageNumberPagination

    @action(methods=('get', 'patch',), detail=False, url_path='me',
            permission_classes=(IsAuthenticated,))
    def user_own_account(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(user, data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=user.role, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    Пользователь отправляет свои 'username' и 'email' на 'auth/signup/ и
    получает код подтверждения на email.
    """
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    email = serializer.validated_data['email']
    try:
        user, created = User.objects.get_or_create(username=username,
                                                   email=email)
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {confirmation_code}',
            DOMAIN_NAME,
            [user.email],
            fail_silently=False,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    except IntegrityError:
        raise serializers.ValidationError(
            'Данные имя пользователя или Email уже зарегистрированы'
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """
    Пользователь отправляет свои 'username' и 'confirmation_code'
    на 'auth/token/ и получает токен.
    """
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    confirmation_code = serializer.validated_data['confirmation_code']
    user = get_object_or_404(User, username=username)
    if default_token_generator.check_token(user, confirmation_code):
        token = str(AccessToken.for_user(user))
        return Response({'token': token}, status=status.HTTP_200_OK)
    raise serializers.ValidationError('Введен неверный код.')


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
