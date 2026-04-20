from celery import shared_task


@shared_task
def cleanup_expired_tokens():
    """Remove expired blacklisted tokens from the database."""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    from django.utils import timezone
    deleted, _ = OutstandingToken.objects.filter(expires_at__lt=timezone.now()).delete()
    return f"Deleted {deleted} expired tokens."
