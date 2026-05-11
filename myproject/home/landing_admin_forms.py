"""
Forms cho trang quản lý Landing Page (Hero, Grid Items, Announcements).
"""
from django import forms
from .models import LandingHero, LandingGridItem, AboutAnnouncement


def _add_bootstrap(form):
    """Thêm class Bootstrap vào tất cả fields."""
    for field in form.fields.values():
        widget = field.widget
        base = widget.attrs.get("class", "")
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            cls = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            cls = "form-check-input"
        elif isinstance(widget, forms.Textarea):
            cls = "form-control"
        else:
            cls = "form-control"
        widget.attrs["class"] = f"{base} {cls}".strip()


# ----- LandingHero Form -----
class LandingHeroAdminForm(forms.ModelForm):
    """Form chỉnh sửa Hero Section - singleton (chỉ 1 bản ghi)."""

    class Meta:
        model = LandingHero
        fields = ["title", "subtitle", "background_image"]
        labels = {
            "title": "Tiêu đề chính",
            "subtitle": "Lời ngỏ / Mô tả",
            "background_image": "Ảnh nền Hero",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Hệ thống Quản lý Cơ sở hạ tầng Đại học"}),
            "subtitle": forms.Textarea(attrs={"rows": 3, "placeholder": "Nhập lời ngỏ..."}),
        }
        help_texts = {
            "background_image": "Kích thước khuyến nghị: 1920x600px. Để trống sẽ dùng gradient mặc định.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- LandingGridItem Form -----
class LandingGridItemAdminForm(forms.ModelForm):
    """Form quản lý mỗi cột trong lưới Tầm nhìn & Sứ mệnh."""

    class Meta:
        model = LandingGridItem
        fields = ["title", "description", "icon", "image", "order", "is_active"]
        labels = {
            "title": "Tiêu đề",
            "description": "Mô tả",
            "icon": "Icon (emoji)",
            "image": "Ảnh minh họa",
            "order": "Thứ tự hiển thị",
            "is_active": "Hiển thị",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Giảng đường hiện đại"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Mô tả chi tiết..."}),
            "icon": forms.TextInput(attrs={"placeholder": "VD: 🏛️", "style": "width: 80px;"}),
            "order": forms.NumberInput(attrs={"min": "0", "style": "width: 100px;"}),
        }
        help_texts = {
            "icon": "Nhập emoji hoặc để trống nếu dùng ảnh minh họa.",
            "order": "Số nhỏ hơn hiển thị trước. VD: 0, 1, 2...",
            "image": "Ảnh minh họa cho thẻ (tùy chọn, nếu có icon thì ưu tiên icon).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- AboutAnnouncement Form -----
class AboutAnnouncementAdminForm(forms.ModelForm):
    """Form quản lý Tin tức & Thông báo trang giới thiệu."""

    class Meta:
        model = AboutAnnouncement
        fields = ["title", "excerpt", "content", "thumbnail", "is_published", "published_at"]
        labels = {
            "title": "Tiêu đề",
            "excerpt": "Tóm tắt ngắn",
            "content": "Nội dung chi tiết",
            "thumbnail": "Ảnh thu nhỏ (thumbnail)",
            "is_published": "Đang hiển thị",
            "published_at": "Thời gian đăng",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Hoàn thành nâng cấp phòng máy tính khu A"}),
            "excerpt": forms.TextInput(attrs={"placeholder": "Tóm tắt ngắn hiển thị trên thẻ tin tức..."}),
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": "Nhập nội dung chi tiết..."}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "excerpt": "Hiển thị trên thẻ tin tức. Để trống sẽ tự cắt từ nội dung.",
            "thumbnail": "Kích thước khuyến nghị: 400x250px.",
            "published_at": "Tự động điền nếu để trống và bật hiển thị.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        # Ẩn trường published_at vì nó được tự động xử lý
        self.fields["published_at"].required = False
        self.fields["published_at"].widget.attrs["readonly"] = True
        self.fields["published_at"].help_text = "Tự động cập nhật khi lưu với 'Đang hiển thị' = Có."
