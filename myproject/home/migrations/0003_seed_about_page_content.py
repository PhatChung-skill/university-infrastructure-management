from django.db import migrations


def seed_about_page_content(apps, schema_editor):
    AboutHeroSection = apps.get_model("home", "AboutHeroSection")
    AboutCoreValue = apps.get_model("home", "AboutCoreValue")
    AboutAnnouncement = apps.get_model("home", "AboutAnnouncement")

    if not AboutHeroSection.objects.exists():
        AboutHeroSection.objects.create(
            title="Hệ thống Quản lý Cơ sở hạ tầng Đại học",
            welcome_text=(
                "Nền tảng quản lý tập trung hỗ trợ nhà trường vận hành, giám sát và nâng cấp cơ sở hạ tầng "
                "một cách minh bạch, kịp thời và hiệu quả. Dữ liệu được cập nhật liên tục để phục vụ công tác "
                "đào tạo, nghiên cứu và trải nghiệm học tập của sinh viên."
            ),
            is_active=True,
        )

    if not AboutCoreValue.objects.exists():
        AboutCoreValue.objects.bulk_create(
            [
                AboutCoreValue(
                    title="Giảng đường thông minh",
                    description=(
                        "Quản lý tình trạng phòng học, thiết bị trình chiếu và năng lực sử dụng theo thời gian thực."
                    ),
                    icon_class="bi bi-easel2",
                    display_order=1,
                    is_active=True,
                ),
                AboutCoreValue(
                    title="Phòng Lab nghiên cứu",
                    description=(
                        "Theo dõi tài sản phòng lab, lịch bảo trì và mức độ sẵn sàng cho các hoạt động thực hành."
                    ),
                    icon_class="bi bi-cpu",
                    display_order=2,
                    is_active=True,
                ),
                AboutCoreValue(
                    title="Ký túc xá và tiện ích",
                    description=(
                        "Chuẩn hóa dữ liệu hạ tầng lưu trú, hệ thống điện nước và các yêu cầu bảo trì định kỳ."
                    ),
                    icon_class="bi bi-building",
                    display_order=3,
                    is_active=True,
                ),
                AboutCoreValue(
                    title="An toàn và vận hành",
                    description=(
                        "Tiếp nhận sự cố, cảnh báo khu vực rủi ro và hỗ trợ ra quyết định vận hành nhanh chóng."
                    ),
                    icon_class="bi bi-shield-check",
                    display_order=4,
                    is_active=True,
                ),
            ]
        )

    if not AboutAnnouncement.objects.exists():
        AboutAnnouncement.objects.bulk_create(
            [
                AboutAnnouncement(
                    title="Hoàn thành nâng cấp phòng máy tính khu A",
                    summary=(
                        "Nhà trường đã hoàn tất nâng cấp hệ thống máy tính và đường truyền cho khu A."
                    ),
                    content=(
                        "Trong đợt bảo trì tháng này, toàn bộ phòng máy khu A đã được nâng cấp RAM, ổ cứng và "
                        "hạ tầng mạng nội bộ. Việc nâng cấp giúp tăng hiệu suất học tập, giảm thời gian chờ "
                        "khi thực hành các học phần công nghệ."
                    ),
                    is_published=True,
                ),
                AboutAnnouncement(
                    title="Kế hoạch bảo trì thang máy tòa B",
                    summary=(
                        "Thang máy tòa B sẽ được bảo trì định kỳ theo kế hoạch của phòng cơ sở vật chất."
                    ),
                    content=(
                        "Công tác bảo trì thang máy tòa B dự kiến diễn ra trong hai ngày cuối tuần để hạn chế "
                        "ảnh hưởng đến hoạt động giảng dạy. Trong thời gian này, sinh viên và giảng viên vui lòng "
                        "sử dụng lối thang bộ hoặc thang máy dự phòng."
                    ),
                    is_published=True,
                ),
                AboutAnnouncement(
                    title="Bổ sung thiết bị an toàn phòng thí nghiệm",
                    summary=(
                        "Các phòng thí nghiệm đã được trang bị bổ sung thiết bị an toàn theo tiêu chuẩn mới."
                    ),
                    content=(
                        "Nhằm nâng cao mức độ an toàn, nhà trường đã trang bị thêm bình chữa cháy, tủ dụng cụ "
                        "sơ cứu và hệ thống biển báo tại các phòng thí nghiệm trọng điểm. Danh mục thiết bị "
                        "được cập nhật đầy đủ trên hệ thống quản lý hạ tầng."
                    ),
                    is_published=True,
                ),
            ]
        )


def unseed_about_page_content(apps, schema_editor):
    AboutHeroSection = apps.get_model("home", "AboutHeroSection")
    AboutCoreValue = apps.get_model("home", "AboutCoreValue")
    AboutAnnouncement = apps.get_model("home", "AboutAnnouncement")

    AboutHeroSection.objects.filter(
        title="Hệ thống Quản lý Cơ sở hạ tầng Đại học"
    ).delete()
    AboutCoreValue.objects.filter(
        title__in=[
            "Giảng đường thông minh",
            "Phòng Lab nghiên cứu",
            "Ký túc xá và tiện ích",
            "An toàn và vận hành",
        ]
    ).delete()
    AboutAnnouncement.objects.filter(
        title__in=[
            "Hoàn thành nâng cấp phòng máy tính khu A",
            "Kế hoạch bảo trì thang máy tòa B",
            "Bổ sung thiết bị an toàn phòng thí nghiệm",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_about_page_redesign"),
    ]

    operations = [
        migrations.RunPython(seed_about_page_content, unseed_about_page_content),
    ]
