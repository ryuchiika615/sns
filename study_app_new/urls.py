from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sns.urls')),
]

# 画像ファイルを表示するための魔法の設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 本番環境（Render）用
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)