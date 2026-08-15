from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('login', views.login_view, name='login'),
    path('login/', views.login_view, name='login-slash'),
    path('mark-attendance', views.mark_attendance_view, name='mark-attendance'),
    path('mark-attendance/', views.mark_attendance_view, name='mark-attendance-slash'),
    path('register-student', views.register_student_view, name='register-student'),
    path('register-student/', views.register_student_view, name='register-student-slash'),
    path('student/stats/<str:student_name>', views.get_student_stats_view, name='student-stats'),
    path('student/stats/<str:student_name>/', views.get_student_stats_view, name='student-stats-slash'),
    path('student/history/<str:student_name>', views.get_student_history_view, name='student-history'),
    path('student/history/<str:student_name>/', views.get_student_history_view, name='student-history-slash'),
    path('get-dashboard-data', views.get_dashboard_data_view, name='get-dashboard-data'),
    path('get-dashboard-data/', views.get_dashboard_data_view, name='get-dashboard-data-slash'),
    path('get-class-roster', views.get_class_roster_view, name='get-class-roster'),
    path('get-class-roster/', views.get_class_roster_view, name='get-class-roster-slash'),
    path('courses', views.get_courses_list_view, name='courses-list'),
    path('courses/', views.get_courses_list_view, name='courses-list-slash'),
    path('export-csv', views.export_csv_view, name='export-csv'),
    path('export-csv/', views.export_csv_view, name='export-csv-slash'),
    path('reset-db', views.reset_db_view, name='reset-db'),
    path('reset-db/', views.reset_db_view, name='reset-db-slash'),
]
