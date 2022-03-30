from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView

from ..forms import UserSignupForm, UserLoginForm, PostForm
from ..models import Post, User
from ..services import decode_token


def main(request):
    """Guide page where all the pages' description and link present"""
    return render(request, 'post_app/url-guide-page.html')


def signup(request):
    """Signup user page"""
    form = UserSignupForm()
    context = {'form': form}
    return render(request, 'post_app/user_signup.html', context)


def login(request):
    """Login user page"""
    form = UserLoginForm()
    context = {'form': form}
    return render(request, 'post_app/user_login.html', context)


class PostList(ListView):
    queryset = Post.objects.select_related('created_by')
    template_name = 'post_app/post_listing.html'
    model = Post
    context_object_name = 'posts'


class PostDetail(LoginRequiredMixin, DetailView):
    queryset = Post.objects.select_related('created_by')
    template_name = 'post_app/post_detail.html'
    model = Post
    context_object_name = 'post'


class PostCreate(LoginRequiredMixin, CreateView):
    """
    Get request: renders page with creation post form
    Post request:
        validates provided form
        gets user by token
        creates user post
    """
    def get(self, request, *args, **kwargs):
        context = {'form': PostForm()}
        return render(request, 'post_app/post_form.html', context)

    def post(self, request, *args, **kwargs):
        form = PostForm(request.POST)
        if form.is_valid():
            token = request.COOKIES.get('token')
            payload = decode_token(token)

            user = User.objects.filter(id=payload['id']).first()
            post = form.save(commit=False)
            post.created_by = user
            post.save()

            return redirect(reverse('detail', kwargs={'pk': post.pk}))

        return render(request, 'post_app/post_form.html', {'form', form})
