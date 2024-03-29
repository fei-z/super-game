# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.app import BaseView
from utils.cache import get_cache, set_cache
from redis import Redis
from rq import Queue
from recharge.consumers.btc_usdt_monitor import consumer_bitcoin_usdt_monitor
from base.eth import Wallet


class Command(BaseCommand, BaseView):
    help = "BTC、USDT充值监控"
    cacheKey = 'key_btc_usdt_block_height'

    def add_arguments(self, parser):
        parser.add_argument('--block_height', type=int, help='块高度')
        parser.add_argument('--only_one_block', type=int, help='是否只获取一个块高度')

    def set_queue(self, block_height):
        """
        写入消息队列
        :param block_height:    块高度
        :return:
        """
        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        q.enqueue(consumer_bitcoin_usdt_monitor, block_height)

        set_cache(self.cacheKey, block_height)

        self.stdout.write(self.style.SUCCESS('监控高度=' + str(block_height) + '的BTC&USDT充值数据'))

    @staticmethod
    def get_block_height():
        """
        获取区块链上最大节点高度
        :return:
        """
        try:
            wallet = Wallet()
            response = wallet.get(url='https://chain.api.btc.com/v3/block/latest')
            block_height = int(response['data']['height'])
        except Exception:
            raise CommandError('获取区块链最新节点高度失败')

        return block_height

    def handle(self, *args, **options):
        if options['block_height']:
            block_height = options['block_height']
        else:
            block_height = self.get_block_height()

        # 只监控某个块高度数据
        if options['only_one_block']:
            self.set_queue(block_height)
            raise CommandError('Done')

        # 获取缓存中的块高度值，若缓存未设置，则首次设置的值为当前区块链块高
        cache_block_height = get_cache(self.cacheKey)
        if cache_block_height is None:
            cache_block_height = block_height
            set_cache(self.cacheKey, block_height)

        # 当缓存中的块高度值大于参数传过来的高度值，则重新写入缓存中的块高度值为参数指定的高度值
        # 如缓存中块高为123，参数传100，区块链上高度为125，则会监控100~125间的所有块数据
        if int(cache_block_height) > int(block_height):
            set_cache(self.cacheKey, block_height)

        cache_block_height = int(cache_block_height)
        for block in range(cache_block_height, block_height + 1):
            # 当前获取到的块高若与缓存中的块高相同，则不再获取
            if block == cache_block_height:
                continue
            self.set_queue(block)

        self.stdout.write(self.style.SUCCESS('执行完成'))
