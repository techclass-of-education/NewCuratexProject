from django.apps import AppConfig


class AdminUserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_user'


# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime
# from .utils import generate_sql_backup, send_backup_email

# def start_scheduler():

#     scheduler = BackgroundScheduler()

#     def job():
#         try:
#             org_id = "vca"   # ⚠ set dynamically if needed
#             filter_date = datetime.now().strftime("%Y-%m-%d")

#             zip_buffer = generate_sql_backup(org_id, filter_date)
#             send_backup_email(zip_buffer, org_id)

#             print("✅ Backup sent successfully")

#         except Exception as e:
#             print("❌ Backup error:", e)

#     # run every 48 hours
#     scheduler.add_job(job, 'interval', hours=48)

#     scheduler.start()
    
    
# from django.apps import AppConfig

# class AdminUserConfig(AppConfig):
#     name = 'admin_user'

#     def ready(self):
#         from .scheduler import start_scheduler
#         start_scheduler()