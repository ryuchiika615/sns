import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Render上で設定する秘密の鍵
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-default-key")

# 公開時はFalse
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", ".onrender.com,localhost,127.0.0.1"
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "https://*.onrender.com"
).split(",")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "debug_toolbar",
    "sns",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "sns.middleware.LoginActivityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1", "localhost"]

ROOT_URLCONF = "study_app_new.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "study_app_new.wsgi.application"

# RenderのDB設定
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# 静的ファイルの設定
STATIC_URL = "/static/"  # ★ 先頭にスラッシュを追加して修正しました！
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}


# メディアファイル（画像）の設定
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "login"
SITE_ADMIN_USERNAME = os.environ.get("SITE_ADMIN_USERNAME", "りゅうのすけ")

# Redis キャッシュ設定
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# セッションはDB保存（Redisが無い環境でも動作）
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ページネーション
PAGINATION_COUNT = 10

# --- Jazzmin（管理画面）をカッコよく＆使いやすくする設定 ---
JAZZMIN_SETTINGS = {
    "site_title": "リュッター管理",
    "site_header": "リュッター管理画面",
    "site_brand": "⚡ リュッター管理",
    "welcome_sign": "ようこそ管理画面へ！神の力で操作してください。",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "site_url": "/",
    "search_model": ["auth.User", "sns.Post", "sns.Profile"],
    "user_avatar": None,
    "topmenu_links": [
        {
            "name": "🏠 リュッターを開く",
            "url": "/",
            "new_window": True,
            "icon": "fas fa-external-link-alt",
        },
        {"separator": True},
        {"app": "sns"},
    ],
    "usermenu_links": [
        {
            "name": "リュッターを開く",
            "url": "/",
            "new_window": True,
            "icon": "fas fa-rocket",
        },
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "sns"],
    "custom_links": {},
    "icons": {
        "auth.User": "fas fa-user-cog",
        "auth.Group": "fas fa-users-cog",
        "sns.Post": "fas fa-pen-square",
        "sns.Profile": "fas fa-id-card",
        "sns.GachaItem": "fas fa-dice-d6",
        "sns.Comment": "fas fa-comment-dots",
        "sns.Notification": "fas fa-bell",
        "sns.UserLoginSession": "fas fa-sign-in-alt",
    },
    "default_icon_parents": "fas fa-folder-open",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.User": "collapsible",
        "sns.Post": "vertical_tabs",
    },
    "language_chooser": False,
}
