from django.contrib.gis.db import models


class Role(models.Model):
    name = models.TextField(unique=True)

    class Meta:
        db_table = "role"

    def __str__(self):
        return self.name

class AppUser(models.Model):
    email = models.TextField(unique=True)
    username = models.TextField(unique=True, null=True, blank=True)
    password = models.TextField(blank=True, null=True)
    must_change_password = models.BooleanField(default=False)
    university_branch = models.ForeignKey("UniversityBranch", on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "app_user"

    def __str__(self):
        return self.username