import os
from django.core.wsgi import get_wsgi_application

# プロジェクト名に合わせて設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_app_new.settings')

application = get_wsgi_application()