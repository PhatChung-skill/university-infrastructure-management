"""
Custom admin CRUD views. All require admin_required (role Admin or Django staff/superuser).
"""
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib import messages

from .decorators import admin_required
from .admin_mixins import AdminSaveRedirectMixin, AdminBulkDeleteMixin
from .models import (
    Building,
    Room,
    Tree,
    Equipment,
    Incident,
    IncidentType,
    Asset,
    Maintenance,
    Role,
    AppUser,
)
from .admin_forms import (
    TreeAdminForm,
    EquipmentAdminForm,
    RoomAdminForm,
    BuildingAdminForm,
    IncidentAdminForm,
    IncidentTypeAdminForm,
    AssetAdminForm,
    MaintenanceAdminForm,
    RoleAdminForm,
    AppUserAdminForm,
)


def _admin_list_view(model, template_name, context_object_name, order_by, filters=None):
    """Helper to avoid repeating get_queryset logic."""
    class _ListView(ListView):
        model = model
        template_name = template_name
        context_object_name = context_object_name
        paginate_by = 20

        def get_queryset(self):
            qs = super().get_queryset().order_by(order_by)
            if filters:
                for key, q_param in filters.items():
                    val = self.request.GET.get(key)
                    if val:
                        qs = qs.filter(**{q_param: val})
            q = self.request.GET.get("q")
            if q and hasattr(model, "code"):
                qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q) if hasattr(model, "name") else qs.filter(code__icontains=q))
            elif q:
                if hasattr(model, "name"):
                    qs = qs.filter(name__icontains=q)
                if hasattr(model, "title"):
                    qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            return qs

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx["q"] = self.request.GET.get("q", "")
            for key in (filters or {}).keys():
                ctx[key] = self.request.GET.get(key, "")
            return ctx

    return _ListView


# ----- Tree -----
@method_decorator(admin_required, name="dispatch")
class TreeListView(AdminBulkDeleteMixin, ListView):
    model = Tree
    template_name = "home/admin/tree_list.html"
    context_object_name = "trees"
    paginate_by = 20
    bulk_delete_message = "Đã xóa cây đã chọn."

    def get_queryset(self):
        qs = Tree.objects.all().order_by("code")
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(species__icontains=q))
        if status:
            qs = qs.filter(health_status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx


@method_decorator(admin_required, name="dispatch")
class TreeCreateView(AdminSaveRedirectMixin, CreateView):
    model = Tree
    form_class = TreeAdminForm
    template_name = "home/admin/tree_form.html"
    list_url_name = "admin_tree_list"
    add_url_name = "admin_tree_add"
    edit_url_name = "admin_tree_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm cây xanh mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class TreeUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Tree
    form_class = TreeAdminForm
    template_name = "home/admin/tree_form.html"
    list_url_name = "admin_tree_list"
    add_url_name = "admin_tree_add"
    edit_url_name = "admin_tree_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật thông tin cây.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class TreeDeleteView(DeleteView):
    model = Tree
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_tree_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Cây xanh"
        ctx["list_url"] = "admin_tree_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa cây.")
        return super().delete(request, *args, **kwargs)


