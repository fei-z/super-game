# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from marksix.models import OpenPrice, Number, Animals, Option
import datetime
from .mark_six_result import ergodic_record

url = 'https://1680660.com/smallSix/findSmallSixHistory.do'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

color_dic = {
    '红': ['01', '02', '07', '08', '12', '13', '18', '19', '23', '24', '29', '30', '34', '35', '40', '45', '46'],
    '蓝': ['03', '04', '09', '10', '14', '15', '20', '25', '26', '31', '36', '37', '41', '42', '47', '48'],
    '绿': ['05', '06', '11', '16', '17', '21', '22', '27', '28', '32', '33', '38', '39', '43', '44', '49'],
}
chinese_zodiac_dic = {
    '狗': ['01', '13', '25', '37', '49'],
    '猪': ['12', '24', '36', '48'],
    '鼠': ['11', '23', '35', '47'],
    '牛': ['10', '22', '34', '46'],
    '虎': ['09', '21', '33', '45'],
    '兔': ['08', '20', '32', '44'],
    '龙': ['07', '19', '31', '43'],
    '蛇': ['06', '18', '30', '42'],
    '马': ['05', '17', '29', '41'],
    '羊': ['04', '16', '28', '40'],
    '猴': ['03', '15', '27', '39'],
    '鸡': ['02', '14', '26', '38'],
}
five_property_dic = {
    '金': ['04', '05', '18', '19', '26', '27', '34', '35', '48', '49'],
    '木': ['01', '08', '09', '16', '17', '30', '31', '38', '39', '46', '47'],
    '水': ['06', '07', '14', '15', '22', '23', '36', '37', '44', '45'],
    '火': ['02', '03', '10', '11', '24', '25', '32', '33', '40', '41'],
    '土': ['12', '13', '20', '21', '28', '29', '42', '43'],
}

ye_animals = ['鼠', '虎', '兔', '龙', '蛇', '猴']
jia_animals = ['牛', '马', '羊', '鸡', '狗', '猪']


def mark_six_result(pre_draw_code_list, pre_draw_date, issue):
    # 码数
    code_list = []
    # 色波
    color_list = []
    # 生肖
    chinese_zodiac_list = []
    # 五行
    five_property_list = []

    flat_code = ','.join(pre_draw_code_list[:-1])
    special_code = str(pre_draw_code_list[-1])
    print(flat_code, special_code, sep='\n')

    for code in pre_draw_code_list:
        if len(code) == 1:
            code = '0' + code
        code_list.append(code)

        for key, value in color_dic.items():
            if code in value:
                color_list.append(key)

        for key, value in chinese_zodiac_dic.items():
            if code in value:
                chinese_zodiac_list.append(key)

        for key, value in five_property_dic.items():
            if code in value:
                five_property_list.append(key)

    flat_code = ','.join(pre_draw_code_list[:-1])
    special_code = str(pre_draw_code_list[-1])

    answer_dic = {
        'code_list': code_list, 'color_list': color_list, 'chinese_zodiac_list': chinese_zodiac_list,
        'five_property_list': five_property_list,
    }
    print(answer_dic)
    # ergodic_record(issue, answer_dic)

    # open_price = OpenPrice()
    # open_price.issue = issue
    # open_price.flat_code = flat_code
    # open_price.special_code = special_code
    # open_price.animal = Option.ANIMAL_CHOICE[chinese_zodiac_list[-1]]
    # open_price.color = Option.WAVE_CHOICE[color_list[-1] + '波']
    # open_price.element = Option.ELEMENT_CHOICE[five_property_list[-1]]
    # open_price.save()

    # ergodic_record(issue)
    # next_issue_date = open_price.next_open
    # new_issue(issue, next_issue_date)

    # open_price.is_open = True
    # open_price.save()
    print('----------------------------------------------------------------------')


def new_issue(issue, next_issue_date):
    open_price = OpenPrice()
    open_price.issue = str(int(issue) + 1)
    open_price.open = next_issue_date
    open_price.closing = next_issue_date - datetime.timedelta(minutes=10)
    open_price.starting = datetime.datetime.now()

    next_open = next_issue_date + datetime.timedelta(days=1)
    while next_open.isoweekday() not in [2, 4, 6]:
        next_open = next_open + datetime.timedelta(days=1)
    open_price.next_open = next_open
    open_price.save()


class Command(BaseCommand):
    help = "mark six result"

    def handle(self, *args, **options):
        data = {
            'type': 1,
            'year': 2018,
        }

        response = requests.post(url, data=data, headers=headers)
        for body_list in response.json()['result']['data']['bodyList']:
            pre_draw_date = body_list['preDrawDate']
            issue = str(body_list['issue'])
            if OpenPrice.objects.filter(issue=str(issue), is_open=False).exists() is not True:
                pass
            else:
                print(pre_draw_date, ' ', issue + '期')
                # 拿到正码
                pre_draw_code = body_list['preDrawCode']
                pre_draw_code_list = pre_draw_code.split(',')

                mark_six_result(pre_draw_code_list, pre_draw_date, issue)
