"""
volunteer_system 项目的 Django 全局配置文件。
"""

from pathlib import Path

# 项目根目录路径。
BASE_DIR = Path(__file__).resolve().parent.parent


# 开发环境配置（不适用于生产环境）。

# 安全提示：生产环境必须更换并妥善保管密钥。
SECRET_KEY = "django-insecure-h_ut2jy9w^re9*#3*ryi5j(m=wz&!#e0762p&67wki@m+@2@8k"

# 安全提示：生产环境必须关闭调试模式。
DEBUG = True

# 开发环境放开主机校验，生产环境请改为明确域名白名单。
ALLOWED_HOSTS = ["*"] if DEBUG else []


# 应用注册

INSTALLED_APPS = [
    # Django 内置应用。
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 三方扩展：REST API、JWT、跨域。
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # 本项目业务应用。
    "api",
]

MIDDLEWARE = [
    # 安全中间件应放在靠前位置。
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 跨域中间件需位于 CommonMiddleware 之前。
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "volunteer_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "volunteer_system.wsgi.application"


# 数据库配置

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # 当前使用 SQLite 便于本地快速启动。
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# 密码强度校验

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# 国际化配置

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True


# 静态资源配置（样式、脚本、图片等）

STATIC_URL = "static/"

# 默认主键类型
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 自定义用户模型
AUTH_USER_MODEL = "api.User"

# 跨域配置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# 开发环境允许全部来源，便于本地联调。
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# 接口框架配置
REST_FRAMEWORK = {
    # 全局使用 JWT 认证。
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # 全局默认需要登录。
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# 令牌认证配置
from datetime import timedelta
SIMPLE_JWT = {
    # 访问令牌较短、刷新令牌较长，平衡安全与体验。
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# 媒体文件配置（上传文件）
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
