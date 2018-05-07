# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import requests
import json
from api.settings import BASE_DIR
import time, sched
from quiz.models import Quiz
from .get_time import get_time

schedule = sched.scheduler(time.time, time.sleep)
base_url = 'http://i.sporttery.cn/api/match_live_2/get_match_updated?callback=?'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
cache_dir = BASE_DIR + '/spider/live_cache/football'


def perform_command(fun, inc):
    # 安排inc秒后再次运行自己，即周期运行
    schedule.enter(inc, 0, perform_command, (fun, inc))
    fun()


def timming_exe(fun, inc=60):
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    schedule.enter(inc, 0, perform_command, (fun, inc))
    # 持续运行，直到计划时间队列变成空为止
    schedule.run()


def get_live_data():
    url = base_url
    str_list = ''
    time = get_time()[0:10]
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.text
            for i in dt[22:-3].strip('').split('},{'):
                reslut = json.loads('{' + i + '}')
                dt = '\"' + reslut['m_id'] + '\"' + ':' + '{' + i + '}'
                str_list = str_list + ',' + dt
        finall_dt = json.loads('{' + str_list[1:] + '}')
        for key in finall_dt:
            data_list = finall_dt[key]

            match_id = data_list['m_id']

            cache_name = 'cache_' + match_id
            os.chdir(cache_dir)
            dir = list(os.walk(cache_dir))[0][1]
            if time not in dir:
                os.mkdir(time)

            os.chdir(cache_dir+'/'+time)
            files = []
            for root, sub_dirs, files in os.walk(cache_dir+'/'+time):
                files = files
            if cache_name not in files:
                with open(cache_name, 'w+') as f:
                    f.write(data_list['fs_h'] + ':' + data_list['fs_a'])
                if data_list['fs_h'] == '':
                    print('warming')
                else:
                    if Quiz.objects.filter(match_flag=match_id).first() is not None:
                        quiz = Quiz.objects.filter(match_flag=match_id).first()

                        # 2H是下半场,1H是上半场,ht， fs_h是主队进球，fs_a是客队进球
                        host_team_score = data_list['fs_h']
                        guest_team_score = data_list['fs_a']

                        if data_list['status'] == 'Played':
                            quiz.host_team_score = host_team_score
                            quiz.guest_team_score = guest_team_score
                            quiz.status = quiz.ENDED
                        elif data_list['status'] == 'Fixture':
                            quiz.status = quiz.PUBLISHING
                        elif data_list['status'] == 'Playing':
                            quiz.host_team_score = host_team_score
                            quiz.guest_team_score = guest_team_score
                            quiz.status = quiz.REPEALED
                        quiz.save()

                        print(quiz.host_team)
                        print(quiz.guest_team)
                        print(host_team_score + ':' + guest_team_score)
                        print('--------------------------')
                    else:
                        print('不存在该比赛')
            else:
                with open(cache_name, 'r') as f:
                    score = f.readline()

                if score == data_list['fs_h'] + ':' + data_list['fs_a'] or data_list['fs_h'] == '':
                    print('不需要更新')
                    print('--------------------------')
                else:
                    with open(cache_name, 'w+') as f:
                        f.write(data_list['fs_h'] + ':' + data_list['fs_a'])

                    if Quiz.objects.filter(match_flag=match_id).first() is not None:
                        quiz = Quiz.objects.filter(match_flag=match_id).first()

                        # 2H是下半场,1H是上半场,ht， fs_h是主队进球，fs_a是客队进球
                        # score = str(data_list['fs_h']) + ':' + str(data_list['fs_a'])
                        host_team_score = data_list['fs_h']
                        guest_team_score = data_list['fs_a']

                        if data_list['status'] == 'Played':
                            quiz.host_team_score = host_team_score
                            quiz.guest_team_score = guest_team_score
                            quiz.status = quiz.ENDED
                        elif data_list['status'] == 'Fixture':
                            quiz.status = quiz.PUBLISHING
                        elif data_list['status'] == 'Playing':
                            quiz.host_team_score = host_team_score
                            quiz.guest_team_score = guest_team_score
                            quiz.status = quiz.REPEALED
                        quiz.save()

                        print(quiz.host_team)
                        print(quiz.guest_team)
                        print(host_team_score + ':' + guest_team_score)
                        print('--------------------------')
                    else:
                        print('不存在该比赛')
    except requests.ConnectionError as e:
        print('Error', e.args)


class Command(BaseCommand):
    help = "爬取足球直播"

    def handle(self, *args, **options):
        try:
            timming_exe(get_live_data, inc=2)
        except KeyboardInterrupt as e:
            pass
