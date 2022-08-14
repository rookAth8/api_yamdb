from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Comment, Genre, Review, Title, User
from .filters import TitleFilter
from .permissions import IsAdminOrReadOnly, IsRoleAdmin
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReviewSerializer, SignupSerializer,
                          TitleGetSerializer, TitlePostSerializer,
                          TokenSerializer, UserEditSerializer, UserSerializer)


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Genre.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return TitlePostSerializer
        return TitleGetSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsRoleAdmin,)
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'username'
    lookup_value_regex = r'[\w\@\.\+\-]+'
    search_fields = ('username',)

    @action(
        methods=[
            'GET',
            'PATCH',
        ],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,),
        serializer_class=UserEditSerializer,
    )
    def users_own_profile(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([AllowAny, ])
def token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = request.data.get('username')
    user = get_object_or_404(User, username=username)
    confirmation_code = request.data.get('confirmation_code')
    if default_token_generator.check_token(user, confirmation_code):
        token_for_user = AccessToken.for_user(user)
        return Response(
            {'token': token_for_user},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny, ])
def signup(request):
    """Отправка сообщения на введенный e-mail для получения кода"""
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        send_code_for_confirm(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_code_for_confirm(user):
    """Отправка кода подтверждения"""
    subject = 'Код подтверждения от YaMBb'
    confirmation_code = default_token_generator.make_token(user)
    message = f'Ваш код подтверждения - {confirmation_code}'
    from_email = None
    recipient_list = [user.email]
    return send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list
    )


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly | IsAdminOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs['titles_id']
        title = get_object_or_404(Title, id=title_id)
        return Review.objects.filter(title=title)

    def perform_create(self, serializer):
        title_id = self.kwargs['titles_id']
        title = get_object_or_404(Title, id=title_id)
        author = self.request.user
        if Review.objects.filter(
            author=author
        ).filter(title=title).exists():
            raise ParseError(
                'Можно оставить только один отзыв'
            )
        serializer.save(
            author=author,
            title=title,
        )

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied('Изменение чужих отзывов запрещено')
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.author == self.request.user or (
            user.is_admin or user.is_superuser or user.is_moderator
        ):
            return super().perform_destroy(instance)
        raise PermissionDenied('Нет прав на удаление')


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly | IsAdminOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs['titles_id']
        title = get_object_or_404(Title, id=title_id)
        review_id = self.kwargs['review_id']
        review = get_object_or_404(Review, id=review_id, title=title)
        return Comment.objects.filter(review=review)

    def perform_create(self, serializer):
        title_id = self.kwargs['titles_id']
        title = get_object_or_404(Title, id=title_id)
        review_id = self.kwargs['review_id']
        review = get_object_or_404(Review, id=review_id, title=title)
        serializer.save(author=self.request.user, review=review)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied('Изменение чужих комментариев запрещено')
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.author == self.request.user or (
            user.is_admin or user.is_superuser or user.is_moderator
        ):
            return super().perform_destroy(instance)
        raise PermissionDenied('Нет прав на удаление')
