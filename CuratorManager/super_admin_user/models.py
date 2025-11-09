from django.db import models
class SuperAdmin(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

class AdminUserList(models.Model):
    name = models.CharField(max_length=255)
    org_id = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    # logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=45, blank=True, null=True)
    city = models.CharField(max_length=45, blank=True, null=True)
    superadmin_id= models.ForeignKey(SuperAdmin, on_delete=models.CASCADE, related_name='superadmins')

    def __str__(self):
        return self.username


class MastersList(models.Model):
    org_id = models.CharField(max_length=20, blank=False, null=False)
    tablename = models.CharField(max_length=255,unique=True)
    auth_groundman = models.BooleanField(blank=False)
    auth_curator = models.BooleanField(blank=False)
    auth_scorer = models.BooleanField(blank=False)
    admin_id= models.ForeignKey(AdminUserList, on_delete=models.CASCADE, related_name='adminuserlist')

    def __str__(self):
        return self.org_id+" "+self.tablename
