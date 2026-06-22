from django.urls import path
from . import views


urlpatterns = [
    path('', views.login, name='login'),  # Root URL
    path('login', views.login, name='login_org'),  # Root URL
    path('groundform', views.groundform, name='groundform'),  # Root URL
    path('curator/login', views.curatorLogin, name='login_curator'),  # Root URL
    path('groundman/login', views.groundmanLogin, name='login_groundman'),  # Root URL
    path('scorer/login', views.scorerLogin, name='login_scorer'),  # Root URL
    path('login_auth', views.login_auth, name='login_auth'),  # Root URL
    path('login_auth_role', views.login_auth_role, name='login_auth_role'),  # Root URL
    path('login_auth_role_direct', views.login_auth_role_direct, name='login_auth_role_direct'),  # Root URL
    path('create_admin_user_role', views.create_admin_user_role, name='create_admin_user_role'),
    path('admin_users_roles_list', views.admin_user_roles_list, name='admin_user_roles_list'),
    path('admin_user_role_details/<int:admin_id>', views.admin_user_role_details, name='admin_user_role_details'),
    # path('admin_user_role_details/edit/<int:id>', views.admin_user_role_edit_form, name='admin_user_role_edit_form'),
    # path('admin_user_edit/update/<int:id>', views.admin_user_edit, name='admin_user_edit'),
    path("admin_user_role/edit/<int:id>", views.admin_user_edit, name='admin_user_edit'),

    path('orgdashboard', views.org_dashboard, name='org_dashboard'),  # Root URL
    path('roledashboard', views.role_dashboard, name='role_dashboard'),  # Root URL
    path('logout', views.logout_view, name='logout'),
    path('add_state_city', views.add_state_city, name='add_state_city'),
    path('list_state_city', views.list_state_city, name='list_state_city'),
    path('create_ground_master/', views.create_ground_master, name='create_ground_master'),
    path('update_ground_master/<int:ground_id>', views.update_ground_master, name='update_ground_master'),
    path('delete_ground_master/<int:ground_id>', views.delete_ground_master, name='delete_ground_master'),
    path('update_pitches/<int:ground_id>/', views.update_pitches, name='update_pitches'),
    path('ground_list/', views.ground_list, name='ground_list'),
    path('get_ground/<str:ground_id>', views.get_ground, name='get_ground'),
    path('ground_pitches/<int:ground_id>', views.ground_pitches, name='ground_pitches'),
    path('edit_pitch/<int:pitch_id>/<int:ground_id>', views.edit_pitch, name='edit_pitch'),
    path('add_pitch/', views.addNewPItch, name='add_pitch'),
    path('save_edit_pitch', views.save_edit_pitch, name='save_edit_pitch'),
    path('get_cities/', views.get_cities, name='get_cities'),
    path('curator_daily_recording_form/', views.curator_daily_recording_form, name='curator_daily_recording_form'),
    path('update_daily/<int:daily_id>', views.update_daily, name='update_daily'),
    path('delete_daily/<int:daily_id>', views.delete_daily, name='delete_daily'),
    path('curator_daily_recording_list/', views.curator_daily_recording_list, name='curator_daily_recording_list'),
    path('curator_daily_recording_list/filter', views.curator_daily_recording_list_filter, name='curator_daily_recording_list_filter'),
    path('curator_daily_recording_list_filter_by_date/filter', views.curator_daily_recording_list_filter_by_date, name='curator_daily_recording_list_filter_by_date'),
    
    path('get_pitches/<str:ground_id>', views.get_pitches, name='get_pitches'),
    path('get_pitch/<str:pitch_id>', views.get_pitch, name='get_pitch'),
    path('get_all_pitches/', views.get_all_pitches, name='get_all_pitches'),
    path('get_grounds/', views.get_grounds, name='get_grounds'),
    path('machinery/', views.machinery_list, name='machinery_list'),
    path('machinery/insert/', views.insert_machinery, name='insert_machinery'),
    path('machinery/update/<str:machinery_id>', views.update_machinery, name='update_machinery'),
    path('machinery/delete/<str:machinery_id>', views.delete_machinery, name='delete_machinery'),
    path('machinery/<int:machinery_id>/', views.get_machinery_details, name='get_machinery_details'),
    path('matches/', views.match_list, name='match_list'),        # URL to list all matches
    path('matches_filter/', views.match_list_filter, name='match_list_filter'),        # URL to list all matches by ground
    path('match_list_filter_by_date/', views.match_list_filter_by_date, name='match_list_filter_by_date'),        # URL to list all matches by ground
    
    path('matches/insert/', views.insert_match, name='insert_match'),  # URL to insert a new match
    path('matches/update/<int:match_id>/', views.update_match, name='update_match'),  # URL to update a match
    path('matches/delete/<int:match_id>/', views.delete_match, name='delete_match'),  # URL to update a match
    path('add_score/<int:match_id>/', views.add_score, name='add_score'),
    path('save_scores/', views.save_scores, name='save_scores'),
    path('get_match_scores/<int:match_id>/', views.get_match_scores, name='get_match_scores'),
    path('match_scores_list/<int:match_id>', views.match_scores_list, name='match_scores_list'),
    path('delete_score/<int:score_id>/', views.delete_score, name='delete_score'),
    path('update_score/<int:score_id>/', views.update_score, name='update_score'),
    path('api/machinery-data/', views.get_machinery_data, name='machinery_data'),
    path('getAllChemicals/', views.fertilizer_list, name='fertilizer_list'),
    path('addChemical/', views.fertilizer_add, name='fertilizer_add'),
    path('editChemical/<int:id>/', views.fertilizer_edit, name='fertilizer_edit'),
    path('deleteChemical/<int:id>/', views.fertilizer_delete, name='fertilizer_delete'),
    path('get-fertilizers-json/', views.get_fertilizers_json, name='get_fertilizers_json'),
    path('get_chemical/<int:fert_id>/', views.get_single_fertilizer, name='get_single_fertilizer'),
    path('getCurators/', views.getCurators, name='getCurators'),
    path('getGroundmans/', views.getGroundmans, name='getGroundmans'),
    path('getScorer/', views.getScorers, name='getScorers'),
    

    path('save_icc_pitch_form/<int:id>/', views.save_icc_pitch_form, name='save_icc_pitch_form'),
    path('save_icc_pitch_save/', views.save_icc_pitch_save, name='save_icc_pitch_save'),
    # path('save_icc_pitch_save/<int:id>/', views.save_icc_pitch_report, name='save_icc_pitch_report'),


    path('annualreportform/', views.annual_report_form, name='annual_report_form'),
    path('save-maintenance/', views.save_maintenance, name='save-maintenance'),
    path('annual-maintenance-report-page/', views.annual_maintenance_report_page, name='annual-maintenance-report-page'),

    path("annual-maintenance-report-api/",views.annual_maintenance_report_api,name="annual_maintenance_report_api"),
    path("get-clagghammer/<int:id>/<str:t>/<str:f>/",views.get_clagghammer,name="get_clagghammer"),
    path("get-moisture/<int:id>/<str:t>/<str:f>/",views.get_moisture,name="get_moisture"),
    
    
    #####################reports
    
   
    path('report-match/',views.reportMatch, name='report_match'),
    path('chemicalsReport/',views.chemicalsReport, name='chemicalsReport'),
    path('fetchChemicalsReport/',views.fertilizer_usage_report, name='fertilizer_usage_report'),
    path("machinery-report/", views.machinery_report, name="machinery_report"),
    path("machinery_pass_report/", views.machinery_pass_report, name="machinery_pass_report"),

    path('fetch-tournaments/', views.fetch_tournaments, name='fetch_tournaments'),
    path('fetch-cities/', views.fetch_cities, name='fetch_cities'),
    path('fetch-grounds/', views.fetch_grounds, name='fetch_grounds'),
    path('fetch-matches/', views.fetch_matches, name='fetch_matches'),

    # path('generate_report/', views.generate_report, name='generate_report')
    path('match-records/', views.fetch_match_records, name='match_records'),
    path('match-records/download-csv/', views.download_csv, name='download_csv'),
    path('match-records/download-pdf/', views.download_pdf, name='download_pdf'),
    path('match-records/daily_download_csv/', views.daily_download_csv, name='daily_download_csv'),
    path('match-records/match_download_csv/', views.match_download_csv, name='match_download_csv'),
    # path('match-records/daily_download_pdf/', views.daily_download_pdf, name='daily_download_pdf'),
    path('curator_recording_report_page/', views.curator_recording_report_page, name='curator_recording_report_page'),
    path('curator-daily-records/', views.curator_recording_report, name='curator_daily_records'),
    path('match-report-page/', views.match_report_page, name='match_daily_records_page'),
    path('match-report/', views.match_report, name='match_daily_records'),
    path('get-chemical-types/', views.get_unique_chemical_types, name='get_chemical_types'),
    path('icc-match-report/', views.icc_match_report, name='icc_match_report'),
    path('get-icc-report/<int:match_id>/', views.get_icc_report, name='get_icc_report'),
    
    ############ Backup database ###############
    path('export-excel/', views.export_multiple_tables_to_excel, name='export-excel'),
    path('export-sql/', views.export_multiple_sql_files_in_zip, name='export-sql'),
    path('export-form/', views.export_form, name='export-form'),
    path('export-logs/', views.get_export_logs, name='get_export_logs'),
    path('get-admin-users/', views.get_admin_user_by_org, name='get_admin_user_by_org'),
    
]



