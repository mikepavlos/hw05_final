from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(request, posts):
    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
