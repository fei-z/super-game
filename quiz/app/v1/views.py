# -*- coding: UTF-8 -*-
from base.app import FormatListAPIView, FormatRetrieveAPIView, CreateAPIView
from django.db import transaction
from django.db.models import Q
from base.function import LoginRequired
from base.app import ListAPIView, ListCreateAPIView
from ...models import Category, Quiz, Record, Rule, Option, OptionOdds
from users.models import UserCoin, CoinValue, CoinDetail
from chat.models import Club
from users.models import UserCoin, CoinValue
from base.exceptions import ParamErrorException
from base import code as error_code
from decimal import Decimal
from .serializers import QuizSerialize, RecordSerialize, QuizDetailSerializer, QuizPushSerializer
from utils.functions import value_judge
from datetime import datetime
import time
import re
from utils.functions import normalize_fraction


class CategoryView(ListAPIView):
    """
    竞猜分类
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        categorys = Category.objects.filter(parent_id=None)
        data = []
        for category in categorys:
            children = []
            categoryslist = Category.objects.filter(parent_id=category.id, is_delete=0).order_by("order")
            for categorylist in categoryslist:
                number = Quiz.objects.filter(category_id=categorylist.id).count()
                if number <= 0:
                    continue
                children.append({
                    "category_id": categorylist.id,
                    "category_name": categorylist.name,
                })
            data.append({
                "category_id": category.id,
                "category_name": category.name,
                "children": children
            })
        return self.response({'code': 0, 'data': data})


class HotestView(ListAPIView):
    """
    热门比赛
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status=0, is_delete=False).order_by('-total_people')[:10]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        return self.response({'code': 0, 'data': items})


class QuizListView(ListCreateAPIView):
    """
    获取竞猜列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        if 'is_user' not in self.request.GET:
            if 'category' not in self.request.GET or self.request.GET['category'] == '':
                if int(self.request.GET.get('type')) == 1:  # 未结束
                    return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2), is_delete=False).order_by(
                        'begin_at')
                elif int(self.request.GET.get('type')) == 2:  # 已结束
                    return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5), is_delete=False).order_by(
                        '-begin_at')
            category_id = str(self.request.GET.get('category'))
            category_arr = category_id.split(',')
            if int(self.request.GET.get('type')) == 1:  # 未开始
                return Quiz.objects.filter(Q(status=0) | Q(status=1) | Q(status=2), is_delete=False,
                                           category__in=category_arr).order_by('begin_at')
            elif int(self.request.GET.get('type')) == 2:  # 已结束
                return Quiz.objects.filter(Q(status=3) | Q(status=4) | Q(status=5), is_delete=False,
                                           category__in=category_arr).order_by(
                    '-begin_at')
        else:
            user_id = self.request.user.id
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            quiz_id = list(
                set(Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).values_list('quiz_id', flat=True)))
            my_quiz = Quiz.objects.filter(id__in=quiz_id).order_by('-begin_at')
            return my_quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        value = results.data.get('results')
        return self.response({"code": 0, "data": value})


class RecordsListView(ListCreateAPIView):
    """
    竞猜记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        if 'user_id' not in self.request.GET:
            user_id = self.request.user.id
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            if 'is_end' not in self.request.GET:
                record = Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).order_by('-created_at')
                return record
            else:
                is_end = self.request.GET.get('is_end')
                if int(is_end) == 1:
                    return Record.objects.filter(Q(quiz__status=0) | Q(quiz__status=1) | Q(quiz__status=2),
                                                 user_id=user_id,
                                                 roomquiz_id=roomquiz_id).order_by('-created_at')
                else:
                    return Record.objects.filter(Q(quiz__status=3) | Q(quiz__status=4) | Q(quiz__status=5),
                                                 user_id=user_id,
                                                 roomquiz_id=roomquiz_id).order_by('-created_at')
        else:
            user_id = self.request.GET.get('user_id')
            roomquiz_id = self.request.parser_context['kwargs']['roomquiz_id']
            return Record.objects.filter(user_id=user_id, roomquiz_id=roomquiz_id).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        Progress = results.data.get('results')
        data = []
        # quiz_id = ''
        tmp = ''
        # time = ''
        # host = ''
        # guest = ''
        for fav in Progress:
            # record = fav.get('pk')
            # quiz = fav.get('quiz_id')
            pecific_dates = fav.get('created_at')[0].get('years')
            pecific_date = fav.get('created_at')[0].get('year')
            # pecific_time = fav.get('created_at')[0].get('time')
            # host_team = fav.get('host_team')
            # guest_team = fav.get('guest_team')
            # if tmp == pecific_date and time == pecific_time and host == host_team and guest == guest_team:
            #     host_team = ""
            #     guest_team = ""
            # else:
            #     host = host_team
            #     guest = guest_team
            #
            # if tmp == pecific_date and time == pecific_time:
            #     pecific_time = ""
            # else:
            #     time = pecific_time
            if tmp == pecific_date:
                pecific_date = ""
                pecific_dates = ""
            else:
                tmp = pecific_date
            # records = Record.objects.get(pk=record)
            # earn_coin = records.earn_coin
            # print("earn_coin=================", earn_coin)
            # if quiz_id==quiz:
            #     pass
            # else:
            #     quiz_id=quiz
            bet = fav.get('bet')
            data.append({
                "quiz_id": fav.get('quiz_id'),
                'host_team': fav.get('host_team'),
                'guest_team': fav.get('guest_team'),
                'earn_coin': fav.get('earn_coin'),
                'pecific_dates': pecific_dates,
                'pecific_date': pecific_date,
                'pecific_time': fav.get('created_at')[0].get('time'),
                'my_option': fav.get('my_option')[0].get('my_option'),
                'is_right': fav.get('my_option')[0].get('is_right'),
                'coin_avatar': fav.get('coin_avatar'),
                'category_name': fav.get('quiz_category'),
                'coin_name': fav.get('coin_name'),
                'bet': fav.get('bets')
            })
        return self.response({'code': 0, 'data': data})


