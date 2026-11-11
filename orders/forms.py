from django import forms
from .models import PricingRule


class PricingRuleForm(forms.ModelForm):
    class Meta:
        model = PricingRule
        fields = [
            'bw_single_rate', 'bw_double_rate',
            'color_single_rate', 'color_double_rate',
            'a3_bw_rate', 'a3_color_rate', 'is_active'
        ]
        widgets = {
            'bw_single_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'bw_double_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'color_single_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'color_double_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'a3_bw_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'a3_color_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
