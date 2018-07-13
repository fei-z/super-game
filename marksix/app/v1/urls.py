# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 下拉玩法分类
    path('play/',views.SortViews.as_view(),name='marksix-app-sort'),
    # 往期开奖历史
    path('openprice/',views.OpenViews.as_view(),name='marksix-app-open'),
    # 玩法赔率接口
    path('play/<str:id>/',views.OddsViews.as_view(),name='marksix-app-play')
]