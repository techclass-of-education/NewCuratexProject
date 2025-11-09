from django import forms
from super_admin_user.models import AdminUserList
from django.core.exceptions import ValidationError
import re


class AdminUserForm(forms.ModelForm):
    org_id = forms.CharField(
        max_length=100,  # Set appropriate max length
       
        widget=forms.TextInput(attrs={
            'class': 'form-control',
           
           
        })
    )

    class Meta:
        model = AdminUserList
        fields = ['org_id', 'name', 'email', 'password', 'username', 'address', 'mobile','state','city', 'superadmin_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'superadmin_id': forms.Select(attrs={'class': 'form-control'}),
        }
        
        
        
        