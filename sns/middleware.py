from datetime import timedelta

from django.utils import timezone

from .models import UserLoginSession


class LoginActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return response

        session_id = request.session.get('login_session_id')
        login_session = None
        if session_id:
            login_session = UserLoginSession.objects.filter(
                id=session_id,
                user=user,
                logout_at__isnull=True
            ).first()

        if not login_session:
            login_session = UserLoginSession.objects.create(
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
            )
            request.session['login_session_id'] = login_session.id
        elif timezone.now() - login_session.last_seen_at > timedelta(minutes=1):
            login_session.save(update_fields=['last_seen_at'])

        return response

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
