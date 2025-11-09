from django import forms
from super_admin_user.models import AdminUserList
from django.core.exceptions import ValidationError
import re
class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = AdminUserList
        fields = ['org_id', 'name', 'email', 'username', 'address', 'mobile', 'state', 'city', 'superadmin_id']
        widgets = {
            'org_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
                       'username': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'superadmin_id': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValidationError("Please enter a valid email address.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not re.match(r"^[0-9]{10}$", mobile):
            raise ValidationError("Please enter a valid 10-digit mobile number.")
        return mobile
