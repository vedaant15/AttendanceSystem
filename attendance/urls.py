# attendanceSystem/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('qr_generator/', views.qr_generator, name='qr_generator'),
    path('qrcodescanner/', views.qrcodescanner, name='qrcodescanner'),
    # path('attendance_record/', views.attendance_record, name='script'),
    path('loginSignup/', views.loginSignup, name='loginSignup'),
    path('login_view/', views.login_view, name='login_view'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
    path('attendance/', views.view_attendance, name='view_attendance'), 
    path('mark_attendance/<int:enrollment_number>/', views.mark_attendance, name='mark_attendance'),
    path('attendance_list/', views.attendance_list, name='attendance_list'),
]
