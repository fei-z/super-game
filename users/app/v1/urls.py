# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    # 用户信息        已测试
    path('info/', views.InfoView.as_view(), name="app-v1-user-info"),
    # 首页推送
    path('quiz_push/', views.QuizPushView.as_view(), name="app-v1-user-quiz_push"),
    # 注册,登录接口        已测试
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
    #  修改用户昵称
    path('nickname/', views.NicknameView.as_view(), name="app-v1-user-nickname"),
    # 手机号绑定
    path('telephone/bind/', views.BindTelephoneView.as_view(), name="app-v1-user-telephone-bind"),
    # 解除手机绑定
    path('telephone/unbind/', views.UnbindTelephoneView.as_view(), name="app-v1-user-telephone-unbind"),
    # 排行榜       已经测试
    path('ranking/', views.RankingView.as_view(), name="app-v1-user-ranking"),
    # 用户退出登录           未测试
    path('logout/', views.LogoutView.as_view(), name="app-v1-user-logout"),
    # 密保设置           已测试
    path('passcode/', views.PasscodeView.as_view(), name="app-v1-user-passcode"),
    # 原密保校验       已测试
    path('passcode/check/', views.ForgetPasscodeView.as_view(), name="app-v1-user-passcode-check"),
    # 忘记密保             已测试
    path('passcode/back/', views.BackPasscodeView.as_view(), name="app-v1-user-back-passcode"),
    # 音效/消息免推送 开关     已测试
    path('switch/', views.SwitchView.as_view(), name="app-v1-user-switch"),
    #  签到列表
    path('daily/list/', views.DailyListView.as_view(), name="app-v1-user-daily"),
    # 点击签到
    path('daily/sign/', views.DailySignListView.as_view(), name="app-v1-user-daily-sign"),
    #  通知列表
    path('message/list/<int:type>/', views.MessageListView.as_view(), name="app-v1-user-message"),
    # 获取消息详细内容
    path('detail/<int:message_id>/', views.DetailView.as_view(), name="app-v1-user-detail"),
    # 一键阅读所有消息公告
    path('message/all-read/', views.AllreadView.as_view(), name="app-v1-user-all-read"),
    # 列出资产情况
    path('asset/', views.AssetView.as_view(), name="app-v1-user-asset"),
    # 资产锁定
    path('asset/lock/', views.AssetLockView.as_view(), name="app-v1-user-asset-lock"),
    # 提交提现申请
    path('asset/presentation/', views.UserPresentationView.as_view(), name="app-v1-user-asset-presentation"),
    # ETH提现记录表
    path('asset/list_pre/', views.PresentationListView.as_view(), name='app-v1-user-asset-list_pre'),
    # ETH提现审核
    path('asset/review/', views.ReviewListView.as_view(), name='app-v1-user-asset-review'),
    # GGTC锁定记录
    path('asset/lock_list/', views.LockListView.as_view(), name='app-v1-user-asset-lock_list'),
    # GGTC分红表
    path('asset/dividend/', views.DividendView.as_view(), name='app-v1-user-asset-dividend'),
    # 用户设置其他(index支持1-5)
    path('setting_others/<int:index>/', views.SettingOthersView.as_view(), name='app-v1-user-setting_others')
]
