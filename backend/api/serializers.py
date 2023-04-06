from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from recipes.models import (
    FavouriteRecipes,
    Ingredients,
    IngredientsInRecipe,
    Recipes,
    ShoppingLists,
    Tags,
)
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueValidator
from users.models import Follow

User = get_user_model()


class GetIngredientsMixin:
    """Миксин для рецептов."""

    def get_ingredients(self, obj):
        """Получение ингредиентов."""
        return obj.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("ingredients_amount__amount"),
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализация объектов типа User. Создание пользователя."""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class CustomUserListSerializer(UserSerializer):
    """Сериализация объектов типа User. Просмотр пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj.id).exists()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
        )
        read_only_fields = ("is_subscribed",)


class TagsSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа Tags. Список тегов."""

    class Meta:
        model = Tags
        fields = "__all__"


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа Ingredients. Список ингредиентов."""

    class Meta:
        model = Ingredients
        fields = "__all__"


class RecipesReadSerializer(GetIngredientsMixin, serializers.ModelSerializer):
    """Сериализация объектов типа Recipes. Чтение рецептов."""

    tags = TagsSerializer(many=True)
    author = CustomUserListSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(default=False)
    in_the_shopping_list = serializers.BooleanField(default=False)

    class Meta:
        model = Recipes
        fields = "__all__"


class RecipesWriteSerializer(GetIngredientsMixin, serializers.ModelSerializer):
    """Сериализация объектов типа Recipes. Запись рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tags.objects.all()
    )
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = "__all__"
        read_only_fields = ("author",)

    def validate(self, data):
        """Проверка рецепта."""
        ingredients = self.initial_data["ingredients"]
        ingredient_list = []
        if not ingredients:
            raise serializers.ValidationError(
                "Должен быть хотя бы 1 ингредиент."
            )
        for item in ingredients:
            ingredient = get_object_or_404(Ingredients, id=item["id"])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    "Ингредиенты не могут повторяться."
                )
            if int(item.get("amount")) < 1:
                raise serializers.ValidationError("Минимальное количество = 1")
            ingredient_list.append(ingredient)
        data["ingredients"] = ingredients
        return data

    def validate_cooking_time(self, time):
        """Проверка времени рецепта."""
        if int(time) < 1:
            raise serializers.ValidationError("Минимальное время = 1")
        return time

    def add_ingredients_and_tags(self, instance, **validate_data):
        """Добавление тегов ингредиентов."""
        ingredients = validate_data["ingredients"]
        tags = validate_data["tags"]
        for tag in tags:
            instance.tags.add(tag)

        IngredientsInRecipe.objects.bulk_create(
            [
                IngredientsInRecipe(
                    recipe=instance,
                    ingredient_id=ingredient.get("id"),
                    amount=ingredient.get("amount"),
                )
                for ingredient in ingredients
            ]
        )
        return instance

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = super().create(validated_data)
        return self.add_ingredients_and_tags(
            recipe, ingredients=ingredients, tags=tags
        )

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        instance = self.add_ingredients_and_tags(
            instance, ingredients=ingredients, tags=tags
        )
        return super().update(instance, validated_data)


class RecipeAddingSerializer(serializers.ModelSerializer):
    """
    Сериализация объектов типа Recipes.
    Добавление в избранное/список покупок.
    """

    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа Follow. Подписки."""

    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_following = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_following",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        """Отображение подписки на пользователя."""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj.id).exists()

    def get_recipes(self, obj):
        """Список подписок с рецептами."""
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[: int(limit)]
        return RecipeAddingSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Общее количество рецептов пользователя."""
        return obj.author.recipes.all().count()


class CheckFollowSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа Follow. Проверка подписки."""

    class Meta:
        model = Follow
        fields = ("user", "author")

    # def validate(self, obj):
    #     """Валидация подписки."""
    #     user = obj["user"]
    #     author = obj["author"]
    #     subscribed = user.follower.filter(author=author).exists()

    #     if self.context.get("request").method == "POST":
    #         if user == author:
    #             raise serializers.ValidationError(
    #                 "Нельзя подписаться на самого себя!"
    #             )
    #         if subscribed:
    #             raise serializers.ValidationError("Вы уже подписаны!")
    #     if self.context.get("request").method == "DELETE":
    #         if user == author:
    #             raise serializers.ValidationError("Нельзя отписаться!")
    #         if not subscribed:
    #             raise serializers.ValidationError("Вы уже не подписаны!")
    #     return obj


class CheckFavouriteSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа FavouriteRecipes. Проверка избранного."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipes.objects.all())

    class Meta:
        model = FavouriteRecipes
        fields = ("user", "recipe")

    # def validate(self, obj):
    #     """Валидация избранного."""
    #     user = self.context["request"].user
    #     recipe = obj["recipe"]
    #     favorites = user.favorites.filter(recipe=recipe).exists()

    #     if self.context.get("request").method == "POST" and favorites:
    #         raise serializers.ValidationError(
    #             "Рецепт уже добавлен в избранное!"
    #         )
    #     if self.context.get("request").method == "DELETE" and not favorites:
    #         raise serializers.ValidationError("Рецепт не в избранном!")
    #     return obj


class CheckShoppingListsSerializer(serializers.ModelSerializer):
    """Сериализация объектов типа ShoppingLists. Проверка списка покупок."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipes.objects.all())

    class Meta:
        model = ShoppingLists
        fields = ("user", "recipe")

    # def validate(self, obj):
    #     """Валидация списка покупок."""
    #     user = self.context["request"].user
    #     recipe = obj["recipe"]
    #     shop_list = user.list.filter(recipe=recipe).exists()

    #     if self.context.get("request").method == "POST" and shop_list:
    #         raise serializers.ValidationError(
    #             "Рецепт уже есть в списке покупок!"
    #         )
    #     if self.context.get("request").method == "DELETE" and not shop_list:
    #         raise serializers.ValidationError(
    #             "Рецепт отсутствует в спске покупок!"
    #         )
    #     return