# ----- Equipment -----
@method_decorator(admin_required, name="dispatch")
class EquipmentListView(AdminBulkDeleteMixin, ListView):
    model = Equipment
    template_name = "home/admin/equipment_list.html"
    context_object_name = "equipment_list"
    paginate_by = 20
    bulk_delete_message = "Đã xóa thiết bị đã chọn."

    def get_queryset(self):
        qs = Equipment.objects.select_related("room").order_by("code")
        q = (self.request.GET.get("q") or "").strip()
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(
                Q(code__icontains=q)
                | Q(name__icontains=q)
                | Q(equipment_type__icontains=q)
                | Q(room__name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx


@method_decorator(admin_required, name="dispatch")
class EquipmentCreateView(AdminSaveRedirectMixin, CreateView):
    model = Equipment
    form_class = EquipmentAdminForm
    template_name = "home/admin/equipment_form.html"
    list_url_name = "admin_equipment_list"
    add_url_name = "admin_equipment_add"
    edit_url_name = "admin_equipment_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm thiết bị mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class EquipmentUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Equipment
    form_class = EquipmentAdminForm
    template_name = "home/admin/equipment_form.html"
    list_url_name = "admin_equipment_list"
    add_url_name = "admin_equipment_add"
    edit_url_name = "admin_equipment_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật thiết bị.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class EquipmentDeleteView(DeleteView):
    model = Equipment
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_equipment_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Thiết bị"
        ctx["list_url"] = "admin_equipment_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa thiết bị.")
        return super().delete(request, *args, **kwargs)


# ----- Room -----
@method_decorator(admin_required, name="dispatch")
class RoomListView(AdminBulkDeleteMixin, ListView):
    model = Room
    template_name = "home/admin/room_list.html"
    context_object_name = "rooms"
    paginate_by = 20
    bulk_delete_message = "Đã xóa phòng đã chọn."

    def get_queryset(self):
        qs = Room.objects.select_related("building").order_by("name")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            filters = Q(name__icontains=q) | Q(building__name__icontains=q)

            # Tìm theo loại phòng bằng tiếng Việt (label choices)
            q_lower = q.lower()
            matching_types = [
                code
                for code, label in Room.ROOM_TYPES
                if q_lower in label.lower()
            ]
            if matching_types:
                filters |= Q(room_type__in=matching_types)

            # Nếu q là số, cho phép tìm theo sức chứa
            if q.isdigit():
                try:
                    capacity_val = int(q)
                    filters |= Q(capacity=capacity_val)
                except ValueError:
                    pass

            qs = qs.filter(filters)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


@method_decorator(admin_required, name="dispatch")
class RoomCreateView(AdminSaveRedirectMixin, CreateView):
    model = Room
    form_class = RoomAdminForm
    template_name = "home/admin/room_form.html"
    list_url_name = "admin_room_list"
    add_url_name = "admin_room_add"
    edit_url_name = "admin_room_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm phòng mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class RoomUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Room
    form_class = RoomAdminForm
    template_name = "home/admin/room_form.html"
    list_url_name = "admin_room_list"
    add_url_name = "admin_room_add"
    edit_url_name = "admin_room_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật phòng.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class RoomDeleteView(DeleteView):
    model = Room
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_room_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Phòng"
        ctx["list_url"] = "admin_room_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa phòng.")
        return super().delete(request, *args, **kwargs)


# ----- Building -----
@method_decorator(admin_required, name="dispatch")
class BuildingListView(AdminBulkDeleteMixin, ListView):
    model = Building
    template_name = "home/admin/building_list.html"
    context_object_name = "buildings"
    paginate_by = 20
    bulk_delete_message = "Đã xóa tòa nhà đã chọn."

    def get_queryset(self):
        return Building.objects.all().order_by("name")


@method_decorator(admin_required, name="dispatch")
class BuildingCreateView(AdminSaveRedirectMixin, CreateView):
    model = Building
    form_class = BuildingAdminForm
    template_name = "home/admin/building_form.html"
    list_url_name = "admin_building_list"
    add_url_name = "admin_building_add"
    edit_url_name = "admin_building_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm tòa nhà mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class BuildingUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Building
    form_class = BuildingAdminForm
    template_name = "home/admin/building_form.html"
    list_url_name = "admin_building_list"
    add_url_name = "admin_building_add"
    edit_url_name = "admin_building_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật tòa nhà.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class BuildingDeleteView(DeleteView):
    model = Building
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_building_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Tòa nhà"
        ctx["list_url"] = "admin_building_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa tòa nhà.")
        return super().delete(request, *args, **kwargs)


