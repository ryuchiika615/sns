from django.contrib import admin
from django.urls import path, include # includeを忘れずに！

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sns.urls')), # SNSアプリのURL設定を読み込む
]