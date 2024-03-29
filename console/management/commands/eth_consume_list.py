# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time as format_time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *
from time import time
import time as format_time
import math
import json
import os
from django.conf import settings
#from django_redis import get_redis_connection
from decimal import Decimal
from redis import Redis
from base.app import BaseView
from users.models import UserRecharge, Coin, UserCoin, CoinDetail,User


def dealDbData(dict):
    #test
    #dict['type'] = 'INT'
    #print(dict)
    info = Coin.objects.filter(name=dict['type'])
    if not info :
        print('type_not allow,type:',dict['type'])
        return 0

    coin_id = info[0].id
    txid = dict['hash']
    addr = dict['to']
    #test
    #addr = '0xbc188Cc44428b38e115a2C693C9D0a4fD0BDCc71'
    value = dict['value']
    t_time = dict['t_time']
    usercoin_info = UserCoin.objects.filter(address=addr,coin_id=coin_id)
    if not usercoin_info:
        return 0

    user_id = usercoin_info[0].user_id

    #users_userrecharge 用户充值记录
    charge_info = UserRecharge.objects.filter(address=addr,txid=txid)
    if charge_info:
        print('addr___',charge_info[0].address)

    time_local = format_time.localtime(t_time)
    time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)

    if not charge_info:
        #充值记录
        recharge_obj = UserRecharge()
        recharge_obj.address = addr
        recharge_obj.coin_id = coin_id
        recharge_obj.txid = txid
        recharge_obj.user_id = user_id
        recharge_obj.amount = value
        recharge_obj.confirmations = 0
        recharge_obj.trade_at = time_dt
        recharge_obj.save()

        #刷新用户余额表
        usercoin_info[0].balance += Decimal(value)
        usercoin_info[0].save()

        #用户余额变更记录
        coin_detail = CoinDetail()
        coin_detail.user_id = user_id
        coin_detail.coin_name = dict['type']
        coin_detail.amount = value
        coin_detail.rest = usercoin_info[0].balance
        coin_detail.sources = CoinDetail.RECHARGE
        coin_detail.save()
        return True

    return False


class Command(BaseCommand,BaseView):
    help = "消费ETH_blocknum获取取交易数据"
    listKey = 'pre_eth_block_list'
    #base_url = "http://127.0.0.1:3001/api/v1/chain/blocknum/"

    # def add_arguments(self, parser):
    #     parser.add_argument('coin', type=str)

    @transaction.atomic()
    def handle(self, *args, **options):
        #coin_name = options['coin'].upper()
        eth_wallet = Wallet()
        #raise CommandError('name' + '无效')
        start_time = time()

        redis_obj = Redis()

        block_num = redis_obj.rpop(self.listKey)
        #print('popValue = ', type(popValue))
        block_num = block_num.decode('utf-8')
        print(block_num)
        if block_num == 'None':
            self.stdout.write(self.style.SUCCESS('队列暂时无数据'))
            return


        #根据block_num 获取交易数据
        # test curl http://127.0.0.1:3001/api/v1/chain/blocknum/7
        #url = self.base_url + str(block_num)j
        #h_data = {}
        #res = requests.get(url=url, headers=h_data)
        #json_obj = json.loads(res.text)
        json_obj = eth_wallet.get(url='/v1/chain/blocknum/' + str(block_num))
        print(json_obj)
        if json_obj['code'] != 0:
            self.stdout.write(self.style.SUCCESS('根据block_num获取数据失败'))
            return

        list = json_obj['data']['data']
        print(list)
        tmp_num = 0
        start_time1 = time()
        for i, val in enumerate(list):
            tmp_dict = val
            tmp_dict['t_time'] = json_obj['data']['t_time']
            tmp_dict['type'] = val['type'].upper()

            #根据交易信息处理db数据
            ret = dealDbData(tmp_dict)
            if ret == True:
                tmp_num+= 1
            """
            sql = 'SELECT user_id,count(*) as cnt from users_loginrecord GROUP BY user_id HAVING cnt > 100 ORDER BY cnt desc'
            aaaa = self.get_all_by_sql(sql)
            #address
                raise CommandError('无地址信息')
            """
        stop_time1 = time()
        cost_time1 = str(round(stop_time1 - start_time1)) + '秒'
        self.stdout.write(self.style.SUCCESS('db处理完成。耗时：' + cost_time1))

        self.stdout.write(self.style.SUCCESS('获取到' + str(tmp_num) + '条交易信息'))

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))



