# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import RecordStockPk, Issues, OptionStockPk, Periods
from .stock_result_new import GuessPKRecording
import datetime
from django.db.models import Q


class Command(BaseCommand):
    help = "处理投注表"

    def handle(self, *args, **options):
        issues = Issues.objects.filter(~Q(size_pk_result=''), result_confirm__gte=3, is_open=False).order_by('id')[:10]
        if len(issues) > 0:
            option_obj_dic = {}
            for option in OptionStockPk.objects.all():
                option_obj_dic.update({
                    option.id: {
                        'title': option.title,
                    }
                })
            i = 0
            for issue in issues:
                record_stock_pk = GuessPKRecording()
                i += 1
                print('正在处理第 ', i, ' 期,issues_id=', issue.id, '   ', '期数是: ', issue.issue, '    ',
                      datetime.datetime.now())
                records = RecordStockPk.objects.filter(issue_id=issue.id, status=str(RecordStockPk.AWAIT))
                if len(records) > 0:
                    for record_pk in records:
                        record_stock_pk.pk_size(record_pk, option_obj_dic, issue)
                    record_stock_pk.insert_info(records, 5)
                    issue.is_open = True
                    issue.save()
        else:
            print('当前无需要处理的数据')
