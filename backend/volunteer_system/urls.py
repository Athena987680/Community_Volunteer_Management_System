"""
volunteer_system 项目根路由配置。
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django 默认管理后台入口。
    path("admin/", admin.site.urls),
    # 业务 API 统一挂载到 /api 前缀下。
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    # 开发环境下由 Django 直接托管媒体文件，便于本地调试上传图片。
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
