# shop/admin.py
from django.contrib import admin
from django.db.models import Sum

from .models import (
    SiteSetting,
    StaticPage,
    ContactMessage,
    Category,
    Brand,
    Product,
    ProductImage,
    ProductAttribute,
    ProductAttributeValue,
    CarModel,
    ProductCompatibility,
    UserCar,
    Order,
    OrderItem,
    Payment,
    Review,
    AboutPage,
    AboutFeature,
    AboutStat,
    TeamMember
)


# -----------------------------
# Helpers / Actions
# -----------------------------
@admin.action(description="Сделать активными")
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Сделать неактивными")
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


# -----------------------------
# Site settings / Content
# -----------------------------
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """
    Обычно нужна одна запись. Админка не запрещает создать несколько,
    но это легко контролировать на уровне проекта (или через сигнал).
    """
    list_display = ("id", "site_name", "phone", "email")
    # удобнее редактировать на одной странице
    fieldsets = (
        ("Общее", {"fields": ("site_name",)}),
        ("Контакты", {"fields": ("phone", "email", "address", "work_hours")}),
        ("Карта", {"fields": ("map_embed", "map_url")}),
        ("Соцсети", {"fields": ("telegram_url", "whatsapp_url", "vk_url")}),
    )


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "updated_at"
    ordering = ("-updated_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "email", "phone", "subject", "status")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "phone", "subject", "message", "admin_note")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Catalog
# -----------------------------
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "sort_order")
    actions = (make_active, make_inactive)


admin.site.register(Category, CategoryAdmin)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)
    actions = (make_active, make_inactive)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt", "sort_order", "is_main")
    ordering = ("sort_order", "id")


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ("attribute", "value", "sort_order")
    ordering = ("sort_order", "id")
    autocomplete_fields = ("attribute",)


class ProductCompatibilityInline(admin.TabularInline):
    model = ProductCompatibility
    extra = 1
    fields = ("car_model", "notes")
    autocomplete_fields = ("car_model",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "brand",
        "price",
        "old_price",
        "stock_qty",
        "is_active",
        "is_featured",
        "updated_at",
    )
    list_filter = ("is_active", "is_featured", "category", "brand")
    search_fields = ("name", "slug", "sku", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "old_price", "stock_qty", "is_active", "is_featured")
    actions = (make_active, make_inactive)
    autocomplete_fields = ("category", "brand")
    inlines = (ProductImageInline, ProductAttributeValueInline, ProductCompatibilityInline)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "sort_order", "is_main", "created_at")
    list_filter = ("is_main",)
    search_fields = ("product__name", "alt")
    autocomplete_fields = ("product",)
    list_editable = ("sort_order", "is_main")
    ordering = ("product", "sort_order", "id")


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("product", "attribute", "value", "sort_order")
    list_filter = ("attribute",)
    search_fields = ("product__name", "attribute__name", "value")
    autocomplete_fields = ("product", "attribute")
    list_editable = ("sort_order",)
    ordering = ("product", "sort_order", "id")


# -----------------------------
# Cars & Compatibility
# -----------------------------
@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "sort_order")
    actions = (make_active, make_inactive)
    ordering = ("sort_order", "name")


@admin.register(ProductCompatibility)
class ProductCompatibilityAdmin(admin.ModelAdmin):
    list_display = ("product", "car_model", "notes", "created_at")
    search_fields = ("product__name", "product__sku", "car_model__name", "notes")
    autocomplete_fields = ("product", "car_model")
    list_filter = ("car_model",)


@admin.register(UserCar)
class UserCarAdmin(admin.ModelAdmin):
    list_display = ("user", "car_model", "year", "vin", "is_primary", "created_at")
    list_filter = ("is_primary", "car_model")
    search_fields = ("user__username", "user__email", "vin", "notes", "car_model__name")
    autocomplete_fields = ("user", "car_model")
    list_editable = ("is_primary",)
    ordering = ("-is_primary", "-created_at")


# -----------------------------
# Orders / Payments
# -----------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "name_snapshot", "price_snapshot", "qty", "line_total", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("product",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("method", "status", "amount", "provider_payment_id", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "user", "full_name", "phone", "total", "items_count")
    list_filter = ("status", "created_at")
    search_fields = ("id", "full_name", "phone", "email", "comment", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = (OrderItemInline, PaymentInline)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def items_count(self, obj: Order) -> int:
        # быстрый подсчёт по related_name items
        return obj.items.aggregate(s=Sum("qty")).get("s") or 0

    items_count.short_description = "Кол-во товаров"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "name_snapshot", "qty", "price_snapshot", "line_total", "created_at")
    search_fields = ("order__id", "product__name", "product__sku", "name_snapshot")
    autocomplete_fields = ("order", "product")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "method", "status", "amount", "created_at")
    list_filter = ("method", "status", "created_at")
    search_fields = ("order__id", "provider_payment_id")
    autocomplete_fields = ("order",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# -----------------------------
# Reviews
# -----------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "rating", "is_published", "user", "name", "created_at")
    list_filter = ("is_published", "rating", "created_at")
    search_fields = ("product__name", "product__sku", "text", "user__username", "user__email", "name")
    autocomplete_fields = ("product", "user")
    list_editable = ("is_published",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


class AboutFeatureInline(admin.TabularInline):
    model = AboutFeature
    extra = 1

class AboutStatInline(admin.TabularInline):
    model = AboutStat
    extra = 1

class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1

@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    inlines = [AboutFeatureInline, AboutStatInline, TeamMemberInline]
    list_display = ("title", "is_active")
    list_filter = ("is_active",)

# -----------------------------
# Admin site cosmetics
# -----------------------------
admin.site.site_header = "ZeekrParts — Администрирование"
admin.site.site_title = "ZeekrParts Admin"
admin.site.index_title = "Управление сайтом"
