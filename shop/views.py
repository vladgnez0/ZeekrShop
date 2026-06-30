from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, List

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.db.models import Q, Min, Max  # <-- добавили Prefetch
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, RegisterForm
from .forms import ProfileForm, AddressForm, UserCarForm
from .models import (
    Brand,
    CarModel,
    Category,
    ContactMessage,
    Order,
    OrderItem,
    Payment,
    Product,
    SiteSetting,
    StaticPage,
    UserCar,
    AboutPage
)
from .models import Favorite
from .models import ProductImage, UserProfile, UserAddress


def _site_settings() -> SiteSetting | None:
    return SiteSetting.objects.first()


def _cart(request: HttpRequest) -> Dict[str, int]:
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    fixed: Dict[str, int] = {}
    for k, v in cart.items():
        try:
            pid = str(int(k))
            qty = int(v)
            if qty > 0:
                fixed[pid] = qty
        except Exception:
            continue
    request.session["cart"] = fixed
    return fixed


@dataclass
class CartItem:
    product: Product
    qty: int
    line_total: Decimal


def _cart_items_and_total(request: HttpRequest) -> tuple[List[CartItem], Decimal]:
    cart = _cart(request)
    pids = [int(pid) for pid in cart.keys()] if cart else []
    products = {p.id: p for p in Product.objects.filter(id__in=pids, is_active=True).prefetch_related("images")}
    items: List[CartItem] = []
    total = Decimal("0")
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = products.get(pid)
        if not p:
            continue
        line = Decimal(str(p.price)) * Decimal(qty)
        items.append(CartItem(product=p, qty=qty, line_total=line))
        total += line
    return items, total


def _wishlist(request: HttpRequest) -> set[int]:
    data = request.session.get("wishlist", [])
    if not isinstance(data, list):
        data = []
    out: set[int] = set()
    for x in data:
        try:
            out.add(int(x))
        except Exception:
            pass
    request.session["wishlist"] = list(out)
    return out


def _base_context(request: HttpRequest) -> dict:
    cart_count = sum(_cart(request).values())
    return {"site_settings": _site_settings(), "cart_count": cart_count}


def home(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    ctx["categories"] = Category.objects.filter(is_active=True).order_by("sort_order", "name")[:8]
    ctx["featured_products"] = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category", "brand")
        .prefetch_related("images")
        .order_by("-updated_at")[:8]
    )
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))

    ctx["favorite_ids"] = favorite_ids
    return render(request, "shop/home.html", ctx)


