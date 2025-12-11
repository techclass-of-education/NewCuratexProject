from datetime import date
from django import forms
from admin_user.models import AdminRole

class AdminUserRoleForm(forms.ModelForm):

    role = forms.ChoiceField(
        choices=[("Groundman", "Groundman"), ("Curator", "Curator"), ("Scorer", "Scorer")],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    is_suspend = forms.ChoiceField(
        choices=[("0", "Active"), ("1", "Suspended")],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = AdminRole
        fields = ['org_id','ground_id', 'name', 'email', 'password',
                  'username','role','mobile','date_reg','is_suspend']

        widgets = {
            'org_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'ground_id': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select Ground'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email-id'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'}),
            # 'profileImage': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile No.'}),
            'date_reg': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(AdminUserRoleForm, self).__init__(*args, **kwargs)
        self.fields['date_reg'].initial = date.today()
        self.fields['is_suspend'].initial = "0"
