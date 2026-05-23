from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from .models import Post


def get_published_posts():
    """Возвращает фильтрованные опубликованные посты."""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).exclude(category__is_published=False)


def paginate_queryset(request, queryset, per_page=10):
    """Возвращает объект Page для пагинации."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def add_comment_count(queryset):
    """Добавляет аннотацию comment_count к каждому объекту."""
    return queryset.annotate(comment_count=models.Count('comments'))
