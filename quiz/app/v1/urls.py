# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    #  竞猜分类
    path('category/', views.CategoryView.as_view(), name="app-v1-quiz-category"),
    # 世界杯列表
    path('world_cup/<int:roomquiz_id>/', views.WorldCup.as_view(), name="app-v1-quiz-worldcup"),
    #  热门比赛
    path('hotest/<int:roomquiz_id>/<int:category_parent>/', views.HotestView.as_view(), name="app-v1-quiz-hotest"),
    # 竞猜列表
    path('list/<int:roomquiz_id>/<int:category_parent>/', views.QuizListView.as_view(), name="app-v1-quiz-list"),
    # 我的竞猜记录
    path('records/<int:roomquiz_id>/', views.RecordsListView.as_view(), name="app-v1-quiz-records"),
    # 他人的竞猜记录
    path('records/', views.RecordsListView.as_view(), name="app-v1-quiz-records"),
    # 竞猜详情
    path('<int:quiz_id>/', views.QuizDetailView.as_view(), name="app-v1-quiz-detail"),
    # 竞猜详情页面推送
    path('quiz_push/<int:quiz_id>/', views.QuizPushView.as_view(), name="app-v1-quiz-push"),
    # 竞猜选项
    path('rule/<int:quiz_id>/', views.RuleView.as_view(), name="app-v1-quiz-rule"),
    # 竞猜下注
    path('bet/', views.BetView.as_view(), name="app-v1-quiz-bet"),
    # 竞猜推荐
    path('recommend/<int:roomquiz_id>/', views.RecommendView.as_view(), name="app-v1-quiz-recommend"),
    # 俱乐部收益
    path('club/profit/', views.ProfitView.as_view(), name="app-v1-club-profit"),
    # 兑换主页面
    path('change/', views.Change.as_view(), name="app-v1-change"),
    # 兑换页面时间轴
    path('change/date/', views.ChangeDate.as_view(), name="app-v1-change-date"),
    # 点击兑换
    path('change/gsg/', views.ChangeGsg.as_view(), name="app-v1-change-gsg"),
    # 点击兑换页面
    path('change/table/', views.ChangeTable.as_view(), name="app-v1-change-table"),
    # gsg价格曲线图
    path('gsg/price/', views.GsgPrice.as_view(), name="app-v1-gsg-price"),
    # GSG交易所列表
    path('platform/name/', views.PlatformList.as_view(), name="app-v1-platform-list"),
    # 兑换检测
    path('change/remainder/', views.ChangeRemainder.as_view(), name="app-v1-change-remainder"),

]
