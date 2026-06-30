# shop/models.py
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify


# -----------------------------
# Utils
# -----------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# -----------------------------
# Content / Settings
# -----------------------------
class SiteSetting(models.Model):
    """
    Одна запись на сайт (контакты, соцсети, карта и т.п.)
    """
    site_name = models.CharField(max_length=120, default="ZeekrParts")

    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    work_hours = models.CharField(max_length=255, blank=True)

    # Можно хранить iframe (Google/Yandex map embed) или ссылку
    map_embed = models.TextField(blank=True, help_text="Вставь сюда iframe карты (embed)")
    map_url = models.URLField(blank=True)

    telegram_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    vk_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return "Настройки сайта"

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"


class StaticPage(TimeStampedModel):
    """
    Статические страницы типа “О нас”, “Доставка”, “Гарантия” и т.п.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField(help_text="Можно хранить HTML/Markdown")
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Статическая страница"
        verbose_name_plural = "Статические страницы"


class ContactMessage(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Закрыт"
        SPAM = "spam", "Спам"

    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    admin_note = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.name} — {self.created_at:%Y-%m-%d}"

    class Meta:
        verbose_name = "Сообщение (контакты)"
        verbose_name_plural = "Сообщения (контакты)"
        ordering = ["-created_at"]


# -----------------------------
# Catalog
# -----------------------------
class Category(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["sort_order", "name"]


class Brand(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ["name"]


class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    sku = models.CharField(max_length=64, unique=True, help_text="Артикул")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")

    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])

    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return self.name

    @property
    def in_stock(self) -> bool:
        return self.stock_qty > 0

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return f"Фото: {self.product.name}"

    class Meta:
        verbose_name = "Фото товара"
        verbose_name_plural = "Фото товара"
        ordering = ["sort_order", "id"]


class ProductAttribute(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Атрибут (характеристика)"
        verbose_name_plural = "Атрибуты (характеристики)"
        ordering = ["name"]


class ProductAttributeValue(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.PROTECT, related_name="values")
    value = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.product.name}: {self.attribute.name} = {self.value}"

    class Meta:
        verbose_name = "Значение характеристики"
        verbose_name_plural = "Значения характеристик"
        ordering = ["sort_order", "id"]
        unique_together = ("product", "attribute", "value")


# -----------------------------
# Cars & Compatibility
# -----------------------------
class CarModel(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    image = models.ImageField(upload_to="cars/", blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Модель авто"
        verbose_name_plural = "Модели авто"
        ordering = ["sort_order", "name"]


class ProductCompatibility(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="compatibilities")
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name="compatible_products")
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} ↔ {self.car_model.name}"

    class Meta:
        verbose_name = "Совместимость товара"
        verbose_name_plural = "Совместимости товаров"
        unique_together = ("product", "car_model")


class UserCar(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cars")
    car_model = models.ForeignKey(CarModel, on_delete=models.PROTECT, related_name="user_cars")

    year = models.PositiveIntegerField(null=True, blank=True)
    vin = models.CharField(max_length=32, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return f"{self.user} — {self.car_model.name}"

    class Meta:
        verbose_name = "Авто пользователя"
        verbose_name_plural = "Авто пользователей"
        ordering = ["-is_primary", "-created_at"]


# -----------------------------
# Orders / Payments
# -----------------------------
class Order(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        PAID = "paid", "Оплачен"
        SHIPPED = "shipped", "Отправлен"
        DONE = "done", "Завершён"
        CANCELED = "canceled", "Отменён"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)

    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)

    delivery_address = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return f"Заказ #{self.id} — {self.get_status_display()}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")

    name_snapshot = models.CharField(max_length=200)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    qty = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return f"{self.order} — {self.name_snapshot} x{self.qty}"

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CARD = "card", "Карта"
        MIR = "mir", "МИР"
        SBP = "sbp", "СБП"

    class Status(models.TextChoices):
        INIT = "init", "Создан"
        SUCCEEDED = "succeeded", "Успешно"
        FAILED = "failed", "Ошибка"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CARD)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.INIT, db_index=True)

    provider_payment_id = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return f"Оплата #{self.id} — {self.get_status_display()}"

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"
        ordering = ["-created_at"]


# -----------------------------
# Reviews
# -----------------------------
class Review(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")

    name = models.CharField(max_length=120, blank=True)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()

    is_published = models.BooleanField(default=True, db_index=True)

    def __str__(self) -> str:
        who = self.user or self.name or "Гость"
        return f"{self.product.name} — {who}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]
# -----------------------------
# About page (О нас)
# -----------------------------
class AboutPage(models.Model):
    """
    Одна запись - настройка страницы "О нас"
    """
    title = models.CharField(max_length=200, default="О нашей компании")
    subtitle = models.CharField(max_length=300, blank=True)
    hero_image = models.ImageField(upload_to="about/", blank=True, null=True)

    mission_title = models.CharField(max_length=200, default="Наша миссия и видение")
    mission_text = models.TextField(blank=True)

    team_title = models.CharField(max_length=200, default="Наша команда")

    cta_title = models.CharField(max_length=200, default="Готовы найти нужные запчасти?")
    cta_text = models.CharField(max_length=300, blank=True)
    cta_button_text = models.CharField(max_length=80, default="Перейти в каталог")
    cta_button_url = models.CharField(max_length=200, default="/catalog/")
    cta_second_button_text = models.CharField(max_length=80, default="Связаться с нами")
    cta_second_button_url = models.CharField(max_length=200, default="/contacts/")

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return "Страница «О нас»"

    class Meta:
        verbose_name = "О нас (страница)"
        verbose_name_plural = "О нас (страница)"


class AboutFeature(models.Model):
    """
    3 карточки: Качество / Сервис / Гарантии и т.п.
    """
    about = models.ForeignKey(AboutPage, on_delete=models.CASCADE, related_name="features")
    title = models.CharField(max_length=120)
    text = models.CharField(max_length=300, blank=True)
    icon = models.CharField(
        max_length=40,
        blank=True,
        help_text="Иконка FontAwesome, например: fa-solid fa-badge-check",
    )
    color = models.CharField(
        max_length=20,
        default="blue",
        help_text="blue/green/purple (для цвета бейджа)",
    )
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "О нас: преимущество"
        verbose_name_plural = "О нас: преимущества"
        ordering = ["sort_order", "id"]


class AboutStat(models.Model):
    """
    Цифры в синей полосе: 5000+ / 98% / 48ч / 15+
    """
    about = models.ForeignKey(AboutPage, on_delete=models.CASCADE, related_name="stats")
    value = models.CharField(max_length=40, help_text="Например: 5000+")
    label = models.CharField(max_length=120, help_text="Например: Деталей в наличии")
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.value} — {self.label}"

    class Meta:
        verbose_name = "О нас: показатель"
        verbose_name_plural = "О нас: показатели"
        ordering = ["sort_order", "id"]


class TeamMember(models.Model):
    """
    Персонал/команда
    """
    about = models.ForeignKey(AboutPage, on_delete=models.CASCADE, related_name="team")
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True)
    bio = models.CharField(max_length=400, blank=True)
    photo = models.ImageField(upload_to="team/", blank=True, null=True)

    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["sort_order", "id"]

from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=32, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Профиль: {self.user}"


class UserAddress(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="address")

    city = models.CharField(max_length=120, blank=True)
    street = models.CharField(max_length=160, blank=True)
    house = models.CharField(max_length=50, blank=True)
    apartment = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Адрес: {self.user}"
class Favorite(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user} ♥ {self.product}"