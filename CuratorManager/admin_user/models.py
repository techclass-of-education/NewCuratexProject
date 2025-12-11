from django.db import models

class AdminRole(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    profileImage = models.ImageField(upload_to='profiles/', null=False)
    org_id = models.CharField(max_length=255, null=False)
    ground_id = models.CharField(max_length=255, null=False)
    role = models.CharField(max_length=255, null=False)
    mobile = models.CharField(max_length=255, null=False)
    date_reg = models.DateField(null=False)
    is_suspend = models.BooleanField(default=False)

    def __str__(self):
        return "Username:"+self.username+" Organization ID:"+self.org_id