class QuizDetailView(ListAPIView):
    """
    竞猜详情
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizDetailSerializer

    def get_queryset(self):
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        quiz = Quiz.objects.filter(pk=quiz_id)
        return quiz

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        item = items[0]
        return self.response({"code": 0, "data": {
            "id": item['id'],
            "host_team": item['host_team'],
            "host_team_score": item['host_team_score'],
            "guest_team": item['guest_team'],
            "guest_team_score": item['guest_team_score'],
            "begin_at": item['start'],
            "year": item['year'],
            "time": item['time'],
            "status": item['status']
        }})


class QuizPushView(ListAPIView):
    """
    下注页面推送
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizPushSerializer

    def get_queryset(self):
        roomquiz_id = self.request.GET.get('roomquiz_id')
        quiz_id = self.request.parser_context['kwargs']['quiz_id']
        record = Record.objects.filter(quiz_id=quiz_id, roomquiz_id=roomquiz_id)
        return record

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "username": item['username'],
                    "my_rule": item['my_rule'],
                    "my_option": item['my_option'],
                    "bet": item['bet']
                }
            )
        return self.response({"code": 0, "data": data})


class RuleView(ListAPIView):
    """
    竞猜选项
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = request.user.id
        roomquiz_id = self.request.GET.get('roomquiz_id')
        quiz_id = kwargs['quiz_id']
        rule = Rule.objects.filter(quiz_id=quiz_id).order_by('type')
        clubinfo = Club.objects.get(pk=int(roomquiz_id))
        coin_id = clubinfo.coin.pk
        coin_betting_control = clubinfo.coin.betting_control
        coin_betting_control = normalize_fraction(coin_betting_control, int(clubinfo.coin.coin_accuracy))
        coin_betting_toplimit = clubinfo.coin.betting_toplimit
        coin_betting_toplimit = normalize_fraction(coin_betting_toplimit, int(clubinfo.coin.coin_accuracy))
        usercoin = UserCoin.objects.get(user_id=user, coin_id=coin_id)
        is_bet = usercoin.id
        balance = normalize_fraction(usercoin.balance, int(clubinfo.coin.coin_accuracy))
        coin_name = usercoin.coin.name
        coin_icon = usercoin.coin.icon

        coinvalue = CoinValue.objects.filter(coin_id=coin_id).order_by('value')
        value1 = coinvalue[0].value
        value1 = normalize_fraction(value1, coinvalue[0].coin.coin_accuracy)
        value2 = coinvalue[1].value
        value2 = normalize_fraction(value2, coinvalue[0].coin.coin_accuracy)
        value3 = coinvalue[2].value
        value3 = normalize_fraction(value3, coinvalue[0].coin.coin_accuracy)
        data = []
        for i in rule:
            # option = Option.objects.filter(rule_id=i.pk).order_by('order')
            option = OptionOdds.objects.filter(option__rule_id=i.pk, club_id=roomquiz_id).order_by('option__order')
            list = []
            total = Record.objects.filter(rule_id=i.pk).count()
            print("total===================================", total)
            for s in option:
                is_record = Record.objects.filter(user_id=user, roomquiz_id=roomquiz_id, option_id=s.pk).count()
                is_choice = 0
                if int(is_record) > 0:
                    is_choice = 1
                # odds = normalize_fraction(s.odds, int(coinvalue[0].coin.coin_accuracy))
                odds = normalize_fraction(s.odds, 2)
                number = Record.objects.filter(rule_id=i.pk, option_id=s.pk).count()
                print("number===================================", number)
                if number == 0 or total == 0:
                    accuracy = "0"
                else:
                    accuracy = number / total
                    print("accuracy=============================", accuracy)
                    accuracy = Decimal(accuracy).quantize(Decimal('0.00'))
                    print("accuracy======================================", accuracy)
                list.append({
                    "option_id": s.pk,
                    "option": s.option.option,
                    "odds": odds,
                    "option_type": s.option.option_type,
                    "is_right": s.option.is_right,
                    "number": number,
                    "accuracy": accuracy,
                    "is_choice": is_choice,
                    "order": s.option.order
                })
            print("list===============================", list)
            # 比分
            win = []
            flat = []
            loss = []
            if int(i.type) == 2:
                for l in list:
                    if str(l['option_type']) == "胜":
                        win.append(l)
                    elif str(l['option_type']) == "平":
                        flat.append(l)
                    else:
                        loss.append(l)
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list_win": win,
                    "list_flat": flat,
                    "list_loss": loss
                })
            elif int(i.type) == 7:
                for l in list:
                    if str(l['option_type']) == "主胜":
                        win.append(l)
                    else:
                        loss.append(l)
                    win.sort(key=lambda x: x["order"])
                    flat.sort(key=lambda x: x["order"])
                    loss.sort(key=lambda x: x["order"])
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list_win": win,
                    "list_loss": loss,
                })
            else:
                data.append({
                    "quiz_id": i.quiz_id,
                    "type": i.TYPE_CHOICE[int(i.type)][1],
                    "tips": i.tips,
                    "home_let_score": normalize_fraction(i.home_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "guest_let_score": normalize_fraction(i.guest_let_score, int(coinvalue[0].coin.coin_accuracy)),
                    "estimate_score": normalize_fraction(i.estimate_score, int(coinvalue[0].coin.coin_accuracy)),
                    "list": list
                })
        return self.response({'code': 0, 'data': data,
                              'list': {'is_bet': is_bet, 'balance': balance, 'coin_name': coin_name,
                                       'coin_icon': coin_icon, 'coin_betting_control': coin_betting_control,
                                       'coin_betting_toplimit': coin_betting_toplimit, 'value1': value1,
                                       'value2': value2, 'value3': value3}})


class BetView(ListCreateAPIView):
    """
    竞猜下注
    """

    # max_wager = 10000
    def get_queryset(self):
        pass

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        value = value_judge(request, "quiz_id", "option", "wager", "roomquiz_id")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = request.user
        quiz_id = self.request.data['quiz_id']  # 获取竞猜ID
        roomquiz_id = self.request.data['roomquiz_id']  # 获取俱乐部ID
        # 单个下注
        option = self.request.data['option']  # 获取选项ID
        coins = self.request.data['wager']  # 获取投注金额
        coins = float(coins)
        try:  # 判断选项ID是否有效
            option_odds = OptionOdds.objects.get(pk=option)
        except Exception:
            raise ParamErrorException(error_code.API_50101_QUIZ_OPTION_ID_INVALID)
        i = 0
        Decimal(i)
        # 判断赌注是否有效
        if i >= Decimal(coins):
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
        quiz = Quiz.objects.get(pk=quiz_id)  # 判断比赛
        nowtime = datetime.now()
        if nowtime > quiz.begin_at:
            raise ParamErrorException(error_code.API_50108_THE_GAME_HAS_STARTED)
        if int(quiz.status) != 0 or quiz.is_delete is True:
            raise ParamErrorException(error_code.API_50107_USER_BET_TYPE_ID_INVALID)
        clubinfo = Club.objects.get(pk=int(roomquiz_id))
        coin_betting_control = float(clubinfo.coin.betting_control)
        coin_betting_toplimit = float(clubinfo.coin.betting_toplimit)
        if coin_betting_control > coins or coin_betting_toplimit < coins:
            raise ParamErrorException(error_code.API_50102_WAGER_INVALID)
        coin_id = clubinfo.coin.pk
        usercoin = UserCoin.objects.get(user_id=user.id, coin_id=coin_id)
        # 判断用户金币是否足够
        if float(usercoin.balance) < coins:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        rule_id = option_odds.option.rule_id

        # 调整赔率
        Option.objects.change_odds(rule_id, coin_id, roomquiz_id)

        record = Record()
        record.user = user
        record.quiz = quiz
        record.roomquiz_id = roomquiz_id
        record.rule_id = rule_id
        record.option = option_odds
        record.bet = round(Decimal(coins), 3)
        record.odds = round(Decimal(option_odds.odds), 2)
        record.save()
        earn_coins = Decimal(coins) * option_odds.odds
        earn_coins = round(earn_coins, 3)
        # 用户减少金币
        usercoin.balance = float(usercoin.balance - Decimal(coins))
        usercoin.save()
        quiz.total_people += 1
        quiz.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = usercoin.coin.name
        coin_detail.amount = '-' + str(coins)
        coin_detail.rest = Decimal(usercoin.balance)
        coin_detail.sources = 3
        coin_detail.save()
        response = {
            'code': 0,
            'data': {
                'message': '下注成功，金额总数为 ' + str(
                    normalize_fraction(coins, int(usercoin.coin.coin_accuracy))) + '，预计可得猜币 ' + str(
                    normalize_fraction(earn_coins, int(usercoin.coin.coin_accuracy))),
                'balance': normalize_fraction(usercoin.balance, int(usercoin.coin.coin_accuracy))
            }
        }
        return self.response(response)


class RecommendView(ListAPIView):
    """
    竞猜推荐
    """
    permission_classes = (LoginRequired,)
    serializer_class = QuizSerialize

    def get_queryset(self):
        return Quiz.objects.filter(status__lt=2, is_delete=False).order_by('-total_people')[:20]

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "quiz_id": item['id'],
                    "match": item['host_team'] + " VS " + item['guest_team'],
                    "match_time": datetime.strftime(datetime.fromtimestamp(item['begin_at']), '%H:%M')
                }
            )
        return self.response({"code": 0, "data": data})
