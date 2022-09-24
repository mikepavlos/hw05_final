from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .utils import get_paginator


def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = get_paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.select_related('author', 'group')
    page_obj = get_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    posts = author.posts.select_related('author', 'group')
    page_obj = get_paginator(request, posts)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', form.author)

    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if form.is_valid():
        form.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id)

    is_edit = True
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = get_paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if author == request.user:
        return redirect('posts:profile', username=username)

    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    if author == request.user:
        return redirect('posts:profile', username=username)

    following = get_object_or_404(Follow, user=request.user, author=author)
    following.delete()
    return redirect('posts:profile', username=username)
