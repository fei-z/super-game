# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import requests
import json
from quiz.models import Quiz, Rule, Option, Record
from users.models import UserCoin, CoinDetail, Coin, UserMessage
from chat.models import Club
from django.db import transaction
import datetime
from decimal import Decimal

base_url = 'http://i.sporttery.cn/api/fb_match_info/get_pool_rs/?f_callback=pool_prcess&mid='
live_url = 'http://i.sporttery.cn/api/match_info_live_2/get_match_live?m_id='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[12:-2])
            return result
    except requests.ConnectionError as e:
        print('Error', e.args)


@transaction.atomic()
def get_data_info(url, match_flag, result_data=None, host_team_score=None, guest_team_score=None):
    if result_data is None:
        datas = get_data(url + match_flag)
        if datas['status']['code'] == 0:
            if len(datas['result']['pool_rs']) > 0:
                result_had = datas['result']['pool_rs']['had']
                result_hhad = datas['result']['pool_rs']['hhad']
                result_ttg = datas['result']['pool_rs']['ttg']
                result_crs = datas['result']['pool_rs']['crs']
                # result_hafu = datas['result']['pool_rs']['hafu']

                score_status = requests.get(live_url + match_flag).json()['status']
                score_data = requests.get(live_url + match_flag).json()['data']
                if score_status['message'] == "no data":
                    print(match_flag)
                    print('no score')
                    print('----------------')
                    return
                else:
                    host_team_score = score_data['fs_h']
                    guest_team_score = score_data['fs_a']
            else:
                print(match_flag + ',' + '未有开奖信息')
                return
        else:
            print(match_flag + ',' + '未请求到任务数据')
            return
    else:
        datas = result_data
        result_had = datas['result']['pool_rs']['had']
        result_hhad = datas['result']['pool_rs']['hhad']
        result_ttg = datas['result']['pool_rs']['ttg']
        result_crs = datas['result']['pool_rs']['crs']

    quiz = Quiz.objects.filter(match_flag=match_flag).first()
    quiz.host_team_score = host_team_score
    quiz.guest_team_score = guest_team_score
    quiz.save()

    rule_all = Rule.objects.filter(quiz=quiz).all()
    rule_had = rule_all.filter(type=0).first()
    rule_hhad = rule_all.filter(type=1).first()
    rule_ttg = rule_all.filter(type=3).first()
    rule_crs = rule_all.filter(type=2).first()

    option_had = Option.objects.filter(rule=rule_had).filter(flag=result_had['pool_rs']).first()
    if option_had is not None:
        option_had.is_right = 1
        option_had.save()

    option_hhad = Option.objects.filter(rule=rule_hhad).filter(flag=result_hhad['pool_rs']).first()
    if option_hhad is not None:
        option_hhad.is_right = 1
        option_hhad.save()

    option_ttg = Option.objects.filter(rule=rule_ttg).filter(flag=result_ttg['pool_rs']).first()
    if option_ttg is not None:
        option_ttg.is_right = 1
        option_ttg.save()

    option_crs = Option.objects.filter(rule=rule_crs).filter(flag=result_crs['pool_rs']).first()
    if option_crs is not None:
        option_crs.is_right = 1
        option_crs.save()

    # 分配奖金
    records = Record.objects.filter(quiz=quiz)
    if len(records) > 0:
        for record in records:
            # 判断是否回答正确
            is_right = False
            if record.rule_id == rule_had.id:
                if record.option_id == option_had.id:
                    is_right = True
            if record.rule_id == rule_hhad.id:
                if record.option_id == option_hhad.id:
                    is_right = True
            if record.rule_id == rule_ttg.id:
                if record.option_id == option_ttg.id:
                    is_right = True
            if record.rule_id == rule_crs.id:
                if record.option_id == option_crs.id:
                    is_right = True

            earn_coin = record.bet * record.odds
            # 对于用户来说，答错只是记录下注的金额
            if is_right is False:
                earn_coin = '-' + str(record.bet)
            record.earn_coin = earn_coin
            record.save()

            if is_right is True:
                # 用户增加对应币金额
                club = Club.objects.get(pk=record.roomquiz_id)

                # 获取币信息
                coin = Coin.objects.get(pk=club.coin_id)

                try:
                    user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
                except UserCoin.DoesNotExist:
                    user_coin = UserCoin()

                user_coin.coin_id = club.coin_id
                user_coin.user_id = record.user_id
                user_coin.balance += Decimal(earn_coin)
                user_coin.save()

                # 用户资金明细表
                coin_detail = CoinDetail()
                coin_detail.user_id = record.user_id
                coin_detail.coin_name = coin.name
                coin_detail.amount = Decimal(earn_coin)
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.BETS
                coin_detail.save()

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = record.user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = '开奖公告'
            option_right = Option.objects.get(rule=record.rule, is_right=True)
            if is_right is False:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + '已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option + '，您答错了。'
            elif is_right is True:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + '已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option + '，您的奖金是:' + str(round(earn_coin, 3))
            u_mes.save()

    quiz.status = Quiz.BONUS_DISTRIBUTION
    quiz.save()
    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')


