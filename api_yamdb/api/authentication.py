from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.response import Response

from api.serializers import (SignupSerializer, TokenSerializer)
from users.models import User


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
