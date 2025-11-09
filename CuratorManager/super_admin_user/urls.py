from django.urls import path
from . import views


urlpatterns = [
path('', views.login, name='login_root'),  # Root URL
path('login_auth_su', views.login_auth, name='login_auth'),  # Root URL
path('superdashboard', views.dashboard, name='dashboard'),  # Root URL
path('logout', views.logout_root, name='logout_root'),
path('create_admin_user', views.create_admin_user, name='create_admin_user'),
path('update_admin_user/<int:admin_id>/', views.update_admin_user, name='update_admin_user'),
path('admin_users', views.admin_users_list, name='admin_users_list'),
path('admin_users/<int:admin_id>/', views.admin_user_details, name='admin_user_details'),
]