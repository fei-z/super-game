# -*- coding: UTF-8 -*-
from rest_framework import serializers
from django.utils import timezone
import time
from ..models import CoinLock, Coin, UserCoinLock, UserCoin, User, CoinDetail, RewardCoin, CoinValue
from quiz.models import Record
from datetime import datetime


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户表
    """
    source = serializers.SerializerMethodField()  # 来源
    # status = serializers.SerializerMethodField()     # 状态
    telephone = serializers.SerializerMethodField()  # 电话
    pass_code = serializers.SerializerMethodField()  # 密保
    degree = serializers.SerializerMethodField()  # 参与竞猜数
    created_at = serializers.SerializerMethodField()  # 创建时间
    assets = serializers.SerializerMethodField()  # 创建时间

    class Meta:
        model = User
        fields = (
            "id", "username", "avatar", "nickname", "source", "telephone", "created_at", "status", "pass_code",
            "degree",
            "assets", "url")

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_source(obj):
        register_type = obj.REGISTER_TYPE[int(obj.register_type) - 1][1]
        source = obj.SOURCE_CHOICE[int(obj.source) - 1][1]
        data = str(register_type) + "-" + str(source)
        return data

    # @staticmethod
    # def get_status(obj):
    #     if int(obj.status) == 1:
    #         data = "启用"
    #     elif int(obj.status) == 0:
    #         data = "禁用"
    #     return data

    @staticmethod
    def get_pass_code(obj):
        if obj.pass_code == '' or obj.pass_code is None:
            return "未设置密保"
        else:
            return obj.telephone

    @staticmethod
    def get_telephone(obj):  # 电话号码
        if obj.telephone == '' or obj.telephone is None:
            return "未绑定电话"
        else:
            return obj.telephone

    @staticmethod
    def get_degree(obj):  # 参与竞猜数
        data = Record.objects.filter(user_id=obj.id).count()
        return data

    @staticmethod
    def get_assets(obj):  # 参与竞猜数
        list = UserCoin.objects.filter(user_id=obj.id)
        data = []
        for i in list:
            coin = Coin.objects.get(pk=i.coin_id)
            data.append({
                "coin": coin.name,
                "balance": i.balance
            })
        return data


class CoinLockSerializer(serializers.HyperlinkedModelSerializer):
    """
    货币锁定周期表序列化
    """
    coin_range = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    admin = serializers.SlugRelatedField(read_only=True, slug_field="username")
    Coin = serializers.SlugRelatedField(read_only=True, slug_field="name")

    class Meta:
        model = CoinLock
        fields = ("id", "period", "profit", "coin_range", "Coin", "admin", "created_at", "url")

    @staticmethod
    def get_coin_range(obj):
        coin_range = str(obj.limit_start) + "-" + str(obj.limit_end)
        return coin_range

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data


class CurrencySerializer(serializers.HyperlinkedModelSerializer):
    """
    货币种类表序列化
    """
    created_at = serializers.SerializerMethodField()
    # is_lock = serializers.SerializerMethodField()
    admin = serializers.SlugRelatedField(read_only=True, slug_field="username")

    class Meta:
        model = Coin
        fields = ("id", "icon", "name", "exchange_rate", "admin", "created_at", "cash_control", "url")

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    # @staticmethod
    # def get_is_lock(obj):  # 时间
    #     if obj.is_lock == False:
    #         data = "允许"
    #     if obj.is_lock == True:
    #         data = "不允许"
    #     return data


class UserCoinLockSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户锁定记录表
    """
    end_time = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    dividend = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field="nickname")
    coin_lock = serializers.SlugRelatedField(read_only=True, slug_field="period")

    class Meta:
        model = UserCoinLock
        fields = ("id", "user", "coin_lock", "amount", "end_time", "created_at", "dividend", "is_free")

    @staticmethod
    def get_end_time(obj):  # 结束时间
        data = obj.end_time.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_created_at(obj):  # 时间
        data = obj.created_at.strftime('%Y年%m月%d日%H:%M')
        return data

    @staticmethod
    def get_dividend(obj):  # 时间
        coinlock = CoinLock.objects.get(pk=obj.coin_lock_id)
        dividend = int(obj.amount) * float(coinlock.profit)
        return dividend

    @staticmethod
    def get_is_free(obj):
        is_free = obj.is_free
        data = "绑定中"
        if is_free == 1:
            data = "已解锁"
        return data


class UserCoinSerializer(serializers.HyperlinkedModelSerializer):
    """
    用户资产
    """

    icon = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    coin = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field="nickname")

    class Meta:
        model = UserCoin
        fields = ("id", "coin", "user", "username", "icon", "address")

    @staticmethod
    def get_icon(obj):
        list = Coin.objects.get(pk=obj.coin_id)
        data = list.icon
        return data

    @staticmethod
    def get_coin(obj):
        coin = Coin.objects.get(pk=obj.coin_id)
        data = str(obj.balance) + " " + str(coin.name)
        return data

    @staticmethod
    def get_username(obj):
        list = User.objects.get(pk=obj.user_id)
        data = list.username
        return data


class CoinDetailSerializer(serializers.ModelSerializer):
    """
    用户资金明细
    """
    coin_name = serializers.CharField(source="coin.name")
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = CoinDetail
        fields = ("coin", "coin_name", "amount", "rest", "sources", "created_at")

    @staticmethod
    def get_created_at(obj):
        # local_time = timezone.localtime(obj.created_at)
        local_time = obj.created_at
        created_time = datetime.strftime(local_time, "%Y-%m-%d %H:%M:%S")
        return created_time


class CoinValueRewardSerializer(serializers.ModelSerializer):
    """
    币允许投注值及兑换积分比例
    """
    reward = serializers.SerializerMethodField()

    class Meta:
        model = CoinValue
        fields = ("id", "coin", "value_index", "value", "reward")

    @staticmethod
    def get_reward(obj):
        reward = RewardCoin.objects.get(coin__name=obj.coin.name)
        return reward.value_ratio
