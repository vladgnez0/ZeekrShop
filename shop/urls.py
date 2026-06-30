from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("about/", views.about, name="about"),
    path("contacts/", views.contacts, name="contacts"),

    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),

    path("checkout/", views.checkout, name="checkout"),

    path("auth/", views.auth_view, name="auth"),
    path("profile/", views.profile, name="profile"),
    path("profile/add-car/", views.add_car, name="add_car"),

    path("wishlist/toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("api/search/", views.search_suggest, name="search_suggest"),
    path("auth/", views.auth_view, name="auth"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="shop/password_reset.html",
        email_template_name="shop/emails/password_reset_email.txt",
        subject_template_name="shop/emails/password_reset_subject.txt",
        success_url="/password-reset/done/"
    ), name="password_reset"),

    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="shop/password_reset_done.html",
    ), name="password_reset_done"),

    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="shop/password_reset_confirm.html",
        success_url="/reset/done/"
    ), name="password_reset_confirm"),

    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="shop/password_reset_complete.html",
    ), name="password_reset_complete"),

    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/address/", views.address_edit, name="address_edit"),

    path("profile/cars/add/", views.car_add, name="car_add"),
    path("profile/cars/<int:pk>/edit/", views.car_edit, name="car_edit"),
    path("profile/cars/<int:pk>/delete/", views.car_delete, name="car_delete"),
    path("profile/favorites/", views.favorites, name="favorites"),
    path("profile/favorites/toggle/<int:product_id>/", views.favorite_toggle, name="favorite_toggle"),

    path("profile/settings/", views.settings_page, name="settings"),
    path("profile/settings/password/", views.CabinetPasswordChangeView.as_view(), name="password_change"),
    path("profile/orders/", views.orders, name="orders"),
    path("profile/orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("favorites/toggle/<int:product_id>/", views.favorite_toggle, name="favorite_toggle")


]
