from backend import serialyzers
from backend.logic.order import verify_order
from backend.logic.user import check_activation_link
from backend.logic.utils import file_shop_load
from backend.models import (Category, Contact, Order, OrderItem, Product,
                            ProductInfo, Shop, User)
from backend.permissions import IsOrderUserOwner, IsShop
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action


# Create your views here.
class UserActivateView(APIView):
    """Активация пользователя"""
    queryset = User.objects.all()
    permission_classes = [~IsAuthenticated]

    def patch(self, id, token):
        resp = check_activation_link(id, token)
        return Response(resp)


class UserRegisterView(CreateAPIView):
    """Регистрация пользователя"""
    queryset = User.objects.all()
    permission_classes = [~IsAuthenticated]
    serializer_class = serialyzers.UserSerialyzer


class UserView(RetrieveUpdateAPIView):
    """Данные авторизованного пользователя"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.UserSerialyzer

    def get_object(self):
        return self.request.user


class CategoryView(ReadOnlyModelViewSet):
    """Информация о категориях"""
    queryset = Category.objects.prefetch_related('products')
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.CategorySerialyzer


class ListProductView(ReadOnlyModelViewSet):
    """информация по товарным наименованиям"""
    queryset = Product.objects.prefetch_related('product_infos')
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']
    ...


class ProductView(ReadOnlyModelViewSet):
    """Информация по товарам магазинов"""
    queryset = ProductInfo.objects.prefetch_related('product_parameters__parameter')
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.ProductInfoSerializer


class BuyerOrderView(ReadOnlyModelViewSet):
    """Список и информация о заказах авторизованного пользователя"""
    queryset = Order.objects.prefetch_related('ordered_items__product_info', 'contact')
    permission_classes = [IsAuthenticated & IsOrderUserOwner]
    serializer_class = serialyzers.OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user).exclude(state='basket')


class BasketView(ModelViewSet):
    """Информация по списку позиций в заказе пользователя со статусом basket"""
    queryset = OrderItem.objects.prefetch_related('product_info')
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.OrderItemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        basket, _ = Order.objects.get_or_create(user=self.request.user, state='basket')
        return queryset.filter(order=basket)

    def perform_create(self, serializer):
        basket, _ = Order.objects.get_or_create(user=self.request.user, state='basket')
        return serializer.save(order=basket)


class OrderConfirmView(APIView):
    """Подтверждение заказа пользователем"""
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated & IsOrderUserOwner]

    def put(self, request):
        resp = verify_order(self.request.user, request.data.get('contact'))
        return Response(resp)


class ContactView(ModelViewSet):
    """Информация по Контактам авторизованного пользователя"""
    queryset = Contact.objects.all()
    permission_classes = [IsAuthenticated & IsOrderUserOwner]
    serializer_class = serialyzers.ContactSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class ShopView(ModelViewSet):
    """Информация по магазинам"""
    queryset = Shop.objects.prefetch_related('product_infos', 'categories')
    permission_classes = [IsAuthenticated]
    serializer_class = serialyzers.ShopSerializer

    def get_permissions(self):
        if self.action in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & IsShop]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def upload(self, request, pk=None):
        shop = Shop.objects.get(pk=pk)
        file_shop_load(shop.filename, request.user)
        return Response('Data uploaded')


class OrderShopView(ModelViewSet):
    """Отображение для магазина списка заказанных позиций с сортировкой по заказам пользователя"""
    queryset = Order.objects.all()
    permission_classes = [IsShop]
    serializer_class = serialyzers.OrderSerializer

    def get_queryset(self):
        shops = Shop.objects.filter(user=self.request.user)
        queryset = Order.objects.filter(ordered_items__product_info__shop__in=shops).prefetch_related(
            Prefetch('ordered_items',
                     queryset=OrderItem.objects.filter(product_info__shop__in=shops).prefetch_related('product_info')
                     )
            )
        return queryset
