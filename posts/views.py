from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User


def index(request):
    latest = Post.objects.select_related('group', 'author').all()
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page,
        'paginator': paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'group': group,
        'page': page,
        'posts': posts,
        'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {'form': form}
        )
    form.instance.author = request.user
    form.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('post', username=post.author, post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'posts/new_post.html',
        {'form': form, 'post': post}
    )


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = user_profile.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    return render(
        request,
        'profile.html',
        {'page': page,
         'paginator': paginator,
         'profile': user_profile}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    return render(
        request,
        'posts/post.html',
        {'profile': post.author,
         'post': post}
    )
