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
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Shop No. 4, College Road, Opp. University Gate'})
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
        # Guarantee unique username
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

        # Create default pricing rule for this shop
        PricingRule.objects.create(shop=shop)

        # Generate permanent QR code (PNG + printable PDF)
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


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = [
            'name', 'phone', 'email', 'address',
            'is_accepting_orders', 'pause_message',
            'razorpay_key_id', 'razorpay_key_secret'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_accepting_orders': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'pause_message': forms.TextInput(attrs={'class': 'form-control'}),
            'razorpay_key_id': forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'rzp_live_... or rzp_test_... (leave empty for sandbox)'
            }),
            'razorpay_key_secret': forms.PasswordInput(render_value=True, attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Razorpay Key Secret'
            }),
        }


class StaffCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff Member Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@shop.example'})
    )
    mobile_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9123456789'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'})
    )
    can_manage_printers = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_authorize_retries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    can_manage_pricing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def save(self, shop):
        email = self.cleaned_data['email']
        name = self.cleaned_data['name']
        username = email.split('@')[0]
        base_username = username
        c = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{c}"
            c += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password'],
            first_name=name.split()[0],
            last_name=" ".join(name.split()[1:]),
            role=User.Role.STAFF,
            phone_number=self.cleaned_data['mobile_number']
        )

        staff = ShopStaff.objects.create(
            shop=shop,
            user=user,
            can_manage_printers=self.cleaned_data.get('can_manage_printers', False),
            can_authorize_retries=self.cleaned_data.get('can_authorize_retries', True),
            can_manage_pricing=self.cleaned_data.get('can_manage_pricing', False)
        )
        return staff
