# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import requests
from marksix.models import OpenPrice, Number, Animals, Option
import datetime
from .mark_six_result import ergodic_record
from marksix.consumers import mark_six_result_code
from bs4 import BeautifulSoup

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
    '金': ['01', '06', '11', '16', '21', '26', '31', '36', '41', '46'],
    '木': ['02', '07', '12', '17', '22', '27', '32', '37', '42', '47'],
    '水': ['03', '08', '13', '18', '23', '28', '33', '38', '43', '48'],
    '火': ['04', '09', '14', '19', '24', '29', '34', '39', '44', '49'],
    '土': ['05', '10', '15', '20', '25', '30', '35', '40', '45'],
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

    special_code_head = code_list[-1][0] + '头'
    special_code_tail = code_list[-1][1] + '尾'

    special_code_head_id = str(Option.objects.get(option=special_code_head).id)
    special_code_tail_id = str(Option.objects.get(option=special_code_tail).id)

    special_color = color_list[-1] + '波'
    special_color_id = str(Option.objects.get(option=special_color).id)

    special_animal = chinese_zodiac_list[-1]
    special_animal_id = str(Option.objects.get(option=special_animal).id)

    special_elements = five_property_list[-1]
    special_elements_id = str(Option.objects.get(option=special_elements).id)

    twq_side_op = {}
    for option in ['特家肖', '特野肖', '特小', '特大', '特双', '特单', '总大', '总小', '总双', '总单']:
        twq_side_op.update({option: str(Option.objects.get(option=option).id)})

    animal_result_list = []
    for animal in chinese_zodiac_list:
        animal_result_list.append(str(Option.objects.get(option=animal).id))

    answer_dic = {
        'special_code': special_code, 'code_list': code_list, 'color_list': color_list,
        'chinese_zodiac_list': chinese_zodiac_list, 'five_property_list': five_property_list,
        'special_code_head_id': special_code_head_id, 'special_code_tail_id': special_code_tail_id,
        'special_color_id': special_color_id, 'special_animal_id': special_animal_id,
        'special_elements_id': special_elements_id, 'twq_side_op': twq_side_op,
        'animal_result_list': animal_result_list,
    }

    openprice = OpenPrice.objects.all().order_by('-id').first()
    if int(issue) != int(openprice.next_issue):
        raise CommandError('警告：mark_six期数不匹配，请及时处理')

    open_price = OpenPrice()
    open_price.issue = issue
    open_price.flat_code = flat_code
    open_price.special_code = special_code
    open_price.animal = Option.ANIMAL_CHOICE[chinese_zodiac_list[-1]]
    open_price.color = Option.WAVE_CHOICE[color_list[-1] + '波']
    open_price.element = Option.ELEMENT_CHOICE[five_property_list[-1]]

    open_price.closing = openprice.next_closing
    open_price.open = openprice.next_open

    next_issue_dic = new_issue(issue, openprice.next_open)
    open_price.next_issue = next_issue_dic['next_issue']
    open_price.starting = datetime.datetime.now()
    open_price.next_open = next_issue_dic['next_open']
    open_price.next_closing = next_issue_dic['next_closing']
    open_price.save()

    # 推送开奖结果
    mark_six_result_code(issue, next_issue_dic['next_issue'])

    # 处理投注记录
    print(answer_dic)
    ergodic_record(issue, answer_dic, openprice.id)

    open_price.is_open = True
    open_price.save()

    print('----------------------------------------------------------------------')


def new_issue(now_issue, now_open_date):
    now_open_ymd = now_open_date.strftime('%Y-%m-%d')
    now_open_hms = now_open_date.strftime('%H:%M:%S')

    six_url = 'https://www.lotto-8.com/listltohkbbk.asp'
    response = requests.get(url=six_url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    next_open_oth_ymd = ''
    for td_tag in soup.select('table[class="auto-style4"]')[0].find_all('tr')[1:5]:
        now_open_oth_ymd = td_tag.find_all('td')[0].text.replace('/', '-')
        if now_open_ymd == now_open_oth_ymd:
            next_open_oth_ymd = td_tag.find_all('td')[3].text.replace('/', '-')
            break

    if next_open_oth_ymd != '':
        print('next_open_oth_ymd  next_open_oth_ymd', next_open_oth_ymd)
        next_open_date = next_open_oth_ymd + ' ' + now_open_hms
        next_open_date = datetime.datetime.strptime(next_open_date, '%Y-%m-%d %H:%M:%S')
        next_closing = next_open_date - datetime.timedelta(minutes=15)
    else:
        next_open_date = now_open_date + datetime.timedelta(days=1)
        while next_open_date.isoweekday() not in [2, 4, 6]:
            next_open_date = next_open_date + datetime.timedelta(days=1)
        next_closing = next_open_date - datetime.timedelta(minutes=15)

    now_year = now_open_date.strftime('%Y')
    next_year = next_open_date.strftime('%Y')
    if int(next_year) > int(now_year):
        next_issue = 1
    else:
        next_issue = int(now_issue) + 1
    return {'next_issue': next_issue, 'next_open': next_open_date, 'next_closing': next_closing}


class Command(BaseCommand):
    help = "mark six result"

    def handle(self, *args, **options):
        now_time = datetime.datetime.now()
        print(' now is ', now_time)

        data = {
            'type': 1,
            'year': 2019,
        }
        open_price = OpenPrice.objects.order_by('-open').first()
        next_open = open_price.next_open
        if now_time > next_open:
            # if now_time < next_open + datetime.timedelta(hours=1) or now_time > next_open + datetime.timedelta(days=1):

            response = requests.post(url, data=data, headers=headers)
            open_price = OpenPrice.objects.order_by('-open').first()
            for body_list in response.json()['result']['data']['bodyList']:
                pre_draw_date = body_list['preDrawDate']
                issue = str(body_list['issue'])
                if issue == open_price.next_issue:
                    print(pre_draw_date, ' ', issue + '期')
                    # 拿到正码
                    pre_draw_code = body_list['preDrawCode']
                    pre_draw_code_list = pre_draw_code.split(',')

                    mark_six_result(pre_draw_code_list, pre_draw_date, issue)
        else:
            print('暂不需要处理')
        print('----------------------------------------------------------------------')
