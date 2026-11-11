def printgrid_global_context(request):
    """
    Exposes platform-level global variables to all templates.
    """
    from django.conf import settings
    return {
        'APP_NAME': 'KEP PrintGrid',
        'APP_VERSION': '1.0.0',
        'BASE_APP_URL': getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000'),
        'PAYMENT_SANDBOX_MODE': getattr(settings, 'PAYMENT_SANDBOX_MODE', True),
    }
