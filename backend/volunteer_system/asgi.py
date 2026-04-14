"""
volunteer_system 项目的 ASGI 配置。

该模块对外暴露名为 ``application`` 的 ASGI 可调用对象。
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "volunteer_system.settings")

application = get_asgi_application()
