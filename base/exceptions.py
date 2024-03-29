# -*- coding: UTF-8 -*-
import json
from django.http import HttpResponse
from rest_framework.views import exception_handler
import traceback

from .code import API_ERROR_MESSAGE
from .code_en import API_ERROR_MESSAGE_EN

from redis import Redis
from rq import Queue
from handle.consumers import send_alert_email
from django.conf import settings


class CCBaseException(Exception):
    """
    基础异常类
    """
    status_code = None
    error_message = None
    is_an_error_response = True
    context = {}

    def __init__(self, error_code='400', context=None):
        Exception.__init__(self)
        self.error_code = error_code
        self.context = context

    def to_dict(self, request):
        code = self.error_code
        message = API_ERROR_MESSAGE_EN[code] if request.GET.get('language') == 'en' else API_ERROR_MESSAGE[code]
        if self.context is not None and 'params' in self.context and '%s' in message:
            message = message % self.context['params']

        context = {
            'code': code,
            'message': message,
        }
        if self.context is not None:
            del self.context['params']
            context = {**context, **self.context}
        return HttpResponse(json.dumps(context), content_type='application/json')


class SystemParamException(CCBaseException):
    status_code = 403


class SignatureNotMatchException(CCBaseException):
    status_code = 403


class NotLoginException(CCBaseException):
    status_code = 403


class ResultNotFoundException(CCBaseException):
    status_code = 404


class ParamErrorException(CCBaseException):
    status_code = 404


class UserLoginException(CCBaseException):
    status_code = 404


def wc_exception_handler(exception, context):
    response = exception_handler(exception, context)
    print('exception = ', exception, ' type is ', type(exception))
    if settings.IS_ENABLE_EMAIL_ALERT:
        if type(exception) not in [SystemParamException, SignatureNotMatchException, NotLoginException, ResultNotFoundException, ParamErrorException, UserLoginException]:
            # 非预定义抛出的异常发送邮件报警
            print('call here')
            redis_conn = Redis()
            q = Queue(connection=redis_conn)
            q.enqueue(send_alert_email, exception, traceback.format_exc(), context['request'].get_full_path())
    print('context = ', context)
    traceback.print_exc()

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response
