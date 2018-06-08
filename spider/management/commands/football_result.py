# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
import requests
import json
from bs4 import BeautifulSoup
from quiz.models import Quiz, Rule, Option, Record, CashBackLog
from users.models import UserCoin, CoinDetail, Coin, UserMessage, User, CoinPrice, CoinGive, CoinGiveRecords
from chat.models import Club
from django.db import transaction
import datetime
from decimal import Decimal

base_url = 'http://i.sporttery.cn/api/fb_match_info/get_pool_rs/?f_callback=pool_prcess&mid='
live_url = 'http://i.sporttery.cn/api/match_info_live_2/get_match_live?m_id='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def trunc(f, n):
    s1, s2 = str(f).split('.')
    if n == 0:
        return s1
    if n <= len(s2):
        return s1 + '.' + s2[:n]
    return s1 + '.' + s2 + '0' * (n - len(s2))


def handle_activity(record, coin, earn_coin):
    # USDT活动
    if CoinGiveRecords.objects.filter(user=record.user, coin_give__coin=coin).exists() is True:
        coin_give_records = CoinGiveRecords.objects.get(user=record.user, coin_give__coin=coin)
        if int(record.source) == Record.GIVE:
            if coin_give_records.is_recharge_lock is False:
                coin_give_records.lock_coin = coin_give_records.lock_coin + Decimal(earn_coin)
                coin_give_records.save()
                coin_give_records = CoinGiveRecords.objects.get(user=record.user, coin_give__coin=coin)
                if (coin_give_records.lock_coin >= coin_give_records.coin_give.ask_number) and (
                        Record.objects.filter(user=record.user,
                                              roomquiz_id=Club.objects.get(
                                                  coin=coin).id).count() >= coin_give_records.coin_give.match_number) and (
                        datetime.datetime.now() <= coin_give_records.coin_give.end_time):
                    lock_coin = coin_give_records.lock_coin
                    coin_give_records.is_recharge_lock = True
                    coin_give_records.lock_coin = 0
                    coin_give_records.save()

                    # 发送信息
                    u_mes = UserMessage()
                    u_mes.status = 0
                    u_mes.user_id = record.user_id
                    u_mes.message_id = 6  # 私人信息
                    u_mes.title = Club.objects.get(coin=coin).room_title + '活动公告'
                    u_mes.content = '恭喜您获得USDT活动奖励共 ' + str(trunc(lock_coin, 2)) + 'USDT，祝贺您。'
                    u_mes.save()
        else:
            user_profit = 0
            for user_record in Record.objects.filter(user=record.user,
                                                     roomquiz_id=Club.objects.get(coin=coin).id,
                                                     source=str(Record.NORMAL),
                                                     created_at__lte=coin_give_records.coin_give.end_time,
                                                     earn_coin__gte=0):
                user_profit = user_profit + (user_record.earn_coin - user_record.bet)
            if (user_profit >= 50) and (coin_give_records.is_recharge_give is False) and (
                    datetime.datetime.now() <= coin_give_records.coin_give.end_time):
                coin_give_records.is_recharge_give = True
                coin_give_records.save()

                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
                user_coin.balance += Decimal(10)
                user_coin.save()

                # 用户资金明细表
                coin_detail = CoinDetail()
                coin_detail.user_id = record.user_id
                coin_detail.coin_name = coin.name
                coin_detail.amount = Decimal(10)
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.ACTIVITY
                coin_detail.save()

                # 发送信息
                u_mes = UserMessage()
                u_mes.status = 0
                u_mes.user_id = record.user_id
                u_mes.message_id = 6  # 私人信息
                u_mes.title = Club.objects.get(coin=coin).room_title + '活动公告'
                u_mes.content = '恭喜您获得USDT活动奖励共 10USDT，祝贺您。'
                u_mes.save()
    else:
        pass


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
    quiz = Quiz.objects.get(match_flag=match_flag)
    rule_all = Rule.objects.filter(quiz=quiz).all()
    rule_had = rule_all.get(type=0)
    rule_hhad = rule_all.get(type=1)
    rule_ttg = rule_all.get(type=3)
    rule_crs = rule_all.get(type=2)

    result_flag = False
    try:
        result_list = []
        new_url = 'http://www.310win.com/jingcaizuqiu/kaijiang_jc_all.html'
        response = requests.get(new_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'lxml')
        data = list(soup.select('div[id="lottery_container"]')[0].children)
        for dt in data[1].find_all('tr')[1:]:
            host_team_fullname = list(dt.select('td[style="text-align:right"]')[0].strings)[0].strip().replace('\n', '')
            guest_team_fullname = dt.select('td[style="text-align:left"]')[0].string.replace(' ', '')
            score = dt.select('td[style="color:red"]')[0].b.string
            host_team_score = score.split('-')[0]
            guest_team_score = score.split('-')[1]
            ttg_list = []
            for i in range(0, 7):
                ttg_list.append(str(i))
            if (quiz.host_team_fullname == host_team_fullname or quiz.host_team == host_team_fullname) and (
                    quiz.guest_team_fullname == guest_team_fullname or quiz.guest_team == guest_team_fullname):
                quiz.host_team_score = host_team_score
                quiz.guest_team_score = guest_team_score
                quiz.save()
                for result in dt.select('span[style="color:#f00;"]')[:-1]:
                    if result.string == '负' or result.string == '胜':
                        result_list.append('主' + result.string)
                    elif result.string == '平':
                        result_list.append(result.string + '局')
                    elif result.string in ttg_list:
                        result_list.append(result.string + '球')
                    elif result.string == '7+':
                        result_list.append('7球以上')
                    else:
                        result_list.append(result.string)

                option_had = Option.objects.filter(rule=rule_had).filter(option=result_list[1]).first()
                if option_had is not None:
                    option_had.is_right = 1

                option_hhad = Option.objects.filter(rule=rule_hhad).filter(option=result_list[0]).first()
                if option_hhad is not None:
                    option_hhad.is_right = 1

                option_ttg = Option.objects.filter(rule=rule_ttg).filter(option=result_list[3]).first()
                if option_ttg is not None:
                    option_ttg.is_right = 1

                option_crs = Option.objects.filter(rule=rule_crs).filter(option=result_list[2]).first()
                if option_crs is not None:
                    option_crs.is_right = 1

                option_had.save()
                option_hhad.save()
                option_ttg.save()
                option_crs.save()

                print('result_list===========================================>', result_list)
                print('--------------------------- new new new ------------------------------')
                result_flag = True
                break
            else:
                result_flag = False
    except:
        pass

    if result_flag is False:
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
                        print('no score')
                        score_url = 'http://i.sporttery.cn/api/fb_match_info/get_result_his?limit=10&is_ha=all&limit=10&c_id=0&mid=' + match_flag + '&ptype[]=three_-1&ptype[]=asia_229&&f_callback=getResultHistoryInfo'
                        response_score = requests.get(score_url, headers=headers)
                        dt = response_score.text.encode("utf-8").decode('unicode_escape')
                        score_dt = eval(dt[21:-2])

                        for score in score_dt['result']['data']:
                            if score['h_cn_abbr'] == quiz.host_team and score['a_cn_abbr'] == quiz.guest_team:
                                if score['final'] != '':
                                    host_team_score = score['final'].split(':')[0]
                                    guest_team_score = score['final'].split(':')[1]
                                    print('===================================================', score['final'])
                                    break
                                else:
                                    print('really no score')
                                    print('=================================')
                                    return
                            else:
                                print('no mtach,return')
                                return
                    else:
                        host_team_score = score_data['fs_h']
                        guest_team_score = score_data['fs_a']

                    quiz.host_team_score = host_team_score
                    quiz.guest_team_score = guest_team_score
                    quiz.save()

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

            quiz.host_team_score = host_team_score
            quiz.guest_team_score = guest_team_score
            quiz.save()

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
    else:
        pass

    flag = False
    # 分配奖金
    records = Record.objects.filter(quiz=quiz, is_distribution=False)
    if len(records) > 0:
        for record in records:
            # 用户增加对应币金额
            club = Club.objects.get(pk=record.roomquiz_id)

            # 获取币信息
            coin = Coin.objects.get(pk=club.coin_id)

            flag = True
            # 判断是否回答正确
            is_right = False
            if record.rule_id == rule_had.id:
                if record.option.option_id == option_had.id:
                    is_right = True
            if record.rule_id == rule_hhad.id:
                if record.option.option_id == option_hhad.id:
                    is_right = True
            if record.rule_id == rule_ttg.id:
                if record.option.option_id == option_ttg.id:
                    is_right = True
            if record.rule_id == rule_crs.id:
                if record.option.option_id == option_crs.id:
                    is_right = True

            earn_coin = record.bet * record.odds
            record.type = Record.CORRECT
            # 对于用户来说，答错只是记录下注的金额
            if is_right is False:
                earn_coin = '-' + str(record.bet)
                record.type = Record.MISTAKE
            record.earn_coin = earn_coin
            record.save()

            if is_right is True:
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
                coin_detail.sources = CoinDetail.OPEB_PRIZE
                coin_detail.save()

                # handle  USDT活动
                handle_activity(record, coin, earn_coin)

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = record.user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = club.room_title + '开奖公告'
            option_right = Option.objects.get(rule=record.rule, is_right=True)
            if is_right is False:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option.option + '，您答错了。'
            elif is_right is True:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option.option + '，您的奖金是:' + str(
                    round(earn_coin, 3))
            u_mes.save()

            record.is_distribution = True
            record.save()

    quiz.status = Quiz.BONUS_DISTRIBUTION
    quiz.save()
    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')
    return flag


