from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def owner_required(view_func):
    """
    Decorator for views that checks that the logged-in user is a Shop Owner.
    """
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
    """
    Decorator for views that checks that the user is either a Shop Owner or Shop Staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not (request.user.is_owner() or request.user.is_staff_member() or request.user.is_superuser):
            messages.error(request, "Access restricted to shop owners and authorized staff members.")
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_user_shop(user):
    """
    Retrieves the shop associated with an owner or staff member.
    """
    if not user.is_authenticated:
        return None
    if user.is_owner() or user.is_superuser:
        return user.owned_shops.first()
    if hasattr(user, 'staff_profile'):
        return user.staff_profile.shop
    return None