def catalog(request):
    ctx = _base_context(request)

    # --- базовые списки для фильтров ---
    categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by("sort_order", "name")
    brands = Brand.objects.filter(is_active=True).order_by("name")

    # --- queryset товаров ---
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "sort_order", "id")))
    )

    # --- фильтры из GET ---
    selected_category_slugs = request.GET.getlist("category")
    selected_brand_slugs = request.GET.getlist("brand")
    in_stock = request.GET.get("in_stock") == "1"
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(short_description__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__name__icontains=q) |
            Q(category__name__icontains=q)
        )

    # price range
    price_min = request.GET.get("min") or ""
    price_max = request.GET.get("max") or ""

    if q:
        qs = qs.filter(name__icontains=q)

    if selected_category_slugs:
        qs = qs.filter(category__slug__in=selected_category_slugs)

    if selected_brand_slugs:
        qs = qs.filter(brand__slug__in=selected_brand_slugs)

    if in_stock:
        qs = qs.filter(stock_qty__gt=0)

    def _to_decimal(v: str):
        try:
            return Decimal(v)
        except (InvalidOperation, TypeError):
            return None

    pmin = _to_decimal(price_min) if price_min else None
    pmax = _to_decimal(price_max) if price_max else None

    if pmin is not None:
        qs = qs.filter(price__gte=pmin)
    if pmax is not None:
        qs = qs.filter(price__lte=pmax)

    # --- сортировка ---
    sort = request.GET.get("sort") or "popular"
    sort_map = {
        "popular": "-is_featured",
        "new": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "name": "name",
    }
    qs = qs.order_by(sort_map.get(sort, "-is_featured"), "-created_at")

    # --- границы цены для UI (по текущему набору товаров без price фильтра) ---
    # Чтобы границы не "прыгать" слишком сильно, можно считать по всем товарам (или по выбранным категориям/брендам)
    base_for_price = (
        Product.objects.filter(is_active=True)
        .filter(category__slug__in=selected_category_slugs) if selected_category_slugs else Product.objects.filter(
            is_active=True)
    )
    if selected_brand_slugs:
        base_for_price = base_for_price.filter(brand__slug__in=selected_brand_slugs)

    bounds = base_for_price.aggregate(min_price=Min("price"), max_price=Max("price"))
    ui_min = bounds["min_price"] or Decimal("0")
    ui_max = bounds["max_price"] or Decimal("100000")

    # --- пагинация ---
    page = request.GET.get("page") or 1
    paginator = Paginator(qs, 9)  # 9 карточек как на скрине
    page_obj = paginator.get_page(page)

    # --- контекст ---
    ctx.update({
        "categories": categories,
        "brands": brands,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,

        "selected_category_slugs": selected_category_slugs,
        "selected_brand_slugs": selected_brand_slugs,
        "in_stock": in_stock,
        "q": q,
        "sort": sort,

        "ui_min": ui_min,
        "ui_max": ui_max,
        "price_min": price_min,
        "price_max": price_max,
    })
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user)
            .values_list("product_id", flat=True)
        )

    ctx["favorite_ids"] = favorite_ids
    return render(request, "shop/catalog.html", ctx)


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    ctx = _base_context(request)
    product = get_object_or_404(
        Product.objects.filter(is_active=True)
        .select_related("category", "brand")
        .prefetch_related("images", "attribute_values__attribute", "compatibilities__car_model", "reviews"),
        slug=slug,
    )
    ctx["product"] = product
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))

    ctx["favorite_ids"] = favorite_ids
    return render(request, "shop/product_detail.html", ctx)


def cart(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    items, total = _cart_items_and_total(request)
    ctx["cart_items"] = items
    ctx["cart_total"] = total
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))

    ctx["favorite_ids"] = favorite_ids
    return render(request, "shop/cart.html", ctx)


@require_GET
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    p = get_object_or_404(Product, id=product_id, is_active=True)
    cart = _cart(request)
    cart[str(p.id)] = cart.get(str(p.id), 0) + 1
    request.session.modified = True
    messages.success(request, f"Добавлено в корзину: {p.name}")
    return redirect("shop:cart")


@require_GET
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = _cart(request)
    pid = str(product_id)
    if pid not in cart:
        return redirect("shop:cart")
    try:
        qty = int(request.GET.get("qty", cart[pid]))
    except Exception:
        qty = cart[pid]
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = qty
    request.session.modified = True
    return redirect("shop:cart")


@require_GET
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    cart = _cart(request)
    cart.pop(str(product_id), None)
    request.session.modified = True
    return redirect("shop:cart")