def handle_delay_game(delay_quiz):
    records = Record.objects.filter(quiz=delay_quiz, is_distribution=False)
    if len(records) > 0:
        for record in records:
            # 延迟比赛，返回用户投注的钱
            return_coin = record.bet
            record.earn_coin = return_coin
            record.type = Record.ABNORMAL
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
            u_mes.title = club.room_title + '退回公告'
            u_mes.content = delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 赛事延期或已中断(您的下注已全额退回)'
            u_mes.save()

            record.is_distribution = True
            record.save()

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


def cash_back(quiz):
    cash_back_rate = 0.5
    for club in Club.objects.filter(~Q(room_title='HAND俱乐部')):
        records = Record.objects.filter(quiz=quiz, roomquiz_id=club.id, user__is_robot=False)
        if len(records) > 0:
            platform_sum = 0
            profit = 0
            cash_back_sum = 0
            user_list = []
            coin_price = CoinPrice.objects.get(coin_name=club.room_title[:-3])
            for record in records:
                platform_sum = platform_sum + record.bet
                if record.earn_coin > 0:
                    profit = profit + (record.earn_coin - record.bet)
                else:
                    profit = profit + record.earn_coin
                if record.user_id not in user_list:
                    user_list.append(record.user_id)

            print('club====>' + club.room_title)
            if profit <= 0:
                print('profit====>' + str(abs(profit)))
            elif profit > 0:
                print('profit====>' + '-' + str(profit))
            print('platform_sum====>' + str(platform_sum))

            if profit < 0:
                profit_abs = abs(profit)
                for user_id in user_list:
                    personal_sum = 0
                    for record_personal in records.filter(user_id=user_id):
                        personal_sum = personal_sum + record_personal.bet
                    gsg_cash_back = float(profit_abs) * cash_back_rate * (float(personal_sum) / float(platform_sum)) * (
                            float(coin_price.price) / float(CoinPrice.objects.get(coin_name='GSG').price))
                    gsg_cash_back = trunc(gsg_cash_back, 2)
                    if float(gsg_cash_back) > 0:
                        user = User.objects.get(pk=user_id)
                        user.integral = float(user.integral) + float(gsg_cash_back)
                        user.save()

                        # 用户资金明细表
                        coin_detail = CoinDetail()
                        coin_detail.user_id = user_id
                        coin_detail.coin_name = "GSG"
                        coin_detail.amount = float(gsg_cash_back)
                        coin_detail.rest = user.integral
                        coin_detail.sources = CoinDetail.CASHBACK
                        coin_detail.save()

                        # 发送信息
                        u_mes = UserMessage()
                        u_mes.status = 0
                        u_mes.user_id = user_id
                        u_mes.message_id = 6  # 私人信息
                        u_mes.title = club.room_title + '返现公告'
                        u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖' + ',您得到的返现为：' + str(
                            gsg_cash_back) + '个GSG'
                        u_mes.save()

                        print('use_id===>' + str(user_id) + ',cash_back====>' + str(gsg_cash_back))

                        cash_back_sum = cash_back_sum + float(gsg_cash_back)

            cash_back_log = CashBackLog()
            cash_back_log.quiz = quiz
            cash_back_log.roomquiz_id = club.id
            cash_back_log.platform_sum = platform_sum
            if profit <= 0:
                cash_back_log.profit = abs(profit)
            elif profit > 0:
                cash_back_log.profit = float('-' + str(profit))
            cash_back_log.cash_back_sum = cash_back_sum
            cash_back_log.coin_proportion = cash_back_rate
            cash_back_log.save()

            print('cash_back_sum====>' + str(cash_back_sum))
            print('---------------------------')
            quiz.is_reappearance = 1
            quiz.save()
    print('\n')


