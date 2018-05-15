# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from quiz.models import Category


class Command(BaseCommand):
    """
    批量修改http为https
    """
    help = "批量修改http为https"

    def handle(self, *args, **options):
        category = Category.objects.all()
        for cate in category:
            icon = cate.icon.replace('http:', 'https:')
            cate.icon = icon
            cate.save()
