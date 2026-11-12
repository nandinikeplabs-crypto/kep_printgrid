from django import forms
from .models import Printer, PrinterCapability


class PrinterForm(forms.ModelForm):
    supports_duplex = forms.BooleanField(
        required=False,
        initial=True,
        label="Supports Duplex (Double-Sided Printing)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    supported_paper_sizes = forms.MultipleChoiceField(
        choices=[
            ('A4', 'A4 (210 x 297 mm)'),
            ('A5', 'A5 (148 x 210 mm)'),
            ('B5', 'B5 (176 x 250 mm)'),
            ('A3', 'A3 (297 x 420 mm)'),
            ('LETTER', 'Letter (8.5 x 11 in)'),
            ('LEGAL', 'Legal (8.5 x 14 in)'),
            ('ENVELOPE', 'DL Envelope'),
        ],
        required=False,
        initial=['A4', 'A5', 'LETTER'],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    dpi = forms.IntegerField(
        initial=1200,
        min_value=300,
        max_value=4800,
        label="Print Resolution (DPI)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1200'})
    )

    class Meta:
        model = Printer
        fields = [
            'name',
            'system_printer_name',
            'model_name',
            'handles_bw',
            'handles_color',
            'is_default',
            'is_active',
            'is_online',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. HP Smart Tank 530 (Counter 1)'
            }),
            'system_printer_name': forms.TextInput(attrs={
                'class': 'form-control font-monospace',
                'placeholder': 'Exact Windows Spooler Name (e.g. HP Smart Tank 530 series)'
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. HP Smart Tank 530 (Product No: 4SB24A)'
            }),
            'handles_bw': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'handles_color': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