# ----- Incident -----
@method_decorator(admin_required, name="dispatch")
class IncidentListView(AdminBulkDeleteMixin, ListView):
    model = Incident
    template_name = "home/admin/incident_list.html"
    context_object_name = "incidents"
    paginate_by = 20
    bulk_delete_message = "Đã xóa sự cố đã chọn."

    def get_queryset(self):
        qs = Incident.objects.select_related("asset", "incident_type").order_by("-reported_at")
        q = (self.request.GET.get("q") or "").strip()
        status = self.request.GET.get("status")
        if q:
            filters = Q(title__icontains=q) | Q(description__icontains=q)

            # Tìm theo tài sản (code thiết bị, tên thiết bị, mã cây, loài cây)
            filters |= Q(asset__equipment__code__icontains=q)
            filters |= Q(asset__equipment__name__icontains=q)
            filters |= Q(asset__tree__code__icontains=q)
            filters |= Q(asset__tree__species__icontains=q)

            # Tìm theo tên loại sự cố
            filters |= Q(incident_type__name__icontains=q)

            # Tìm theo mức độ ưu tiên (nhập chữ Thấp / Trung bình / Cao)
            q_lower = q.lower()
            matching_priorities = [
                code
                for code, label in Incident.PRIORITY
                if q_lower in label.lower()
            ]
            if matching_priorities:
                filters |= Q(priority__in=matching_priorities)

            qs = qs.filter(filters)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx


@method_decorator(admin_required, name="dispatch")
class IncidentCreateView(AdminSaveRedirectMixin, CreateView):
    model = Incident
    form_class = IncidentAdminForm
    template_name = "home/admin/incident_form.html"
    list_url_name = "admin_incident_list"
    add_url_name = "admin_incident_add"
    edit_url_name = "admin_incident_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm sự cố mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class IncidentUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Incident
    form_class = IncidentAdminForm
    template_name = "home/admin/incident_form.html"
    list_url_name = "admin_incident_list"
    add_url_name = "admin_incident_add"
    edit_url_name = "admin_incident_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật sự cố.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class IncidentDeleteView(DeleteView):
    model = Incident
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_incident_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Sự cố"
        ctx["list_url"] = "admin_incident_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa sự cố.")
        return super().delete(request, *args, **kwargs)


# ----- IncidentType -----
@method_decorator(admin_required, name="dispatch")
class IncidentTypeListView(AdminBulkDeleteMixin, ListView):
    model = IncidentType
    template_name = "home/admin/incident_type_list.html"
    context_object_name = "incident_types"
    paginate_by = 20
    bulk_delete_message = "Đã xóa loại sự cố đã chọn."

    def get_queryset(self):
        return IncidentType.objects.all().order_by("code")


@method_decorator(admin_required, name="dispatch")
class IncidentTypeCreateView(AdminSaveRedirectMixin, CreateView):
    model = IncidentType
    form_class = IncidentTypeAdminForm
    template_name = "home/admin/incident_type_form.html"
    list_url_name = "admin_incident_type_list"
    add_url_name = "admin_incident_type_add"
    edit_url_name = "admin_incident_type_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm loại sự cố mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class IncidentTypeUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = IncidentType
    form_class = IncidentTypeAdminForm
    template_name = "home/admin/incident_type_form.html"
    list_url_name = "admin_incident_type_list"
    add_url_name = "admin_incident_type_add"
    edit_url_name = "admin_incident_type_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật loại sự cố.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class IncidentTypeDeleteView(DeleteView):
    model = IncidentType
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_incident_type_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Loại sự cố"
        ctx["list_url"] = "admin_incident_type_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa loại sự cố.")
        return super().delete(request, *args, **kwargs)


# ----- Asset -----
@method_decorator(admin_required, name="dispatch")
class AssetListView(AdminBulkDeleteMixin, ListView):
    model = Asset
    template_name = "home/admin/asset_list.html"
    context_object_name = "assets"
    paginate_by = 20
    bulk_delete_message = "Đã xóa tài sản đã chọn."

    def get_queryset(self):
        return Asset.objects.select_related("equipment", "tree").order_by("id")


@method_decorator(admin_required, name="dispatch")
class AssetCreateView(AdminSaveRedirectMixin, CreateView):
    model = Asset
    form_class = AssetAdminForm
    template_name = "home/admin/asset_form.html"
    list_url_name = "admin_asset_list"
    add_url_name = "admin_asset_add"
    edit_url_name = "admin_asset_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm tài sản mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class AssetUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Asset
    form_class = AssetAdminForm
    template_name = "home/admin/asset_form.html"
    list_url_name = "admin_asset_list"
    add_url_name = "admin_asset_add"
    edit_url_name = "admin_asset_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật tài sản.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class AssetDeleteView(DeleteView):
    model = Asset
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_asset_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Tài sản"
        ctx["list_url"] = "admin_asset_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa tài sản.")
        return super().delete(request, *args, **kwargs)


