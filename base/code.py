# -*- coding: UTF-8 -*-
"""
接口错误码
"""
API_0_SUCCESS = 0
API_403_ACCESS_DENY = 403
API_404_NOT_FOUND = 404
API_405_WAGER_PARAMETER = 405
API_10101_SYSTEM_PARAM_REQUIRE = 10101
API_10102_SIGNATURE_ERROR = 10102
API_10103_REQUEST_EXPIRED = 10103
API_10104_PARAMETER_EXPIRED = 10104
API_20101_TELEPHONE_ERROR = 20101
API_20401_TELEPHONE_ERROR = 20401
API_20402_INVALID_SMS_CODE = 20402
API_20403_SMS_CODE_EXPIRE = 20403
API_20601_PASS_CODE_ERROR = 20601
API_20602_PASS_CODE_LEN_ERROR = 20602
API_20701_USED_PASS_CODE_ = 20701
API_20702_USED_PASS_CODE_ERROR = 20702
API_20801_PASS_CODE_ERROR = 20801
API_20802_PASS_CODE_LEN_ERROR = 20802
API_30201_ALREADY_SING = 30201
API_40101_SMS_CODE_ID_INVALID = 40101
API_40102_SMS_CODE_EXPIRED = 20105
API_40103_SMS_CODE_INVALID = 20104
API_40104_SMS_PERIOD_INVALID = 20102
API_50101_QUIZ_OPTION_ID_INVALID = 50101
API_50102_WAGER_INVALID = 50102
API_50103_WAGER_LIMITED = 50103
API_50104_USER_COIN_NOT_METH = 50104
API_50105_USER_COIN_NOT_GGTC = 50105
API_50106_PARAMETER_EXPIRED = 50106
API_50107_USER_BET_TYPE_ID_INVALID = 50107


API_ERROR_MESSAGE = {
    API_0_SUCCESS: '请求成功',
    API_403_ACCESS_DENY: '无访问权限',
    API_404_NOT_FOUND: '无数据',
    API_405_WAGER_PARAMETER: '无效参数',
    API_10101_SYSTEM_PARAM_REQUIRE: '系统级参数错误',
    API_10102_SIGNATURE_ERROR: '签名值错误',
    API_10103_REQUEST_EXPIRED: '请求已失效',
    API_10104_PARAMETER_EXPIRED: '参数错误',
    API_20101_TELEPHONE_ERROR: '手机号码格式错误',
    API_20401_TELEPHONE_ERROR: '请输入手机号',
    API_20402_INVALID_SMS_CODE: '短信验证码错误',
    API_20403_SMS_CODE_EXPIRE: '验证码已过期',
    API_20601_PASS_CODE_ERROR:'请输入密保',
    API_20602_PASS_CODE_LEN_ERROR:'请输入6位以上密保',
    API_20701_USED_PASS_CODE_:'请输入原密保',
    API_20702_USED_PASS_CODE_ERROR:'原密保错误',
    API_20801_PASS_CODE_ERROR:'请客输入新密保',
    API_20802_PASS_CODE_LEN_ERROR:'请输入6位以上新密保',
    API_30201_ALREADY_SING: '您已签到',
    API_40101_SMS_CODE_ID_INVALID: '无效的code_id',
    API_40102_SMS_CODE_EXPIRED: '验证码已过期',
    API_40103_SMS_CODE_INVALID: '验证码错误',
    API_40104_SMS_PERIOD_INVALID: '短信间隔期未到',
    API_50101_QUIZ_OPTION_ID_INVALID: '无效的投注选项',
    API_50102_WAGER_INVALID: '无效的赌注',
    API_50103_WAGER_LIMITED: '单次下注超过上限',
    API_50104_USER_COIN_NOT_METH: 'METH币不足',
    API_50105_USER_COIN_NOT_GGTC: 'GGTC币不足',
    API_50106_PARAMETER_EXPIRED: '参数错误',
    API_50107_USER_BET_TYPE_ID_INVALID: '无效竞猜',
}