def handle_delay_game(delay_quiz):
    records = Record.objects.filter(quiz=delay_quiz)
    if len(records) > 0:
        for record in records:
            # 延迟比赛，返回用户投注的钱
            return_coin = record.bet
            record.earn_coin = return_coin
            record.save()

            # 用户增加回退还金额
            club = Club.objects.get(pk=record.roomquiz_id)

            # 获取币信息
            coin = Coin.objects.get(pk=club.coin_id)

            try:
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
            except UserCoin.DoesNotExist:
                user_coin = UserCoin()

            user_coin.coin_id = club.coin_id
            user_coin.user_id = record.user_id
            user_coin.balance += Decimal(return_coin)
            user_coin.save()

            # 用户资金明细表
            coin_detail = CoinDetail()
            coin_detail.user_id = record.user_id
            coin_detail.coin_name = coin.name
            coin_detail.amount = Decimal(return_coin)
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.RETURN
            coin_detail.save()

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = record.user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = '退回公告'
            u_mes.content = delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + '赛事延期或已中断(您的下注已全额退回)'
            u_mes.save()

            print(delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 返还成功！共' + str(len(records)) + '条投注记录！')


def handle_unusual_game(quiz_list):
    result_data = ''
    host_team_score = ''
    guest_team_score = ''
    for quiz in quiz_list:
        datas = get_data(base_url + quiz.match_flag)
        if len(datas['result']['pool_rs']) > 0:
            result_data = datas

        score_json = requests.get(live_url + quiz.match_flag).json()
        score_status = score_json['status']
        score_data = score_json['data']
        if score_status['message'] == "no data":
            pass
        else:
            host_team_score = score_data['fs_h']
            guest_team_score = score_data['fs_a']

    if result_data != '' and host_team_score != '' and guest_team_score != '':
        for quiz in quiz_list:
            get_data_info(base_url, quiz.match_flag, result_data, host_team_score, guest_team_score)


class Command(BaseCommand):
    help = "爬取足球开奖结果"

    # def add_arguments(self, parser):
    #     parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        after_24_hours = datetime.datetime.now() - datetime.timedelta(hours=24)
        if Quiz.objects.filter(begin_at__lt=after_24_hours, status=Quiz.PUBLISHING, category__parent_id=2).exists():
            for delay_quiz in Quiz.objects.filter(begin_at__lt=after_24_hours, status=Quiz.PUBLISHING,
                                                  category__parent_id=2):
                delay_quiz.status = Quiz.DELAY
                handle_delay_game(delay_quiz)
                delay_quiz.save()

        # 在此基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter(
            (Q(status=Quiz.PUBLISHING) | Q(status=Quiz.ENDED)) & Q(begin_at__lt=after_2_hours) & Q(
                category__parent_id=2))
        if quizs.exists():
            for quiz in quizs:
                # print(quiz.match_flag)
                if int(Quiz.objects.filter(match_flag=quiz.match_flag).first().status) != Quiz.BONUS_DISTRIBUTION:
                    if quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                    guest_team=quiz.guest_team).count() >= 2:
                        handle_unusual_game(quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                                         guest_team=quiz.guest_team))
                    else:
                        get_data_info(base_url, quiz.match_flag)
        else:
            print('暂无比赛需要开奖')

        # quiz = Quiz.objects.filter(match_flag=options['match_flag']).first()
        # get_data_info(base_url, options['match_flag'])
