from backend.serialyzers import OrderSerializer, ValidationError
from backend.exception import ItemNotFound
from backend.models import Contact, Order, OrderItem, ProductInfo, Shop, User
from backend.tasks import send_mail_task, send_mass_mail_task
from django.conf import settings
from django.urls import reverse
from django.template import Context
from django.template.loader import get_template


def inform_shops_on_new_order(order):
    """Отправка информации о новом заказе на почту менеджерам магазинов"""
    items = [item['product_info'] for item in OrderItem.objects.filter(order=order.pk).values('product_info')]
    shops = [product['shop'] for product in ProductInfo.objects.filter(pk__in=items).values('shop')]
    users = [shop['user__email'] for shop in Shop.objects.filter(id__in=shops).values('user__email')]
    domain = settings.EMAIL_SITE_HOST
    url = reverse('orders_shop-detail', kwargs={'pk': order.pk})
    subject = 'Order created'
    message = f'Created new order for You shop</br>{domain}{url}'
    to_email = users
    send_mass_mail_task.delay(subject, message, to_email)


def inform_user_on_new_order(order):
    """Отправка Информации о созданном заказе на почту покупателю"""
    user = User.objects.get(pk=order.user.id)
    domain = settings.EMAIL_SITE_HOST
    url = reverse('orders-detail', kwargs={'pk': order.pk})
    subject = 'Order changed'
    message = f'Order status changed</br>{domain}{url}'
    to_email = [user.email]
    template = get_template("template_new_order.html")
    context = {
        'order': OrderSerializer(order).data
        }
    html_message = template.render(context)
    send_mail_task.delay(subject=subject, message=message, to_email=to_email, html_message=html_message)


def change_quantity(items):
    """Списание количества заказанных позиций с полки магазина"""
    save_list = [item.save() for item in items]
    OrderItem.objects.bulk_update(save_list, item.product_info.quantity)


def verify_items(basket):
    """Сбор ошибок по позициям в заказе"""
    errors, items = {}, {}
    ordered_items = OrderItem.objects.filter(order=basket)
    for item in ordered_items:
        try:
            check_quantity = item.quantity <= item.product_info.quantity
            if check_quantity:
                item.product_info.quantity -= item.quantity
                items[item.product_info.pk] = item.product_info.quantity
                continue
            else:
                errors[item.product_info.pk] = 'incorrect quantity'
        except OrderItem.DoesNotExist:
            errors['0']('Item Not Found')
    return errors, items


def check_basket(user):
    """Проверка заказа со статусом basket"""
    try:
        basket = Order.objects.get(user=user, state='basket')
    except Order.DoesNotExist:
        raise ItemNotFound('Basket is empty')
    return basket


def verify_contact(basket, contact):
    """Проверка Контакта в Заказе"""
    if contact:
        try:
            return Contact.objects.get(pk=contact)
        except Contact.DoesNotExist:
            raise ValidationError('Wrong contact')
    elif basket.contact:
        return basket.contact
    else:
        raise ValidationError('Contact must be set for create order')


def verify_order(user, contact):
    """Главная функция проверки заказа и изменения статуса заказа"""
    basket = check_basket(user)
    errors, items = verify_items(basket)
    new_contact = verify_contact(basket, contact)
    if not errors and contact:
        for product, quantity in items.items():
            instance = ProductInfo.objects.get(pk=product)
            instance.quantity = quantity
            instance.save()
        basket.state = 'new'
        basket.contact = new_contact
        basket.save(update_fields=['state', 'contact'])
        inform_shops_on_new_order(basket)
        inform_user_on_new_order(basket)
        return {'Status: Order created'}
    else:
        return {'Wrong data in order': errors}
