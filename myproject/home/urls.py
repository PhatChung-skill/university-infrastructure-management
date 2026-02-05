from django.urls import path
from .views import (
    Login,
    admin_dashboard,
    facility_dashboard,
    facility_incident,
    teacher_dashboard,
)

urlpatterns = [
    path('login/', Login.as_view(template_name='login.html'), name='login'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('facility/', facility_dashboard, name='facility_dashboard'),
    path('facility/incidents/', facility_incident, name='facility_incident'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
]