class Command(BaseCommand):
    help = "爬取足球开奖结果"

    # def add_arguments(self, parser):
    #     parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        after_24_hours = datetime.datetime.now() - datetime.timedelta(hours=24)
        if Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                               category__parent_id=2).exists():
            for delay_quiz in Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                                                  category__parent_id=2):
                delay_quiz.status = Quiz.DELAY
                handle_delay_game(delay_quiz)
                delay_quiz.save()

        # 在此基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter(
            (Q(status=str(Quiz.PUBLISHING)) | Q(status=str(Quiz.ENDED))) & Q(begin_at__lt=after_2_hours) & Q(
                category__parent_id=2))
        if quizs.exists():
            for quiz in quizs:
                print(quiz.match_flag)
                if int(Quiz.objects.filter(match_flag=quiz.match_flag).first().status) != Quiz.BONUS_DISTRIBUTION:
                    if quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                    guest_team=quiz.guest_team).count() >= 2:
                        handle_unusual_game(quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                                         guest_team=quiz.guest_team))
                    else:
                        flag = get_data_info(base_url, quiz.match_flag)
                        # print(Quiz.objects.get(match_flag=quiz.match_flag).status)
                        if int(Quiz.objects.get(
                                match_flag=quiz.match_flag).status) == Quiz.BONUS_DISTRIBUTION and flag is True:
                            cash_back(Quiz.objects.get(match_flag=quiz.match_flag))
        else:
            print('暂无比赛需要开奖')

        # quiz = Quiz.objects.filter(match_flag=options['match_flag']).first()
        # get_data_info(base_url, options['match_flag'])
