# KEP PrintGrid - User Module Codebase

This document contains all source code related to **Users, Roles, Authentication, Registration, and Session Security** in KEP PrintGrid.

---

## 1. User Model (`core/models.py`)

```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Shop Owner / Admin'
        STAFF = 'STAFF', 'Shop Staff'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_owner(self):
        return self.role == self.Role.OWNER

    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def is_customer(self):
        return self.role == self.Role.CUSTOMER
```

---

## 2. User Forms & Validation (`core/forms.py`)

```python
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import User, Shop, ShopStaff
from orders.models import PricingRule
from core.services.qr_service import generate_shop_qr_code


class ShopOwnerRegistrationForm(forms.Form):
    shop_name = forms.CharField(
        max_length=150,
        label="Shop Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Metro Xerox & Print Centre'})
    )
    owner_name = forms.CharField(
        max_length=150,
        label="Owner Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ramesh Kumar'})
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ramesh@printgrid.example'})
    )
    mobile_number = forms.CharField(
        max_length=20,
        label="Mobile Number",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'At least 8 characters'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat your password'})
    )
    shop_address = forms.CharField(
        label="Shop Address",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Shop Address'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email address already exists. Please log in.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                validate_password(password)
        return cleaned_data

    @transaction.atomic
    def save(self):
        email = self.cleaned_data['email']
        owner_name = self.cleaned_data['owner_name']
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        first_name = owner_name.split()[0] if owner_name else ""
        last_name = " ".join(owner_name.split()[1:]) if " " in owner_name else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            role=User.Role.OWNER,
            phone_number=self.cleaned_data['mobile_number']
        )

        shop = Shop.objects.create(
            name=self.cleaned_data['shop_name'],
            owner=user,
            phone=self.cleaned_data['mobile_number'],
            email=email,
            address=self.cleaned_data['shop_address'],
            is_accepting_orders=True
        )

        PricingRule.objects.create(shop=shop)
        generate_shop_qr_code(shop)
        return user, shop


class LoginForm(forms.Form):
    email_or_username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def clean(self):
        cleaned_data = super().clean()
        login_val = cleaned_data.get('email_or_username', '').strip()
        password = cleaned_data.get('password')

        if login_val and password:
            user = None
            if '@' in login_val:
                try:
                    user_obj = User.objects.get(email__iexact=login_val)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            else:
                user = authenticate(username=login_val, password=password)

            if not user:
                raise ValidationError("Invalid email/username or password. Please try again.")
            if not user.is_active:
                raise ValidationError("This account is currently disabled.")

            cleaned_data['authenticated_user'] = user

        return cleaned_data
```

---

## 3. User Role-Based Access Control (`core/decorators.py`)

```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not (request.user.is_owner() or request.user.is_superuser):
            messages.error(request, "Access denied. Only registered shop owners can access this section.")
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_or_owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not (request.user.is_owner() or request.user.is_staff_member() or request.user.is_superuser):
            messages.error(request, "Access restricted to shop owners and authorized staff members.")
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

---

## 4. User Views (`core/views.py`)

```python
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import User, AuditLog
from .forms import ShopOwnerRegistrationForm, LoginForm
from .decorators import staff_or_owner_required

def register_owner(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = ShopOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user, shop = form.save()
            login(request, user)
            AuditLog.objects.create(
                shop=shop,
                user=user,
                action='SHOP_REGISTERED',
                resource_type='Shop',
                resource_id=str(shop.id),
                details={'shop_name': shop.name}
            )
            messages.success(request, f"Welcome to KEP PrintGrid! Your shop '{shop.name}' is now active.")
            return redirect('core:owner_overview')
    else:
        form = ShopOwnerRegistrationForm()
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['authenticated_user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('core:dashboard')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('core:login')


@staff_or_owner_required
def dashboard_dispatch(request):
    if request.user.is_owner() or request.user.is_superuser:
        return redirect('core:owner_overview')
    elif request.user.is_staff_member():
        return redirect('orders:staff_dashboard')
    return redirect('core:home')
```

---

## 5. User Login Template (`templates/core/login.html`)

```html
{% extends 'base.html' %}

{% block title %}Sign In - KEP PrintGrid{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5 bg-white">
                <div class="text-center mb-4">
                    <h3 class="fw-bold">Sign In</h3>
                    <p class="text-muted small">Access your Shop Admin or Staff Console.</p>
                </div>

                <form method="post" novalidate>
                    {% csrf_token %}
                    {% if form.non_field_errors %}
                        <div class="alert alert-danger py-2 small">
                            {% for error in form.non_field_errors %}
                                <div>{{ error }}</div>
                            {% endfor %}
                        </div>
                    {% endif %}

                    <div class="mb-3">
                        <label class="form-label fw-semibold small text-muted">Email or Username</label>
                        {{ form.email_or_username }}
                    </div>

                    <div class="mb-4">
                        <label class="form-label fw-semibold small text-muted">Password</label>
                        {{ form.password }}
                    </div>

                    <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold">Sign In</button>
                </form>

                <div class="text-center mt-4 small text-muted">
                    Need a shop account? <a href="{% url 'core:register' %}">Register Shop</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 6. User Unit & Integration Tests (`tests/test_auth.py`)

```python
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_valid_registration(self):
        payload = {
            'shop_name': 'Express Print Hub',
            'owner_name': 'Rohit Sharma',
            'email': 'rohit@express.example',
            'mobile_number': '+91 9876543210',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'shop_address': 'Shop 10, Metro Station Complex',
        }
        resp = self.client.post(reverse('core:register'), payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(email='rohit@express.example').exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='u1', email='dup@test.com', password='Password123!')
        payload = {
            'shop_name': 'Shop 2',
            'owner_name': 'Owner',
            'email': 'dup@test.com',
            'mobile_number': '+91 9999999999',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'shop_address': 'Main Road'
        }
        resp = self.client.post(reverse('core:register'), payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('email', resp.context['form'].errors)
```
