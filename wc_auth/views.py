# -*- coding: UTF-8 -*-
import rest_framework_filters as filters
from base.backend import CreateAPIView, FormatListAPIView, FormatRetrieveAPIView

from .serializers import InfoSerialize, RoleListSerialize
from .models import Role, Admin


class LoginView(CreateAPIView):
    """
    管理员登录
    """
    serializer_class = InfoSerialize

    def post(self, request, *args, **kwargs):
        return self.response({
            'code': 0
        })


class RoleFilter(filters.FilterSet):
    """
    角色列表筛选
    """
    class Meta:
        model = Role
        fields = {
            "name": ['contains']
        }


class RoleListView(FormatListAPIView):
    """
    管理员角色列表
    """
    serializer_class = RoleListSerialize
    filter_class = RoleFilter
    queryset = Role.objects.all()


class InfoView(FormatRetrieveAPIView):
    """
    管理员信息
    """
    serializer_class = InfoSerialize
    queryset = Admin.objects.all()

    def get(self, request, *args, **kwargs):
        return self.response({
            "name": "Serati Ma",
            "avatar": "https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png",
            "userid": "00000001",
            "notifyCount": 12,
        })
