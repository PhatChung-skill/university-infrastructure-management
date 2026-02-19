from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    Login,
    admin_dashboard,
    facility_dashboard,
    facility_incident,
    teacher_dashboard,
)
from . import admin_views

urlpatterns = [
    path('login/', Login.as_view(template_name='login.html'), name='login'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    # /admin/ → custom admin dashboard (so /admin/users/ etc. are our pages)
    path('admin/', RedirectView.as_view(pattern_name='admin_dashboard')),
    path('facility/', facility_dashboard, name='facility_dashboard'),
    path('facility/incidents/', facility_incident, name='facility_incident'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),

    # Admin CRUD - Buildings
    path('admin/buildings/', admin_views.BuildingListView.as_view(), name='admin_building_list'),
    path('admin/buildings/add/', admin_views.BuildingCreateView.as_view(), name='admin_building_add'),
    path('admin/buildings/<int:pk>/edit/', admin_views.BuildingUpdateView.as_view(), name='admin_building_edit'),
    path('admin/buildings/<int:pk>/delete/', admin_views.BuildingDeleteView.as_view(), name='admin_building_delete'),

    # Admin CRUD - Rooms
    path('admin/rooms/', admin_views.RoomListView.as_view(), name='admin_room_list'),
    path('admin/rooms/add/', admin_views.RoomCreateView.as_view(), name='admin_room_add'),
    path('admin/rooms/<int:pk>/edit/', admin_views.RoomUpdateView.as_view(), name='admin_room_edit'),
    path('admin/rooms/<int:pk>/delete/', admin_views.RoomDeleteView.as_view(), name='admin_room_delete'),

    # Admin CRUD - Trees
    path('admin/trees/', admin_views.TreeListView.as_view(), name='admin_tree_list'),
    path('admin/trees/add/', admin_views.TreeCreateView.as_view(), name='admin_tree_add'),
    path('admin/trees/<int:pk>/edit/', admin_views.TreeUpdateView.as_view(), name='admin_tree_edit'),
    path('admin/trees/<int:pk>/delete/', admin_views.TreeDeleteView.as_view(), name='admin_tree_delete'),

    # Admin CRUD - Equipment
    path('admin/equipment/', admin_views.EquipmentListView.as_view(), name='admin_equipment_list'),
    path('admin/equipment/add/', admin_views.EquipmentCreateView.as_view(), name='admin_equipment_add'),
    path('admin/equipment/<int:pk>/edit/', admin_views.EquipmentUpdateView.as_view(), name='admin_equipment_edit'),
    path('admin/equipment/<int:pk>/delete/', admin_views.EquipmentDeleteView.as_view(), name='admin_equipment_delete'),

    # Admin CRUD - Incident types
    path('admin/incident-types/', admin_views.IncidentTypeListView.as_view(), name='admin_incident_type_list'),
    path('admin/incident-types/add/', admin_views.IncidentTypeCreateView.as_view(), name='admin_incident_type_add'),
    path('admin/incident-types/<int:pk>/edit/', admin_views.IncidentTypeUpdateView.as_view(), name='admin_incident_type_edit'),
    path('admin/incident-types/<int:pk>/delete/', admin_views.IncidentTypeDeleteView.as_view(), name='admin_incident_type_delete'),

    # Admin CRUD - Incidents
    path('admin/incidents/', admin_views.IncidentListView.as_view(), name='admin_incident_list'),
    path('admin/incidents/add/', admin_views.IncidentCreateView.as_view(), name='admin_incident_add'),
    path('admin/incidents/<int:pk>/edit/', admin_views.IncidentUpdateView.as_view(), name='admin_incident_edit'),
    path('admin/incidents/<int:pk>/delete/', admin_views.IncidentDeleteView.as_view(), name='admin_incident_delete'),

    # Admin CRUD - Assets
    path('admin/assets/', admin_views.AssetListView.as_view(), name='admin_asset_list'),
    path('admin/assets/add/', admin_views.AssetCreateView.as_view(), name='admin_asset_add'),
    path('admin/assets/<int:pk>/edit/', admin_views.AssetUpdateView.as_view(), name='admin_asset_edit'),
    path('admin/assets/<int:pk>/delete/', admin_views.AssetDeleteView.as_view(), name='admin_asset_delete'),

    # Admin CRUD - Maintenance
    path('admin/maintenance/', admin_views.MaintenanceListView.as_view(), name='admin_maintenance_list'),
    path('admin/maintenance/add/', admin_views.MaintenanceCreateView.as_view(), name='admin_maintenance_add'),
    path('admin/maintenance/<int:pk>/edit/', admin_views.MaintenanceUpdateView.as_view(), name='admin_maintenance_edit'),
    path('admin/maintenance/<int:pk>/delete/', admin_views.MaintenanceDeleteView.as_view(), name='admin_maintenance_delete'),

    # Admin CRUD - Roles
    path('admin/roles/', admin_views.RoleListView.as_view(), name='admin_role_list'),
    path('admin/roles/add/', admin_views.RoleCreateView.as_view(), name='admin_role_add'),
    path('admin/roles/<int:pk>/edit/', admin_views.RoleUpdateView.as_view(), name='admin_role_edit'),
    path('admin/roles/<int:pk>/delete/', admin_views.RoleDeleteView.as_view(), name='admin_role_delete'),

    # Admin CRUD - Users (AppUser)
    path('admin/users/', admin_views.AppUserListView.as_view(), name='admin_user_list'),
    path('admin/users/add/', admin_views.AppUserCreateView.as_view(), name='admin_user_add'),
    path('admin/users/<int:pk>/edit/', admin_views.AppUserUpdateView.as_view(), name='admin_user_edit'),
    path('admin/users/<int:pk>/delete/', admin_views.AppUserDeleteView.as_view(), name='admin_user_delete'),
]
