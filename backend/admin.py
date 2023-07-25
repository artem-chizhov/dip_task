from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
from backend.models import Category, Contact, Order, OrderItem, Parameter, Product, ProductInfo, ProductParameter, Shop, User


class ProductParameterAdmin(admin.StackedInline):
    model = ProductParameter


class ProductInfoAdmin(admin.TabularInline):
    model = ProductInfo
    show_change_link = True


class ProductInfosAdmin(admin.ModelAdmin):
    inlines = [ProductParameterAdmin]


class ProductAdmin(admin.ModelAdmin):
    pass


class CategoryAdmin(admin.TabularInline):
    model = Category.shops.through


class ShopAdmin(admin.ModelAdmin):
    inlines = [CategoryAdmin, ProductInfoAdmin]


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemAdmin]


class OrderUserAdmin(admin.TabularInline):
    model = Order
    extra = 1
    show_change_link = True


class ContactAdmin(admin.StackedInline):
    model = Contact
    extra = 1


class TokenAdmin(admin.TabularInline):
    model = Token
    readonly_fields = ('key',)
    extra = 0
    can_delete = False


class MyUserAdmin(UserAdmin):
    list_display_links = ('email',)
    inlines = [TokenAdmin, ContactAdmin, OrderUserAdmin]
    list_display = ('email', 'type', 'first_name', 'last_name', 'is_staff')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'father_name', 'company', 'position', 'email')}),
        (
            ('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


class ParameterAdmin(admin.ModelAdmin):
    pass


# Register your models here.
admin.site.register(User, MyUserAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductInfo, ProductInfosAdmin)
admin.site.register(Parameter, ParameterAdmin)
