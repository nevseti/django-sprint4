"""View-функции приложения blog."""
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def get_posts(posts=Post.objects, published_only=True):
    """Добавляет к публикациям связанные объекты и число комментариев.

    Если published_only=True, оставляет только публикации, которые
    можно показывать всем посетителям.
    """
    posts = posts.select_related(
        'author', 'category', 'location'
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    if published_only:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    return posts


def get_page(request, posts):
    """Возвращает нужную страницу пагинатора."""
    return Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def index(request):
    """Показывает ленту публикаций."""
    return render(
        request,
        'blog/index.html',
        {'page_obj': get_page(request, get_posts())},
    )


def category_posts(request, category_slug):
    """Показывает опубликованные посты выбранной категории."""
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': get_page(request, get_posts(category.posts)),
    })


def profile(request, username):
    """Показывает страницу пользователя и его публикации.

    Автор видит все свои публикации, включая отложенные и снятые
    с публикации; остальные посетители — только опубликованные.
    """
    author = get_object_or_404(User, username=username)
    posts = get_posts(author.posts, published_only=request.user != author)
    return render(request, 'blog/profile.html', {
        'profile': author,
        'page_obj': get_page(request, posts),
    })


@login_required
def edit_profile(request):
    """Редактирует профиль текущего пользователя."""
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)
    return render(request, 'blog/user.html', {'form': form})


def post_detail(request, post_id):
    """Показывает публикацию с комментариями.

    Автор видит свою публикацию всегда, остальные — только опубликованную.
    """
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        post = get_object_or_404(get_posts(), pk=post_id)
    return render(request, 'blog/detail.html', {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.select_related('author'),
    })


@login_required
def create_post(request):
    """Создаёт публикацию от имени текущего пользователя."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирует публикацию. Доступно только автору."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Удаляет публикацию после подтверждения. Доступно только автору."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', request.user.username)
    return render(
        request, 'blog/create.html', {'form': PostForm(instance=post)}
    )


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий к публикации."""
    post = get_object_or_404(get_posts(), pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирует комментарий. Доступно только автору комментария."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    return render(
        request, 'blog/comment.html', {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаляет комментарий после подтверждения. Доступно только автору."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
