# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
import datetime
import re
import requests
from bs4 import BeautifulSoup
from quiz.models import Quiz, Rule, Option, Record
from django.db import transaction

base_url = 'http://info.sporttery.cn/basketball/pool_result.php?id='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

result_match = {
    'result_mnl': {
        '主负': 'a',
        '主胜': 'h',
    },
    'result_hdc': {
        '让分主负': 'a',
        '让分主胜': 'h',
    },
    'result_wnm': {
        '主胜1-5': 'w1', '主胜6-10': 'w2', '主胜11-15': 'w3', '主胜16-20': 'w4', '主胜21-25': 'w5', '主胜26+': 'w6',
        '客胜1-5': 'l1', '客胜6-10': 'l2', '客胜11-15': 'l3', '客胜16-20': 'l4', '客胜21-25': 'l5', '客胜26+': 'l6',
    },
    'result_hilo': {
        '大': 'h',
        '小': 'l',
    },
    '未捕抓到数据': '开奖异常'
}


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.content
            return dt
    except requests.ConnectionError as e:
        print('Error', e.args)


def get_data_info(url, match_flag, quiz):
    if quiz.category.parent_id == 1:
        datas = get_data(url + match_flag)
        soup = BeautifulSoup(datas, 'lxml')

        result_score = soup.select('span[class="k_bt"]')[0].string
        if len(re.findall('.*\((.*?:.*?)\)', result_score)) > 0:
            host_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][1]
            guest_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][0]

            # print(result_score)
            # print(guest_team_score + ':' + host_team_score)

            result_list = soup.select('table[class="kj-table"]')
            try:
                result_mnl = result_list[0].select('span[class="win"]')[0].string.replace(' ', '')
                result_mnl_flag = result_match['result_mnl'][result_mnl]
            except:
                print(match_flag + ',' + result_match['未捕抓到数据'])
                print('----------------------------------------')

            try:
                result_hdc = result_list[1].select('span[class="win"]')[0].string
                result_hdc_flag = result_match['result_hdc'][result_hdc]
            except:
                print(match_flag + ',' + result_match['未捕抓到数据'])
                print('----------------------------------------')

            try:
                result_hilo = result_list[2].select('span[class="win"]')[0].string
                result_hilo_flag = result_match['result_hilo'][result_hilo]
            except:
                print(match_flag + ',' + result_match['未捕抓到数据'])
                print('----------------------------------------')

            try:
                result_wnm = result_list[3].select('span[class="win"]')[0].string
                result_wnm_flag = result_match['result_wnm'][result_wnm]
            except:
                print(match_flag + ',' + result_match['未捕抓到数据'])
                print('----------------------------------------')

        else:
            print(match_flag + ',' + '未有开奖信息')

        # ------------------------------------------------------------------------------------------------

        quiz = Quiz.objects.filter(match_flag=match_flag).first()
        quiz.host_team_score = host_team_score
        quiz.guest_team_score = guest_team_score
        quiz.status = quiz.PUBLISHING_ANSWER
        quiz.save()

        rule_all = Rule.objects.filter(quiz=quiz).all()
        rule_mnl = rule_all.filter(type=4).first()
        rule_hdc = rule_all.filter(type=5).first()
        rule_hilo = rule_all.filter(type=6).first()
        rule_wnm = rule_all.filter(type=7).first()

        option = Option.objects.filter(rule=rule_mnl).filter(flag=result_mnl_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_hdc).filter(flag=result_hdc_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_hilo).filter(flag=result_hilo_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_wnm).filter(flag=result_wnm_flag).first()
        option.is_right = 1
        option.save()

        # 分配奖金
        records = Record.objects.filter(quiz=quiz)
        if len(records) > 0:
            for record in records:
                record.earn_coin = record.bet * record.odds
                record.save()
        quiz.status = Quiz.BONUS_DISTRIBUTION
        print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')


class Command(BaseCommand):
    help = "爬取篮球开奖结果"

    # def add_arguments(self, parser):
    #     parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        # 在此基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter((Q(status=Quiz.PUBLISHING) | Q(status=Quiz.ENDED)) & Q(begin_at__lt=after_2_hours))
        for quiz in quizs:
            get_data_info(base_url, quiz.match_flag, quiz)