# ----- Maintenance -----
@method_decorator(admin_required, name="dispatch")
class MaintenanceListView(AdminBulkDeleteMixin, ListView):
    model = Maintenance
    template_name = "home/admin/maintenance_list.html"
    context_object_name = "maintenances"
    paginate_by = 20
    bulk_delete_message = "Đã xóa phiếu bảo trì đã chọn."

    def get_queryset(self):
        return Maintenance.objects.select_related("asset", "staff").order_by("-maintenance_date")


@method_decorator(admin_required, name="dispatch")
class MaintenanceCreateView(AdminSaveRedirectMixin, CreateView):
    model = Maintenance
    form_class = MaintenanceAdminForm
    template_name = "home/admin/maintenance_form.html"
    list_url_name = "admin_maintenance_list"
    add_url_name = "admin_maintenance_add"
    edit_url_name = "admin_maintenance_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm phiếu bảo trì.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class MaintenanceUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Maintenance
    form_class = MaintenanceAdminForm
    template_name = "home/admin/maintenance_form.html"
    list_url_name = "admin_maintenance_list"
    add_url_name = "admin_maintenance_add"
    edit_url_name = "admin_maintenance_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật phiếu bảo trì.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class MaintenanceDeleteView(DeleteView):
    model = Maintenance
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_maintenance_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Phiếu bảo trì"
        ctx["list_url"] = "admin_maintenance_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa phiếu bảo trì.")
        return super().delete(request, *args, **kwargs)


# ----- Role -----
@method_decorator(admin_required, name="dispatch")
class RoleListView(AdminBulkDeleteMixin, ListView):
    model = Role
    template_name = "home/admin/role_list.html"
    context_object_name = "roles"
    paginate_by = 50
    bulk_delete_message = "Đã xóa vai trò đã chọn."

    def get_queryset(self):
        return Role.objects.all().order_by("name")


@method_decorator(admin_required, name="dispatch")
class RoleCreateView(AdminSaveRedirectMixin, CreateView):
    model = Role
    form_class = RoleAdminForm
    template_name = "home/admin/role_form.html"
    list_url_name = "admin_role_list"
    add_url_name = "admin_role_add"
    edit_url_name = "admin_role_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm vai trò mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class RoleUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = Role
    form_class = RoleAdminForm
    template_name = "home/admin/role_form.html"
    list_url_name = "admin_role_list"
    add_url_name = "admin_role_add"
    edit_url_name = "admin_role_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật vai trò.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class RoleDeleteView(DeleteView):
    model = Role
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_role_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Vai trò"
        ctx["list_url"] = "admin_role_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa vai trò.")
        return super().delete(request, *args, **kwargs)


# ----- AppUser -----
@method_decorator(admin_required, name="dispatch")
class AppUserListView(AdminBulkDeleteMixin, ListView):
    model = AppUser
    template_name = "home/admin/user_list.html"
    context_object_name = "users"
    paginate_by = 20
    bulk_delete_message = "Đã xóa người dùng đã chọn."

    def get_queryset(self):
        return AppUser.objects.select_related("role").order_by("username")


@method_decorator(admin_required, name="dispatch")
class AppUserCreateView(AdminSaveRedirectMixin, CreateView):
    model = AppUser
    form_class = AppUserAdminForm
    template_name = "home/admin/user_form.html"
    list_url_name = "admin_user_list"
    add_url_name = "admin_user_add"
    edit_url_name = "admin_user_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã thêm người dùng mới.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class AppUserUpdateView(AdminSaveRedirectMixin, UpdateView):
    model = AppUser
    form_class = AppUserAdminForm
    template_name = "home/admin/user_form.html"
    list_url_name = "admin_user_list"
    add_url_name = "admin_user_add"
    edit_url_name = "admin_user_edit"

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật người dùng.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class AppUserDeleteView(DeleteView):
    model = AppUser
    template_name = "home/admin/confirm_delete.html"
    success_url = reverse_lazy("admin_user_list")
    context_object_name = "obj"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["model_label"] = "Người dùng"
        ctx["list_url"] = "admin_user_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Đã xóa người dùng.")
        return super().delete(request, *args, **kwargs)
