from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField
from django.utils import timezone

class Signup(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField(_("Email"), max_length=254, unique=True)
    password = models.CharField(max_length=128)
    enrollment_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    timezone = TimeZoneField(default='Asia/Kolkata')

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        if self.enrollment_number is None:
            last = Signup.objects.exclude(enrollment_number=None).order_by('-enrollment_number').first()
            self.enrollment_number = 1 if not last else last.enrollment_number + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.enrollment_number or 'No Enrollment'}"

class Attendance(models.Model):
    student = models.ForeignKey(Signup, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} - {self.date} - {'Present' if self.is_present else 'Absent'}"
