from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from celery import shared_task


@shared_task()
def send_mail_task(subject, message, to_email, html_message=None):
    from_email = settings.EMAIL_FROM
    send_mail(subject, message, from_email, to_email, fail_silently=False, html_message=html_message)


@shared_task()
def send_mass_mail_task(subject, message, to_email):
    from_email = settings.EMAIL_FROM
    send_mass_mail([(subject, message, from_email, to_email)], fail_silently=False)
