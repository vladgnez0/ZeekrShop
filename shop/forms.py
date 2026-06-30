from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={
            "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
            "placeholder": "Введите логин",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "id": "id_password",
            "class": "mt-2 w-full rounded-xl border px-4 py-3 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-200",
            "placeholder": "Введите пароль",
            "autocomplete": "current-password",
        })
    )



class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label="Имя",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
            "placeholder": "Имя",
            "autocomplete": "given-name",
        })
    )

    last_name = forms.CharField(
        label="Фамилия",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
            "placeholder": "Фамилия",
            "autocomplete": "family-name",
        })
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
            "placeholder": "you@email.com",
            "autocomplete": "email",
        })
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base = "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200"

        # Логин
        self.fields["username"].widget.attrs.update({
            "class": base,
            "placeholder": "Придумайте логин",
            "autocomplete": "username",
        })

        # Пароль
        self.fields["password1"].widget.attrs.update({
            "class": base,
            "placeholder": "Пароль",
            "autocomplete": "new-password",
        })

        # Повтор пароля
        self.fields["password2"].widget.attrs.update({
            "class": base,
            "placeholder": "Повторите пароль",
            "autocomplete": "new-password",
        })
from django import forms
from .models import UserProfile, UserAddress, UserCar


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone", "birth_date")
        widgets = {
            "phone": forms.TextInput(attrs={
                "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
                "placeholder": "+7 (999) 123-45-67",
            }),
            "birth_date": forms.DateInput(attrs={
                "type": "date",
                "class": "mt-2 w-full rounded-xl border px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-200",
            }),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ("city", "street", "house", "apartment", "zip_code")
        widgets = {
            "city": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Москва"}),
            "street": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Улица"}),
            "house": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Дом"}),
            "apartment": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Кв."}),
            "zip_code": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Индекс"}),
        }


class UserCarForm(forms.ModelForm):
    class Meta:
        model = UserCar
        fields = ("car_model", "year", "vin", "notes", "is_primary")
        widgets = {
            "car_model": forms.Select(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200"}),
            "year": forms.NumberInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "2023"}),
            "vin": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "VIN"}),
            "notes": forms.TextInput(attrs={"class": "mt-2 w-full rounded-xl border px-4 py-3 focus:ring-2 focus:ring-blue-200", "placeholder": "Комментарий"}),
        }
