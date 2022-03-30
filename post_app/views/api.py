from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Post, User, Like
from ..renderers import UserJSONRenderer
from ..serializers import UserSignupSerializer, UserLoginSerializer, UserSerializer
from ..services import decode_token, parse_date


def analytics_api(request):
    """
    Gets parameters date_from and date_to
    Returns likes that have been made during specified time range
    """
    _from = request.GET.get('date_from')
    _to = request.GET.get('date_to')

    if not _from or not _to:
        return HttpResponse(f'<h1>Please specify params date_from, date_to</h1>')

    date_from = parse_date(request.GET.get('date_from'))
    date_to = parse_date(request.GET.get('date_to'))

    r = Like.made_at_time_range(date_from, date_to)
    return JsonResponse({'likes_made': r})


def like_api(request, **kwargs):
    """Toggles user like for post (sets dislike or like)"""
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        payload = decode_token(token)
        user = User.objects.get(id=payload['id'])
        post = Post.objects.get(id=kwargs['pk'])

        if not post.has_user_liked(user):
            post.set_like(user)
            return JsonResponse({'status': 'like_set'})
        else:
            post.set_dislike(user)
            return JsonResponse({'status': 'dislike_set'})
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')


class SignupAPIView(APIView):
    """Receives json and validating values to create user:
    {
        "email": value
        "username": value
        "token": value
        "password": value
     }
    """
    permission_classes = (AllowAny,)
    serializer_class = UserSignupSerializer

    def post(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """Receives json, authenticates user and sets user cookie:
    {
        "email": value
        "password": value
    }
    """
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserLoginSerializer

    def post(self, request):
        user = request.data.get('user', {})
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.data

        response = Response()
        response.set_cookie(key='token', value=serializer_data['token'])
        response.data = serializer_data
        response.status_code = 200

        return response


class UserAPIView(APIView):
    """
    Gets user by provided token and renders user info:
    email, username, last_request, last_login
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    renderer_classes = (UserJSONRenderer,)

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
