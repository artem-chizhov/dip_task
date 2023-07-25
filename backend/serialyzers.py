from backend.models import (Category, Contact, Order, OrderItem, Parameter,
                            Product, ProductInfo, ProductParameter, Shop, User)
from django.db.utils import IntegrityError
from rest_framework.serializers import (CharField, CurrentUserDefault,
                                        HiddenField, IntegerField,
                                        ModelSerializer, SlugRelatedField,
                                        ValidationError)


class UserSerialyzer(ModelSerializer):
    password = CharField(required=True, write_only=True, label='Пароль')
    password2 = CharField(required=True, write_only=True, label='Проверка пароля')

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'password2', 'type', 'first_name', 'last_name', 'father_name', 'company', 'position', 'auth_token']
        read_only_fields = ['auth_token']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if attrs.get('password') and attrs.get('password2'):
            if attrs['password'] != attrs['password2']:
                raise ValidationError('Пароли не совпадают')
            attrs.pop('password2')
        return super().validate(attrs)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.set_password(validated_data.get('password'))
        instance.save()
        return instance


class ParameterSerializer(ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['name']


class ProductParameterSerialyzer(ModelSerializer):
    parameter = SlugRelatedField('name', read_only=True)

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']

    def to_internal_value(self, data):
        ret = []
        for key, val in data.items():
            ret.append({
                'parameter': key,
                'value': val,
                })
        return ret


class ProductInfoSerializer(ModelSerializer):
    product_parameters = ProductParameterSerialyzer(many=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'external_id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters']


class ProductSerializer(ModelSerializer):

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'product_infos']


class CategorySerialyzer(ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name', 'products']


class ShopSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Shop
        fields = ['id', 'name', 'user', 'state', 'categories', 'product_infos', 'filename', 'url']
        read_only_fields = ['user', 'categories', 'product_infos']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise ValidationError('Only one Shop per User')


class ContactSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Contact
        fields = '__all__'


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'quantity', 'sum']

    def get_sum(self, obj):
        return obj.sum

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise ValidationError('Item already in basket')


class OrderSerializer(ModelSerializer):
    ordered_items = OrderItemSerializer(many=True, read_only=True)
    contact = ContactSerializer(read_only=True)
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['id', 'user', 'dt', 'state', 'contact', 'total', 'ordered_items']
        read_only_fields = ['state']

    def get_total(self, obj):
        return obj.total

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise ValidationError('Basket exists')


class ProductInfoLoadSerializer(ModelSerializer):
    id = IntegerField(source='external_id')
    parameters = ProductParameterSerialyzer(source='product_parameters')

    class Meta:
        model = ProductInfo
        fields = ['id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'parameters']


class ShopLoadSerializer(ModelSerializer):
    shop = CharField(source='name')
    goods = ProductInfoLoadSerializer(many=True, source='product_infos')
    categories = CategorySerialyzer(many=True)

    class Meta:
        model = Shop
        fields = ['shop', 'user', 'state', 'categories', 'goods', 'filename', 'url']