@login_required(login_url="shop:auth")
@require_http_methods(["GET", "POST"])
def checkout(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    items, total = _cart_items_and_total(request)
    ctx["cart_items"] = items
    ctx["cart_total"] = total

    if not items:
        messages.error(request, "Корзина пуста.")
        return redirect("shop:cart")

    # Достаём профиль/адрес (если нет — создаём пустые)
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    address_obj, _ = UserAddress.objects.get_or_create(user=request.user)

    # --- значения по умолчанию для формы (GET) ---
    initial_full_name = (request.user.get_full_name() or "").strip()
    initial_email = (request.user.email or "").strip()
    initial_phone = (profile_obj.phone or "").strip()

    # Собираем адрес в одну строку (под твою форму delivery_address)
    parts = []
    if address_obj.zip_code: parts.append(address_obj.zip_code)
    if address_obj.city: parts.append(address_obj.city)
    if address_obj.street: parts.append(address_obj.street)
    if address_obj.house: parts.append(f"д. {address_obj.house}")
    if address_obj.apartment: parts.append(f"кв. {address_obj.apartment}")
    initial_delivery_address = ", ".join(parts)

    if request.method == "POST":
        # берем из формы, если пусто — подставляем из профиля
        full_name = (request.POST.get("full_name") or initial_full_name).strip()
        phone = (request.POST.get("phone") or initial_phone).strip()
        email = (request.POST.get("email") or initial_email).strip()
        delivery_address = (request.POST.get("delivery_address") or initial_delivery_address).strip()
        comment = (request.POST.get("comment") or "").strip()
        payment_method = request.POST.get("payment_method", "card")

        order = Order.objects.create(
            user=request.user,  # ✅ только авторизованный
            full_name=full_name,
            phone=phone,
            email=email,
            delivery_address=delivery_address,
            comment=comment,
            subtotal=total,
            total=total,
        )

        for it in items:
            OrderItem.objects.create(
                order=order,
                product=it.product,
                name_snapshot=it.product.name,
                price_snapshot=it.product.price,
                qty=it.qty,
                line_total=it.line_total,
            )

        Payment.objects.create(order=order, method=payment_method, amount=total)

        request.session["cart"] = {}
        request.session.modified = True

        messages.success(request, f"Заявка отправлена! Менеджер скоро с вами свяжется. Номер заказа: #{order.id}")
        return redirect("shop:order_detail", pk=order.id)

    # GET: отдаём defaults в шаблон
    ctx.update({
        "initial_full_name": initial_full_name,
        "initial_phone": initial_phone,
        "initial_email": initial_email,
        "initial_delivery_address": initial_delivery_address,
        "profile_obj": profile_obj,
        "address_obj": address_obj,
    })
    return render(request, "shop/checkout.html", ctx)


def about(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    ctx["page"] = StaticPage.objects.filter(slug="about", is_published=True).first()
    return render(request, "shop/about.html", ctx)


def contacts(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name", "").strip(),
            email=request.POST.get("email", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            subject=request.POST.get("subject", "").strip(),
            message=request.POST.get("message", "").strip(),
        )
        messages.success(request, "Сообщение отправлено. Мы свяжемся с вами.")
        return redirect("shop:contacts")
    return render(request, "shop/contacts.html", ctx)


def auth_view(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    return render(request, "shop/auth.html", ctx)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    ctx["user_cars"] = request.user.cars.select_related("car_model").all()
    ctx["orders"] = request.user.orders.all()[:10]
    return render(request, "shop/profile.html", ctx)


@login_required
def add_car(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request)
    ctx["car_models"] = CarModel.objects.filter(is_active=True).order_by("sort_order", "name")

    if request.method == "POST":
        model_name = request.POST.get("model", "").strip()
        car_model = CarModel.objects.filter(name=model_name).first()
        if not car_model:
            messages.error(request, "Не удалось определить модель. Выберите модель ещё раз.")
            return redirect("shop:add_car")

        is_primary = bool(request.POST.get("is_primary"))
        if is_primary:
            request.user.cars.update(is_primary=False)

        year = request.POST.get("year", "").strip()
        UserCar.objects.create(
            user=request.user,
            car_model=car_model,
            year=int(year) if year.isdigit() else None,
            vin=request.POST.get("vin", "").strip(),
            notes=request.POST.get("notes", "").strip(),
            is_primary=is_primary,
        )
        messages.success(request, "Автомобиль добавлен.")
        return redirect("shop:profile")

    return render(request, "shop/add_car.html", ctx)


@require_GET
def wishlist_toggle(request: HttpRequest, product_id: int) -> HttpResponse:
    wl = _wishlist(request)
    if product_id in wl:
        wl.remove(product_id)
        messages.info(request, "Убрано из избранного.")
    else:
        wl.add(product_id)
        messages.success(request, "Добавлено в избранное.")
    request.session["wishlist"] = list(wl)
    request.session.modified = True
    return redirect(request.META.get("HTTP_REFERER", "/"))


def about(request):
    ctx = _base_context(request)

    about_page = (
        AboutPage.objects.filter(is_active=True)
        .prefetch_related("features", "stats", "team")
        .first()
    )

    ctx["about_page"] = about_page
    return render(request, "shop/about.html", ctx)


def search_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    qs = (
        Product.objects.filter(is_active=True)
        .select_related("brand", "category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_main", "sort_order", "id"),
            )
        )
        .filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(short_description__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__name__icontains=q) |
            Q(category__name__icontains=q)
        )
        .order_by("-is_featured", "-created_at")[:8]
    )

    results = []
    for p in qs:
        img = p.images.all()[0].image.url if p.images.all() else ""
        results.append({
            "name": p.name,
            "slug": p.slug,
            "sku": p.sku,
            "brand": p.brand.name if p.brand else "",
            "category": p.category.name if p.category else "",
            "price": str(p.price),
            "image": img,
            "url": reverse("shop:product_detail", kwargs={"slug": p.slug}),
        })

    return JsonResponse({"results": results})


def auth_view(request):
    ctx = _base_context(request)
    next_url = request.GET.get("next") or request.POST.get("next") or "/profile/"

    if request.user.is_authenticated:
        return redirect(next_url)

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is None:
            form.add_error(None, "Неверный логин или пароль.")
        else:
            login(request, user)
            return redirect(next_url)

    ctx["form"] = form
    ctx["next"] = next_url
    return render(request, "shop/auth.html", ctx)


def register_view(request):
    ctx = _base_context(request)
    next_url = request.GET.get("next") or request.POST.get("next") or "/profile/"

    if request.user.is_authenticated:
        return redirect(next_url)

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(next_url)

    ctx["form"] = form
    ctx["next"] = next_url
    return render(request, "shop/register.html", ctx)


def logout_view(request):
    logout(request)
    return redirect("shop:home")


def logout_view(request):
    logout(request)
    return redirect("shop:home")


@login_required
def profile(request):
    ctx = _base_context(request)
    user = request.user

    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    address_obj, _ = UserAddress.objects.get_or_create(user=user)

    cars = UserCar.objects.filter(user=user).select_related("car_model").order_by("-is_primary", "-created_at")
    orders = Order.objects.filter(user=user).order_by("-created_at")[:5]

    ctx.update({
        "profile_obj": profile_obj,
        "address_obj": address_obj,
        "cars": cars,
        "orders": orders,
        "active_tab": "profile",
    })
    return render(request, "shop/profile.html", ctx)


@login_required
def profile_edit(request):
    ctx = _base_context(request)
    obj, _ = UserProfile.objects.get_or_create(user=request.user)

    form = ProfileForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("shop:profile")

    ctx["form"] = form
    return render(request, "shop/profile_edit.html", ctx)


@login_required
def address_edit(request):
    ctx = _base_context(request)
    obj, _ = UserAddress.objects.get_or_create(user=request.user)

    form = AddressForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("shop:profile")

    ctx["form"] = form
    return render(request, "shop/address_edit.html", ctx)


@login_required
def car_add(request):
    ctx = _base_context(request)
    form = UserCarForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        car = form.save(commit=False)
        car.user = request.user
        car.save()

        # если поставили "основной" — сбрасываем остальные
        if car.is_primary:
            UserCar.objects.filter(user=request.user).exclude(id=car.id).update(is_primary=False)

        return redirect("shop:profile")

    ctx["form"] = form
    ctx["title"] = "Добавить автомобиль"
    return render(request, "shop/car_form.html", ctx)


@login_required
def car_edit(request, pk):
    ctx = _base_context(request)
    car = get_object_or_404(UserCar, pk=pk, user=request.user)

    form = UserCarForm(request.POST or None, instance=car)
    if request.method == "POST" and form.is_valid():
        car = form.save()

        if car.is_primary:
            UserCar.objects.filter(user=request.user).exclude(id=car.id).update(is_primary=False)

        return redirect("shop:profile")

    ctx["form"] = form
    ctx["title"] = "Редактировать автомобиль"
    return render(request, "shop/car_form.html", ctx)


@login_required
def car_delete(request, pk):
    car = get_object_or_404(UserCar, pk=pk, user=request.user)
    if request.method == "POST":
        car.delete()
        return redirect("shop:profile")
    return render(request, "shop/car_delete.html", {"car": car, **_base_context(request)})


@login_required
def favorites(request):
    ctx = _base_context(request)

    favs = (
        Favorite.objects.filter(user=request.user)
        .select_related("product", "product__brand", "product__category")
        .prefetch_related(
            Prefetch(
                "product__images",
                queryset=ProductImage.objects.order_by("-is_main", "sort_order", "id"),
            )
        )
        .order_by("-created_at")
    )

    ctx.update({
        "favorites": favs,
        "active_tab": "favorites",
    })
    return render(request, "shop/favorites.html", ctx)


@login_required
def favorite_toggle(request, product_id):
    if request.method != "POST":
        return redirect("shop:catalog")

    obj = Favorite.objects.filter(user=request.user, product_id=product_id)
    if obj.exists():
        obj.delete()
        messages.info(request, "Удалено из избранного")
    else:
        Favorite.objects.create(user=request.user, product_id=product_id)
        messages.success(request, "Добавлено в избранное")

    return redirect(request.META.get("HTTP_REFERER", reverse_lazy("shop:favorites")))


@login_required
def settings_page(request):
    ctx = _base_context(request)
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    address_obj, _ = UserAddress.objects.get_or_create(user=request.user)

    ctx.update({
        "profile_obj": profile_obj,
        "address_obj": address_obj,
        "active_tab": "settings",
    })
    return render(request, "shop/settings.html", ctx)


class CabinetPasswordChangeView(PasswordChangeView):
    template_name = "shop/password_change.html"
    success_url = reverse_lazy("shop:settings")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_base_context(self.request))
        ctx["active_tab"] = "settings"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Пароль успешно изменён.")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        base = "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200"
        for name in ["old_password", "new_password1", "new_password2"]:
            if name in form.fields:
                form.fields[name].widget.attrs.update({"class": base})
        return form


@login_required
def orders(request):
    ctx = _base_context(request)
    qs = Order.objects.filter(user=request.user).order_by("-created_at")
    ctx.update({"orders": qs, "active_tab": "profile"})
    return render(request, "shop/orders.html", ctx)


@login_required
def order_detail(request, pk):
    ctx = _base_context(request)
    o = get_object_or_404(Order, pk=pk, user=request.user)
    ctx.update({"order": o, "active_tab": "profile"})
    return render(request, "shop/order_detail.html", ctx)


def _get_cart(session):
    """
    Корзина в сессии: { "product_id": qty }
    """
    cart = session.get("cart")
    if cart is None:
        cart = {}
        session["cart"] = cart
    return cart


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    qty = request.POST.get("qty", "1")
    try:
        qty = int(qty)
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1

    cart = _get_cart(request.session)
    key = str(product.id)
    cart[key] = cart.get(key, 0) + qty

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(request, f"Добавлено в корзину: {product.name}")
    return redirect(request.META.get("HTTP_REFERER", "/catalog/"))
def custom_404(request, exception):
    return render(request, "shop/404.html", status=404)

def custom_500(request):
    return render(request, "shop/500.html", status=500)