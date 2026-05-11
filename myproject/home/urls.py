from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    home,
    about_school,
    about_news_detail,
    about_event_detail,
    about_updates,
    Login,
    forgot_password_request,
    forgot_password_verify,
    forgot_password_set,
    forgot_password_complete,
    account_password_change,
    admin_dashboard,
    facility_dashboard,
    facility_incident,
    facility_teacher_reports_history,
    teacher_dashboard,
    radius_search,
    dangerous_trees_near_rooms,
    devices_to_check,
    map_building_floors,
    map_floor_rooms,
    map_floor_equipment,
    map_room_layout,
    map_equipment_search,
)
from . import admin_views

urlpatterns = [
    path("", home, name="home"),
    path("gioi-thieu/", about_school, name="about_school"),
    path("gioi-thieu/tin/<int:pk>/", about_news_detail, name="about_news_detail"),
    path("gioi-thieu/su-kien/<int:pk>/", about_event_detail, name="about_event_detail"),
    path("gioi-thieu/tat-ca/", about_updates, name="about_updates"),
    path('login/', Login.as_view(template_name='login.html'), name='login'),
    path("password-reset/", forgot_password_request, name="password_reset"),
    path("password-reset/verify/", forgot_password_verify, name="password_reset_verify"),
    path("password-reset/set-password/", forgot_password_set, name="password_reset_set"),
    path("password-reset/done/", forgot_password_complete, name="password_reset_complete"),
    path("account/change-password/", account_password_change, name="account_password_change"),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    # /admin/ → custom admin dashboard (so /admin/users/ etc. are our pages)
    path('admin/', RedirectView.as_view(pattern_name='admin_dashboard')),
    path('facility/', facility_dashboard, name='facility_dashboard'),
    path('facility/incidents/', facility_incident, name='facility_incident'),
    path('facility/teacher-reports/', facility_teacher_reports_history, name='facility_teacher_reports_history'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),

    # Admin CRUD - Branches
    path('admin/branches/', admin_views.UniversityBranchListView.as_view(), name='admin_branch_list'),
    path('admin/branches/add/', admin_views.UniversityBranchCreateView.as_view(), name='admin_branch_add'),
    path('admin/branches/<int:pk>/edit/', admin_views.UniversityBranchUpdateView.as_view(), name='admin_branch_edit'),
    path('admin/branches/<int:pk>/delete/', admin_views.UniversityBranchDeleteView.as_view(), name='admin_branch_delete'),

    # Admin CRUD - Buildings
    path('admin/buildings/', admin_views.BuildingListView.as_view(), name='admin_building_list'),
    path('admin/buildings/add/', admin_views.BuildingCreateView.as_view(), name='admin_building_add'),
    path('admin/buildings/<int:pk>/edit/', admin_views.BuildingUpdateView.as_view(), name='admin_building_edit'),
    path('admin/buildings/<int:pk>/delete/', admin_views.BuildingDeleteView.as_view(), name='admin_building_delete'),

    # Admin CRUD - Floors
    path('admin/floors/', admin_views.FloorListView.as_view(), name='admin_floor_list'),
    path('admin/floors/add/', admin_views.FloorCreateView.as_view(), name='admin_floor_add'),
    path('admin/floors/<int:pk>/edit/', admin_views.FloorUpdateView.as_view(), name='admin_floor_edit'),
    path('admin/floors/<int:pk>/delete/', admin_views.FloorDeleteView.as_view(), name='admin_floor_delete'),

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
    path('admin/about-page/', admin_views.AboutManageLandingView.as_view(), name='admin_about_manage'),
    path('admin/about-hero/', admin_views.AboutHeroSectionListView.as_view(), name='admin_about_hero_list'),
    path('admin/about-hero/add/', admin_views.AboutHeroSectionCreateView.as_view(), name='admin_about_hero_add'),
    path('admin/about-hero/<int:pk>/edit/', admin_views.AboutHeroSectionUpdateView.as_view(), name='admin_about_hero_edit'),
    path('admin/about-hero/<int:pk>/delete/', admin_views.AboutHeroSectionDeleteView.as_view(), name='admin_about_hero_delete'),
    path('admin/about-core-values/', admin_views.AboutCoreValueListView.as_view(), name='admin_about_core_value_list'),
    path('admin/about-core-values/add/', admin_views.AboutCoreValueCreateView.as_view(), name='admin_about_core_value_add'),
    path('admin/about-core-values/<int:pk>/edit/', admin_views.AboutCoreValueUpdateView.as_view(), name='admin_about_core_value_edit'),
    path('admin/about-core-values/<int:pk>/delete/', admin_views.AboutCoreValueDeleteView.as_view(), name='admin_about_core_value_delete'),
    path('admin/about-announcements/', admin_views.AboutAnnouncementListView.as_view(), name='admin_about_announcement_list'),
    path('admin/about-announcements/add/', admin_views.AboutAnnouncementCreateView.as_view(), name='admin_about_announcement_add'),
    path('admin/about-announcements/<int:pk>/edit/', admin_views.AboutAnnouncementUpdateView.as_view(), name='admin_about_announcement_edit'),
    path('admin/about-announcements/<int:pk>/delete/', admin_views.AboutAnnouncementDeleteView.as_view(), name='admin_about_announcement_delete'),
    path('admin/about-events/', admin_views.AboutFeaturedEventListView.as_view(), name='admin_about_event_list'),
    path('admin/about-events/add/', admin_views.AboutFeaturedEventCreateView.as_view(), name='admin_about_event_add'),
    path('admin/about-events/<int:pk>/edit/', admin_views.AboutFeaturedEventUpdateView.as_view(), name='admin_about_event_edit'),
    path('admin/about-events/<int:pk>/delete/', admin_views.AboutFeaturedEventDeleteView.as_view(), name='admin_about_event_delete'),
    path('admin/about-page/reset-sample/', admin_views.admin_about_reset_sample_data, name='admin_about_reset_sample_data'),
    path('admin/data-import/', admin_views.AdminExcelImportView.as_view(), name='admin_excel_import'),
    path('admin/data-import/template/', admin_views.AdminExcelTemplateDownloadView.as_view(), name='admin_excel_import_template'),

    # API bản đồ drill-down (tòa nhà → tầng → phòng → sơ đồ trong nhà)
    path('api/map/building/<int:building_id>/floors/', map_building_floors, name='map_building_floors'),
    path('api/map/floor/<int:floor_id>/rooms/', map_floor_rooms, name='map_floor_rooms'),
    path('api/map/floor/<int:floor_id>/equipment/', map_floor_equipment, name='map_floor_equipment'),
    path('api/map/room/<int:room_id>/layout/', map_room_layout, name='map_room_layout'),
    path('api/map/equipment-search/', map_equipment_search, name='map_equipment_search'),

    # API GIS / truy vấn không gian
    path('api/spatial/radius-search/', radius_search, name='radius_search'),
    path('api/spatial/dangerous-trees/', dangerous_trees_near_rooms, name='dangerous_trees'),
    path('api/spatial/devices-to-check/', devices_to_check, name='devices_to_check'),
]