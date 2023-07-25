from backend.exception import InvalidActivationCode, ItemNotFound
from backend.models import User
from backend.tasks import send_mail_task
from django.conf import settings
from django.urls import reverse
from rest_framework.authtoken.models import Token


def user_activate_mail(user):
    domain = settings.EMAIL_SITE_HOST
    token = Token.objects.get(user=user)
    url = reverse('activation', kwargs={'id': user.pk, 'token': token.key})
    subject = 'Confirm registration'
    message = f'Please, follow link below, to confirm register</br>{domain}{url}'
    to_email = [user.email]
    send_mail_task.delay(subject=subject, message=message, to_email=to_email)


def user_activate(user):
    user.is_active = True
    user.save()


def check_activation_link(id, token):
    try:
        user = User.objects.get(pk=id)
        created_token = Token.objects.get(user_id=user)
    except User.DoesNotExist as er:
        raise ItemNotFound(er)
    except Token.DoesNotExist as er:
        raise ItemNotFound(er)
    if created_token.key != token:
        raise InvalidActivationCode()

    user_activate(user)
    return {'Status': 'User activated'}
