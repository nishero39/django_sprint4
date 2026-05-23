from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, CustomUserChangeForm
from .utils import get_published_posts, paginate_queryset, add_comment_count


def index(request):
    """Главная страница - 10 публикаций с пагинацией"""
    template_name = 'blog/index.html'
    post_list = get_published_posts().select_related(
        'author',
        'location',
        'category'
    )
    post_list = add_comment_count(post_list).order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


def post_detail(request, post_id):
    """Страница отдельного поста с комментариями."""
    template_name = 'blog/detail.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        post = get_object_or_404(
            get_published_posts(),
            id=post_id
        )

    comments = post.comments.select_related('author').all()
    comment_form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, template_name, context)


def category_posts(request, category_slug):
    """Страница с постами определенной категории с пагинацией."""
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )
    post_list = get_published_posts().filter(
        category=category
    ).select_related(
        'author',
        'location'
    )
    post_list = add_comment_count(post_list).order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


def profile(request, username):
    """Страница пользователя со всеми его публикациями с пагинацией."""
    user = get_object_or_404(User, username=username)
    if request.user == user:
        post_list = Post.objects.filter(author=user).select_related(
            'category', 'location'
        )
    else:
        post_list = get_published_posts().filter(author=user).select_related(
            'category', 'location'
        )

    post_list = add_comment_count(post_list).order_by('-pub_date')
    page_obj = paginate_queryset(request, post_list)

    context = {
        'profile': user,
        'page_obj': page_obj,
        'is_owner': request.user == user
    }
    return render(request, 'blog/profile.html', context)


@login_required
def create_post(request):
    """Создание новой публикации."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    """Удаление публикации."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(
        request, 'blog/detail.html', {'post': post, 'confirm_delete': True}
    )


@login_required
def add_comment(request, post_id):
    """Добавление комментария к публикации."""
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(
        request, 'blog/comment.html', {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})


@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'blog/user.html', {'form': form})
