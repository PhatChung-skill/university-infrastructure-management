from __future__ import annotations

from typing import Iterable

from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse


class AdminSaveRedirectMixin:
    """
    Mimic Django admin save buttons:
    - Save
    - Save and continue editing
    - Save and add another
    """

    list_url_name: str | None = None
    add_url_name: str | None = None
    edit_url_name: str | None = None

    def get_success_url(self) -> str:
        if not (self.list_url_name and self.add_url_name and self.edit_url_name):
            raise ValueError("AdminSaveRedirectMixin requires list_url_name/add_url_name/edit_url_name")

        action = self.request.POST.get("_save_action", "save")
        if action == "continue":
            return reverse(self.edit_url_name, kwargs={"pk": self.object.pk})
        if action == "add_another":
            return reverse(self.add_url_name)
        return reverse(self.list_url_name)


class AdminBulkDeleteMixin:
    """
    Minimal 'Actions' support like Django admin: delete selected.
    Expects checkboxes named _selected_action.
    """

    bulk_delete_message: str = "Đã xóa các mục đã chọn."
    action_field_name: str = "action"
    selected_field_name: str = "_selected_action"

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        action = request.POST.get(self.action_field_name) or ""
        if action != "delete_selected":
            return redirect(request.get_full_path())

        selected: Iterable[str] = request.POST.getlist(self.selected_field_name)
        if not selected:
            messages.warning(request, "Vui lòng chọn ít nhất 1 dòng để thực hiện hành động.")
            return redirect(request.get_full_path())

        # Delete and redirect back to same page (keeping filters via get_full_path)
        qs = self.model.objects.filter(pk__in=selected)
        deleted_count = qs.count()
        qs.delete()
        messages.success(request, f"{self.bulk_delete_message} (Đã xóa: {deleted_count})")
        return redirect(request.path)

