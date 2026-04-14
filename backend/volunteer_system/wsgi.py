"""
volunteer_system 项目的 WSGI 配置。

该模块对外暴露名为 ``application`` 的 WSGI 可调用对象。
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "volunteer_system.settings")

application = get_wsgi_application()
