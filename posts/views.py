from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User


def index(request):
    latest = Post.objects.all()
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
    return render(request, 'posts/group.html', {
        'group': group,
        'page': page,
        'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {'form': form, 'edit': False}
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect("post", username=post.author, post_id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST or None, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post', username=post.author, post_id=post_id)
    else:
        form = PostForm(instance=post)
        return render(
            request,
            'posts/new_post.html',
            {"form": form,
             'edit': True,
             'post': post}
        )
    return render(
        request,
        'posts/new_post.html',
        {"form": form, 'edit': True, 'post': post}
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    return render(
        request,
        'profile.html',
        {'page': page,
         'paginator': paginator,
         'author': author}
    )


def post_view(request, username, post_id):
    user_profile = get_object_or_404(User, username=username)
    post = Post.objects.get(author=user_profile.pk, id=post_id)
    posts = Post.objects.filter(
        author=user_profile).order_by('-pub_date').all()
    posts_count = posts.count()
    return render(
        request,
        "posts/post.html",
        {'profile': user_profile,
         'post': post,
         'post_count': posts_count}
    )
