# -*- coding: UTF-8 -*-
from itertools import chain
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView, DestroyAPIView, UpdateAPIView, \
    ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models.functions import ExtractDay
from django.db.models import Q, Count, Sum, Max, F, Func, When, Case, DecimalField
from chat.models import Club
from users.models import Coin, CoinLock, Admin, UserCoinLock, UserCoin, User, CoinDetail, CoinValue, RewardCoin, \
    LoginRecord, UserInvitation, UserPresentation, CoinOutServiceCharge, UserRecharge, CoinGiveRecords, CoinGive
from users.app.v1.serializers import PresentationSerialize
from rest_framework import status
import jsonfield
from utils.functions import normalize_fraction
from base import code as error_code
from base.exceptions import ParamErrorException
from django.http import HttpResponse
from . import serializers
import json
import rest_framework_filters as filters
from utils.filter import JsonFilter
from base import backend
from django.http import JsonResponse
from utils.functions import reversion_Decorator
from url_filter.integrations.drf import DjangoFilterBackend
from quiz.models import Record


class CoinLockListView(CreateAPIView, FormatListAPIView):
    """
    添加一条货币锁定周期方案
    """
    """
    get:
    锁定周期列表

    post:
    锁定周期表：添加一条方案
    """
    serializer_class = serializers.CoinLockSerializer

    def get_queryset(self):
        return CoinLock.objects.filter(is_delete=0)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        coins = Coin.objects.get(pk=1)
        admin = self.request.user
        period = request.data['period']
        if int(period) not in [7, 31, 365]:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        coinlock = CoinLock()
        coinlock.period = period
        coinlock.profit = int(request.data['profit']) / 100
        coinlock.limit_start = request.data['start_date']
        coinlock.limit_end = request.data['end_date']
        coinlock.Coin = coins
        coinlock.admin = admin
        coinlock.save()

        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CoinLockDetailView():
    serializer_class = serializers.CoinLockSerializer

    def get(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coinlock = CoinLock.objects.get(pk=id, is_delete=0)
        data = {
            "period": str(coinlock.period),
            "profit": str(coinlock.profit * 100),
            "start_date": coinlock.limit_start,
            "end_date": coinlock.limit_end,
            "url": ''
        }
        return JsonResponse({'data': data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coinlock = CoinLock.objects.get(pk=id, is_delete=0)
        coinlock.period = int(request.data['period'])
        coinlock.profit = int(request.data['profit']) / 100
        coinlock.limit_start = int(request.data['start_date'])
        coinlock.limit_end = int(request.data['end_date'])
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class CurrencyListView(ListCreateAPIView):
    """
    get:
    币总列表

    post:
    锁定周期表：添加一条方案
    """
    serializer_class = serializers.CurrencySerializer

    def get_queryset(self):
        return Coin.objects.all()

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        max_order = Coin.objects.all().aggregate(Max('coin_order'))['coin_order__max']
        admin = self.request.user
        exchange_rate = request.data['exchange_rate']
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        betting_value_one = request.data['betting_value_one']
        betting_value_two = request.data['betting_value_two']
        betting_value_three = request.data['betting_value_three']
        coin_accuracy = request.data['coin_accuracy']
        is_eth_erc20 = request.data['is_eth_erc20']
        value = request.data['value']
        Integral_proportion = request.data['Integral_proportion']

        coin = Coin()
        coin.icon = request.data['icon']
        coin.coin_order = int(max_order) + 1
        if int(exchange_rate) != 1:
            coin.exchange_rate = 1
        else:
            coin.exchange_rate = exchange_rate
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
        coin.is_eth_erc20 = is_eth_erc20
        coin.coin_accuracy = coin_accuracy
        coin.name = request.data['name']
        # coin.type = request.data['type']
        # coin.is_lock = request.data['is_lock']
        coin.admin = admin
        coin.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 1
        coin_value.value = Decimal(betting_value_one)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 2
        coin_value.value = Decimal(betting_value_two)
        coin_value.save()
        coin_value = CoinValue()
        coin_value.coin = coin
        coin_value.value_index = 3
        coin_value.value = Decimal(betting_value_three)
        coin_value.save()

        coin_service = CoinOutServiceCharge()
        # try:
        #     coin_t = Coin.objects.get(coin__name=coin.name)
        # except:
        #     return JsonResponse({'Error':'币不存在,请先添加币%s' % coin.name}, status=status.HTTP_400_BAD_REQUEST)
        coin_service.coin_out = coin
        coin_service.coin_payment = coin
        coin_service.value = value
        coin_service.save()
        reward_coin = RewardCoin()
        reward_coin.coin = coin
        reward_coin.value_ratio = Integral_proportion
        reward_coin.admin = admin
        reward_coin.save()

        return JsonResponse({}, status=status.HTTP_201_CREATED)


class CurrencyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.CurrencySerializer

    def get(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coin = Coin.objects.get(pk=id)
        coinvalue_list = CoinValue.objects.filter(coin_id=coin.id).order_by("value_index")
        value_ratio = RewardCoin.objects.filter(coin_id=coin.id)
        if len(value_ratio) == 0:
            Integral_proportion = ""
        else:
            Integral_proportion = value_ratio[0].value_ratio
        if len(coinvalue_list) != 3:
            betting_value_one = ""
            betting_value_two = ""
            betting_value_three = ""
        else:
            betting_value_one = coinvalue_list[0].value
            betting_value_two = coinvalue_list[1].value
            betting_value_three = coinvalue_list[2].value

        values = CoinOutServiceCharge.objects.filter(coin_out_id=coin.id)
        if len(values) == 0:
            value = ''
        else:
            value = values[0].value
        # is_lock = coin.is_lock
        # if is_lock == False:
        #     is_lock = 0
        # if is_lock == True:
        #     is_lock = 1
        data = {
            "icon": coin.icon,
            "name": coin.name,
            # "type": coin.type,
            "exchange_rate": coin.exchange_rate,
            "cash_control": str(coin.cash_control),
            "betting_toplimit": str(coin.betting_toplimit),
            "betting_control": str(coin.betting_control),
            "betting_value_one": str(betting_value_one),
            "betting_value_two": str(betting_value_two),
            "betting_value_three": str(betting_value_three),
            "Integral_proportion": Integral_proportion,
            "coin_order": coin.coin_order,
            "coin_accuracy": coin.coin_accuracy,
            "value": value,
            "is_eth_erc20": coin.is_eth_erc20,
            # "is_lock": str(is_lock),
            "url": ''
        }
        return JsonResponse({'data': data}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coin_id = self.request.parser_context['kwargs']['pk']
        coin = Coin.objects.get(pk=coin_id)
        coin.is_delete = True
        coin.save()
        content = {'status': status.HTTP_200_OK}
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        cash_control = request.data['cash_control']
        betting_toplimit = request.data['betting_toplimit']
        betting_control = request.data['betting_control']
        coin_accuracy = request.data['coin_accuracy']
        is_eth_erc20 = request.data['is_eth_erc20']
        coin = Coin.objects.get(pk=id)
        coin.icon = request.data['icon']
        coin.name = request.data['name']
        # coin.type = request.data['type']
        coin.exchange_rate = request.data['exchange_rate']
        coin.cash_control = cash_control
        coin.betting_toplimit = betting_toplimit
        coin.betting_control = betting_control
        coin.coin_accuracy = coin_accuracy
        coin.is_eth_erc20 = is_eth_erc20
        # coin.is_lock = request.data['is_lock']
        coin.coin_order = int(request.data['coin_order'])
        coin.save()
        coin_value_one = CoinValue.objects.get(coin_id=coin.pk, value_index=1)
        coin_value_one.value = request.data['betting_value_one']
        coin_value_one.save()
        coin_value_two = CoinValue.objects.get(coin_id=coin.pk, value_index=2)
        coin_value_two.value = request.data['betting_value_two']
        coin_value_two.save()
        coin_value_three = CoinValue.objects.get(coin_id=coin.pk, value_index=3)
        coin_value_three.value = request.data['betting_value_three']
        coin_value_three.save()
        reward_coin = RewardCoin.objects.get(coin_id=coin.pk)
        reward_coin.value_ratio = request.data['Integral_proportion']
        reward_coin.save()

        coin_service = CoinOutServiceCharge.objects.get(coin_out_id=coin.pk)
        coin_service.value = request.data['value']
        coin_service.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


class UserLockListView(CreateAPIView, FormatListAPIView):
    """
    锁定列表
    """
    serializer_class = serializers.UserCoinLockSerializer

    def get_queryset(self):
        return UserCoinLock.objects.all()


class UserCoinListView(CreateAPIView, FormatListAPIView):
    """
    用户资产管理
    """
    serializer_class = serializers.UserCoinSerializer

    def get_queryset(self):
        return UserCoin.objects.all()


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['contains'],
        }
        filter_overrides = {
            jsonfield.JSONField: {
                'filter_class': JsonFilter,
            }
        }


class UserListView(backend.ListCreateAPIView):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    filter_class = UserFilter


class UserListDetailView(DestroyAPIView, FormatRetrieveAPIView, UpdateAPIView):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        user = User.objects.get(pk=id)
        admin = self.request.user
        data = request.data
        user.status = data
        user.save()
        content = {'status': status.HTTP_201_CREATED}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def delete(self, request, *args, **kwargs):
        coinlovk_id = self.request.parser_context['kwargs']['pk']
        coinlock = CoinLock.objects.get(pk=coinlovk_id)
        coinlock.is_delete = True
        coinlock.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')

    @reversion_Decorator
    def update(self, request, *args, **kwargs):
        id = int(kwargs['pk'])
        coins = UserCoin.objects.filter(user_id=id)
        for i in coins:
            coin_name = i.coin.name
            coinname = 'balance-' + coin_name
            coinname = request.data[coinname]
            i.balance = coinname
            i.save()
        users = User.objects.get(pk=id)
        users.nickname = request.data['nickname']
        users.status = request.data['status']
        users.save()
        content = {'status': status.HTTP_200_OK}
        return HttpResponse(json.dumps(content), content_type='text/json')


class LoginView(CreateAPIView):
    """
    后台管理员登录
    """


class CoinDetailView(ListAPIView, DestroyAPIView):
    """
    用户资金明细
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        if "uuid" not in self.request.query_params:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        uuid = self.request.query_params.get("uuid")
        query_s = CoinDetail.objects.filter(user_id=uuid, is_delete=0)
        return query_s

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        count_item = results.data.get('count')
        items = results.data.get('results')
        list_t = Coin.objects.filter(admin=1).values('id', 'name').distinct()
        coin_list = {}
        for x in list_t:
            coin_list[x['name']] = x['id']
        return JsonResponse({"results": items, "choice": coin_list, "count": count_item}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def post(self, request, *args, **kwargs):
        coin = int(request.data['coin'])
        options = dict(request.data['options'])
        ratio = request.data['value_ratio']
        for x in options.keys():
            if CoinValue.objects.filter(coin_id=coin, value_index=x).exists():
                return JsonResponse({"ERROR": "CoinValue Index %d Object Exist,You Can Modify It" % x},
                                    status=status.HTTP_400_BAD_REQUEST)
            coin_value = CoinValue()
            coin_value.coin_id = coin
            coin_value.value_index = int(x)
            coin_value.value = options[x]
            coin_value.save()
        if RewardCoin.objects.filter(coin_id=coin).exists():
            return JsonResponse({"ERROR": "RewardCoin Object Exist,You Can Modify It!"},
                                status=status.HTTP_400_BAD_REQUEST)
        reward_coin = RewardCoin()
        reward_coin.coin_id = coin
        reward_coin.admin_id = 1
        reward_coin.value_ratio = int(ratio)
        reward_coin.save()
        return JsonResponse({}, status=status.HTTP_200_OK)

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        coin = int(request.data['coin'])
        if not RewardCoin.objects.filter(coin_id=coin).exists() and not CoinValue.objects.filter(coin_id=coin).exists():
            return JsonResponse({"ERROR": "Coin Items Don't Exist,You Need Create It First"},
                                status=status.HTTP_400_BAD_REQUEST)
        for x in request.data.items():
            if x[0] == 'options':
                values = dict(x[1])
                for vv in values.keys():
                    try:
                        coin_value = CoinValue.objects.get(coin_id=coin, value_index=int(vv))
                    except Exception:
                        return JsonResponse({"Error": 'CoinValue对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
                    coin_value.value = values[vv]
                    coin_value.save()
            if x[0] == 'value_ratio':
                try:
                    reward = RewardCoin.objects.get(coin_id=coin)
                except Exception:
                    return JsonResponse({"Error": 'RewardCoin对象不存在'}, status=status.HTTP_400_BAD_REQUEST)
                reward.value_ratio = int(x[1])
                reward.save()
        return JsonResponse({}, status=status.HTTP_200_OK)


# class InviterInfo(RetrieveAPIView):
#     """
#     推荐人信息
#     """
#
#     def retrieve(self, request, *args, **kwargs):
#         username = request.query_params.get('username')
#         try:
#             record = LoginRecord.objects.filter(user__username=username).order_by('-login_time')[0]
#         except Exception:
#             return JsonResponse({'Error': '用户不存在或参数username未提供'}, status=status.HTTP_400_BAD_REQUEST)
#         rc = serializers.InviterInfoSerializer(record)
#         return JsonResponse({'results': rc.data}, status=status.HTTP_200_OK)


class UserAllView(ListAPIView):
    """
    所有用户资产表
    """
    queryset = User.objects.filter(is_robot=0).order_by('-created_at')
    serializer_class = serializers.UserAllSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['username']


class InviterDetailView(RetrieveAPIView):
    """
    推荐人信息
    """

    def retrieve(self, request, *args, **kwargs):
        uuid = self.kwargs['pk']
        try:
            user = User.objects.get(pk=uuid)
        except Exception:
            return JsonResponse({'Error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        rc = serializers.UserAllSerializer(user)
        return JsonResponse({'results': [rc.data]}, status=status.HTTP_200_OK)


class InviteNewView(ListAPIView):
    """
    邀请好友数
    """
    serializer_class = serializers.UserAllSerializer

    def get_queryset(self):
        uuid = int(self.kwargs['pk'])
        inviter = UserInvitation.objects.filter(inviter_id=uuid)
        user_id1 = inviter.values_list('invitee_one')
        user_id2 = inviter.values_list('invitee_two')
        users = []
        if inviter.exists():
            for x in list(user_id1):
                if x[0] != 0:
                    users.append(int(x[0]))
            for x in list(user_id2):
                if x[0] != 0:
                    users.append(int(x[0]))
        user_group = User.objects.filter(pk__in=users)
        return user_group


class CoinPresentView(ListAPIView):
    """
    提现记录表
    """
    queryset = UserPresentation.objects.all().order_by('-created_at', 'status')
    serializer_class = PresentationSerialize
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'status', 'coin']


class CoinPresentCheckView(RetrieveUpdateAPIView):
    """
    提现审核
    """

    @reversion_Decorator
    def patch(self, request, *args, **kwargs):
        id = kwargs['pk']  # 提现记录id
        if 'status' not in request.data and 'text' not in request.data and 'is_bill' not in request.data:
            return JsonResponse({'Error': '请传递参数'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            item = UserPresentation.objects.get(pk=id)
        except Exception:
            return JsonResponse({'Error': 'Instance Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        if 'status' in request.data:
            sts = int(request.data.get('status'))
            item.status = sts
            if sts == 2:
                try:
                    user_coin = UserCoin.objects.get(user=item.user, coin=item.coin)
                    coin_out = CoinOutServiceCharge.objects.get(coin_out=user_coin.coin)
                except Exception:
                    raise
                if user_coin.coin.name == 'HAND':
                    try:
                        eth_coin = UserCoin.objects.get(user=item.user, coin__name='ETH')
                    except Exception:
                        raise
                    eth_coin.balance += coin_out.value
                    eth_coin.save()
                    user_coin.balance += item.amount
                else:
                    user_coin.balance = user_coin.balance + item.amount + coin_out.value
                user_coin.save()
        if 'text' in request.data:
            text = request.data.get('text')
            item.feedback = text

        if 'is_bill' in request.data:
            bill = request.data.get('is_bill')
            item.is_bill = bill
        item.save()

        return JsonResponse({}, status=status.HTTP_200_OK)


class RechargeView(ListAPIView):
    """
    用户充值记录
    """
    #
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        coin_name = self.kwargs['coin_name']
        details = CoinDetail.objects.filter(user_id=pk, sources=CoinDetail.RECHARGE, coin_name=coin_name)
        return details


class RechargeAllView(ListAPIView):
    """
    所有用户充值记录
    """
    queryset = UserRecharge.objects.filter(user__is_robot=0).order_by('-amount')
    serializer_class = serializers.UserRechargeSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'coin']


class GSGBackendView(ListAPIView):
    """
    用户GSG明细
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        details = CoinDetail.objects.filter(user_id=pk, coin_name='GSG')
        return details


class CoinBackendDetail(ListAPIView):
    """
    用户资产情况
    """
    serializer_class = serializers.CoinBackendDetailSerializer

    def get_queryset(self):
        uuid = int(self.kwargs['pk'])
        user_coin = UserCoin.objects.filter(user_id=uuid)
        return user_coin


class RewardBackendDetail(ListAPIView):
    """
    系统奖励及其他
    """
    serializer_class = serializers.CoinDetailSerializer

    def get_queryset(self):
        pk = int(self.kwargs['pk'])
        coin_name = self.kwargs['coin_name']
        details = CoinDetail.objects.filter(~Q(coin_name='GSG'), ~Q(
            sources__in=[CoinDetail.RECHARGE, CoinDetail.REALISATION, CoinDetail.BETS]), user_id=pk,
                                            coin_name=coin_name)
        return details


class CoinPresentDetailView(ListAPIView):
    """
    提现列表--用户管理内
    """
    serializer_class = PresentationSerialize

    def get_queryset(self):
        pk = self.kwargs['pk']
        coin = int(self.kwargs['coin'])
        presents = UserPresentation.objects.filter(user_id=pk, coin_id=coin)
        return presents


class RunningView(ListAPIView):
    """
    运营数据统计
    """

    def count_earn_coin(self, number):
        """
        计算赠送币的人数
        :return:
        """
        usdt = CoinGiveRecords.objects.all()
        if number == 50:
            count_user = usdt.filter(is_recharge_lock=True, is_recharge_give=True).count()
        else:
            count_user = usdt.filter(lock_coin__gte=number).count()
        return count_user

    def list(self, request, *args, **kwargs):

        user_register = User.objects.filter(is_robot=0)
        register_num = user_register.count()
        x = user_register.extra(select={
            'sum_invite': 'select count(*) from users_userinvitation as ui where ui.inviter_id=users_user.id'}).values(
            'sum_invite')
        invite_4 = 0
        invite_0 = 0
        for i in x:
            if i['sum_invite'] == 0:
                invite_0 += 1
            if i['sum_invite'] >= 4:
                invite_4 += 1
        gsg_0 = user_register.filter(integral=0).count()
        sum_integral = user_register.values('integral').aggregate(Sum('integral'))['integral__sum']
        sum_amount = CoinDetail.objects.filter(user__is_robot=0, coin_name='GSG', sources=4).values('amount').aggregate(
            Sum('amount'))['amount__sum']
        gsg_sent = Decimal(str(sum_integral)) - Decimal(str(sum_amount))  # 发放gsg数量
        recharge_sum = UserRecharge.objects.filter(user__is_robot=0).values('user_id').distinct().count()  # 充值总人数
        present_sum = UserPresentation.objects.filter(user__is_robot=0).values('user_id').distinct().count()  # 提现总人数
        hand_recharge = \
            UserRecharge.objects.filter(coin__name='HAND', user__is_robot=0).values('amount').aggregate(Sum('amount'))[
                'amount__sum']
        hand_system = CoinDetail.objects.filter(coin_name='HAND', user__is_robot=0, sources__in=[4, 6, 7, 8]).values(
            'amount').aggregate(Sum('amount'))['amount__sum']
        records = Record.objects.filter(source=Record.NORMAL, roomquiz_id=1)
        hand_bet = records.values('bet').aggregate(Sum('bet'))['bet__sum']
        hand_out = records.filter(quiz__status=5, option__option__is_right=1).annotate(
            hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum']
        hand_in = records.filter(quiz__status=5, option__option__is_right=0).annotate(
            hand_i=F('bet')).aggregate(Sum('hand_i'))['hand_i__sum']
        hand_bet_not_begin = records.filter(quiz__status=0).aggregate(Sum('bet'))['bet__sum']
        hand_rest = \
            UserCoin.objects.filter(user__is_robot=0, coin__name='HAND').values('balance').aggregate(Sum('balance'))[
                'balance__sum']
        hand_sent = hand_rest + hand_bet_not_begin + hand_in - hand_recharge
        usdt_record = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=6)
        usdt_recharge_count = UserRecharge.objects.filter(user__is_robot=0, coin__name='USDT').values(
            'user_id').distinct().count()
        usdt_recharge = \
            UserRecharge.objects.filter(coin__name='USDT', user__is_robot=0).values('amount').aggregate(Sum('amount'))[
                'amount__sum']
        usdt_bet = usdt_record.values('bet').aggregate(Sum('bet'))['bet__sum']
        usdt_out = usdt_record.filter(quiz__status=5, option__option__is_right=1).annotate(
            hand_o=F('bet') * (F('odds') - 1)).aggregate(Sum('hand_o'))['hand_o__sum']
        usdt_in = usdt_record.filter(quiz__status=5, option__option__is_right=0).annotate(
            hand_i=F('bet')).aggregate(Sum('hand_i'))['hand_i__sum']
        usdt_system = \
            CoinGiveRecords.objects.all().values('coin_give__number').aggregate(total_coin=Sum('coin_give__number'))[
                'total_coin']
        usdt_rest = \
            UserCoin.objects.filter(user__is_robot=0, coin__name='USDT').values('balance').aggregate(Sum('balance'))[
                'balance__sum']
        usdt_bet_not_begin = usdt_record.filter(quiz__status=0).aggregate(Sum('bet'))['bet__sum']
        usdt_balance_max = \
            UserCoin.objects.filter(user__is_robot=0, coin__name='USDT').values('balance').aggregate(Max('balance'))[
                'balance__max']
        usdt_lock_coin_max = \
            CoinGiveRecords.objects.filter(user__is_robot=0).values('lock_coin').aggregate(Max('lock_coin'))[
                'lock_coin__max']

        # for x in records:
        #     option = Option.objects.filter(is_right=1, rule_id=x.rule_id)
        #     if len(option) > 0:
        #         if option[0].id == x.option.option_id:
        #             hand_out += x.bet * (x.odds - 1)
        #         else:
        #             hand_in += x.bet
        data = {'register_num': register_num,  # 总注册用户数
                'invite_4': invite_4,  # 邀请4个以上的用户数
                'invite_0': invite_0,  # 邀请0个用户数
                'gsg_0': gsg_0,  # gsg余额为0用户数
                'gsg_sent': gsg_sent,  # gsg发放的金额数
                'recharge_sum': recharge_sum,  # 充值人数
                'present_sum': present_sum,  # 提现人数
                'hand_recharge': hand_recharge,  # hand币充值金额
                'hand_system': hand_system,  # hand币系统发放
                'hand_bet': hand_bet,  # hand币投注金额
                'hand_out': hand_out,  # hand币投注发出金额
                'hand_in': hand_in,  # hand币投注回收金额
                'hand_rest': hand_rest,  ##hand币所有用户余额
                'hand_bet_not_begin': hand_bet_not_begin,  # hand币投注未开奖金额
                'hand_sent': hand_sent,  # hand币发放金额
                'usdt_recharge_count': usdt_recharge_count,  # usdt充值人数
                'usdt_recharge': 0 if usdt_recharge == None else usdt_recharge,  # usdt充值额度
                'usdt_bet': usdt_bet,  # usdt下注值
                'usdt_out': usdt_out,  # usdt下注平台发放
                'usdt_in': usdt_in,  # usdt下注平台回收
                'usdt_system': usdt_system,  # usdt平台系统赠送
                'usdt_rest': usdt_rest,  # usdt用户余额
                'usdt_bet_not_begin': usdt_bet_not_begin,  # usdt用户投注未结算
                'usdt_balance_max': usdt_balance_max,  # usdt用户余额最大值
                'usdt_lock_coin_max': usdt_lock_coin_max,  # usdt用户锁定金额最大值
                'usdt_earn_gte_20': self.count_earn_coin(20),
                'usdt_earn_gte_30': self.count_earn_coin(30),
                'usdt_earn_gte_40': self.count_earn_coin(40),
                'usdt_earn_gte_50': self.count_earn_coin(50),
                'now_time': datetime.now().strftime('%Y年%m月%d日')
                }
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class LoginRateView(ListAPIView):
    """
    用户留存率
    """

    def list(self, request, *args, **kwargs):
        user_register = User.objects.filter(is_robot=0)
        register_num = user_register.count()
        logins = LoginRecord.objects.filter(user__is_robot=0).extra(select={'date': 'date(login_time)'}).values(
            'user_id', 'date', 'user__source').distinct().values('date', 'user__source').annotate(
            Count('user__source')).order_by('date')
        temp_dict = {}
        for x in logins:
            date = x['date'].strftime('%m/%d')
            source_index = x['user__source']
            for i in User.SOURCE_CHOICE:
                if int(source_index) == i[0]:
                    source = i[1]
            if source != '':
                if date not in temp_dict:
                    temp_dict[date] = {
                        source: 0 if register_num == 0 else round(100 * x['user__source__count'] / register_num, 2)
                    }
                else:
                    temp_dict[date][source] = 0 if register_num == 0 else round(
                        100 * x['user__source__count'] / register_num, 2)
        data = []
        for k in temp_dict:
            vv = {'Date': k}
            for j in temp_dict[k]:
                vv[j] = temp_dict[k][j]
            data.append(vv)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


class UserSts(ListAPIView):
    """
    用户数据统计
    """

    def list(self, request, *args, **kwargs):
        new_register = User.objects.filter(is_robot=0).extra(select={'date': 'date(created_at)'}).values(
            'date').annotate(
            register_count=Count('id')).order_by('date')
        activy_user = LoginRecord.objects.annotate(date=Func(F('login_time'), function='date')).filter(
            ~Q(user__created_at__date__contains=F('date')), user__is_robot=0).values('date').annotate(
            activy_count=Count('user_id', distinct=True)).order_by('date')
        records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE]).extra(
            select={'date': 'date(created_at)'}).values('date')
        bet_user = records.annotate(user_count=Count('user_id', distinct=True)).order_by('date')
        total = 0
        data = []
        activy_list = [it for it in activy_user]
        activy_list = [{'date': datetime.strptime('2018-5-28', '%Y-%m-%d').date(), 'activy_count': 0}] + activy_list
        print('aaaaaaaaaaaaaaa', activy_list)
        # activy.insert({'date': datetime.strptime('2018-5-28', '%Y-%m-%d').date(), 'activy_count':0})
        # print('aaaaaaaaaaaaa',activy)
        if len(new_register) == len(activy_list) == len(bet_user):
            for x, y, z in zip(new_register, activy_list, bet_user):
                if x['date'] == y['date'] == z['date']:
                    date = x['date'].strftime('%m/%d')
                    total += x['register_count']
                    unbet = total - z['user_count']
                    temp_dict = {
                        'date': date,
                        'new_register': x['register_count'],
                        'activy_user': y['activy_count'],
                        'bet_user': z['user_count'],
                        'unbet_user': unbet
                    }
                    data.append(temp_dict)
                else:
                    return JsonResponse({'Error': '日期需按同一顺序列表'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(new_register, '----------\n', activy_user, '-----------\n', bet_user)
            return JsonResponse({'Error': '缺少天数'}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({'results': data}, status=status.HTTP_200_OK)

        # data = []
        # for x in obj_s:
        #     date = x['date'].strftime('%m/%d')
        #     temp_dict = {
        #         'date': date,
        #         'total_count': x['total_count']
        #     }
        #     data.append(temp_dict)

        return JsonResponse({'results': ''}, status=status.HTTP_200_OK)


class CoinSts(ListAPIView):
    """
    币统计
    """

    # def compute(self, a, b):
    #     return a * (b - 1)

    def list(self, request, *args, **kwargs):
        club_room = kwargs['club_room']
        try:
            club = Club.objects.get(id=club_room)
        except Exception:
            return JsonResponse({'Error': '俱乐部不存在'}, status=status.HTTP_400_BAD_REQUEST)
        coin_name = club.coin.name
        records = Record.objects.filter(source__in=[Record.NORMAL, Record.GIVE], roomquiz_id=club_room)
        # whens = [
        #     When(multiplier_choice='A', then=F('bet') * (F('odds')-1))
        # ]
        # multiplier_case = Case(*whens, output_field=DecimalField(), default=0)
        bet_sum = records \
            .extra(select={'date': 'date(quiz_record.created_at)'}) \
            .values('date').annotate(bet_sum=Sum('bet')) \
            .order_by('date')
        coin_out = records \
            .filter(quiz__status=5, option__option__is_right=1) \
            .extra(select={'date': 'date(quiz_record.created_at)'}) \
            .values('date') \
            .annotate(out=Sum(F('bet') * (F('odds') - 1))) \
            .order_by('date')

        coin_in = records \
            .filter(quiz__status=5, option__option__is_right=0) \
            .extra(select={'date': 'date(quiz_record.created_at)'}) \
            .values('date') \
            .annotate(in_count=Sum('bet')) \
            .order_by('date')

        bet_user = records \
            .extra(select={'date': 'date(quiz_record.created_at)'}) \
            .values('date') \
            .annotate(user_count=Count('user_id', distinct=True)) \
            .order_by('date')

        bet_times = records \
            .extra(select={'date': 'date(quiz_record.created_at)'}) \
            .values('date').annotate(rc_count=Count('id')) \
            .order_by('date')
        data = []
        if len(coin_out) == len(coin_in) == len(bet_user) == len(bet_times) == len(bet_sum):
            for a, b, c, d, e in zip(coin_out, coin_in, bet_user, bet_times, bet_sum):
                if a['date'] == b['date'] == c['date'] == d['date']:
                    temp_dict = {
                        'date': a['date'].strftime('%m/%d'),
                        'coin_out': a['out'],
                        'coin_in': b['in_count'],
                        'bet_user': c['user_count'],
                        'bet_times': d['rc_count'],
                        'earn_coin': b['in_count'] - a['out'],
                        'bet_sum': e['bet_sum']
                    }
                    data.append(temp_dict)
                else:
                    return JsonResponse({'Error': '日期不一致'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({'Error': '缺少天数'}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'coin_name': coin_name, 'results': data}, status=status.HTTP_200_OK)


class CoinAllSts(ListAPIView):
    """
    币余额统计
    """

    def list(self, request, *args, **kwargs):
        coins = Coin.objects.all()
        data = []
        for coin in coins:
            total = UserCoin.objects.filter(user__is_robot=0, coin_id=coin).values('coin__name').annotate(
                total_balance=Sum('balance')).order_by('total_balance')
            temp_dict = {
                'coin_name': total[0]['coin__name'],
                'total_balance': normalize_fraction(total[0]['total_balance'], coin.coin_accuracy)
            }
            data.append(temp_dict)
        return JsonResponse({'results': data}, status=status.HTTP_200_OK)


# class AABBCC(ListAPIView):
#
#     def list(self, request, *args, **kwargs):
#         user = User.objects.filter(is_robot=0, integral=0)
#         return JsonResponse({'data':gsg}, status=status.HTTP_200_OK)


class RemainRate(ListAPIView):
    """
    用户留存率
    """

    def list(self, request, *args, **kwargs):
        end_day = datetime.now().date() - timedelta(1)
        register_user = User.objects.filter(is_robot=0, created_at__date__lt=end_day).extra(
            select={'date': 'date(created_at)'}).values('date', 'id').order_by('date')
        temp_user = {}
        for i in register_user:
            date = i['date'].strftime('%Y-%m-%d')
            if date not in temp_user:
                temp_user[date] = [i['id']]
            else:
                temp_user[date].append(i['id'])
        count_dict = {}
        for x in temp_user:
            count_dict[x] = len(temp_user[x])
        for x in temp_user:
            start_day = datetime.strptime(x, '%Y-%m-%d').date() + timedelta(1)
            print(x)
            login_users = LoginRecord.objects.filter(user__in=temp_user[x],
                                                     login_time__date__range=(start_day, end_day)).extra(
                select={'date': 'date(login_time)'}).values('date').annotate(Count('user_id', distinct=True)).order_by(
                'date')
            # user = LoginRecord.objects.filter(user__)
            print(login_users)

        return JsonResponse({'date': count_dict}, status=status.HTTP_200_OK)
