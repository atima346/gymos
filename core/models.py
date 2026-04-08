from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta


# ─── MEMBER ──────────────────────────────────────────────────────────────────

class Member(models.Model):
    MEMBERSHIP_CHOICES = [
        ('Basic', 'Basic'),
        ('Premium', 'Premium'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
        ('Suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    join_date = models.DateField(null=True, blank=True)
    duration_months = models.PositiveIntegerField(default=1)
    expiry_date = models.DateField(blank=True, null=True)
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    class Meta:
        ordering = ['-join_date']

    def save(self, *args, **kwargs):
        if self.join_date and self.duration_months:
            self.expiry_date = self.join_date + relativedelta(months=self.duration_months)
        super().save(*args, **kwargs)

    @property
    def total_plan_days(self):
        """Total number of days in this member's plan."""
        if self.join_date and self.expiry_date:
            return (self.expiry_date - self.join_date).days
        return 0

    @property
    def days_used(self):
        """How many days have passed since join_date (capped at total plan days)."""
        if self.join_date:
            today = timezone.now().date()
            used = (today - self.join_date).days
            return min(max(used, 0), self.total_plan_days)
        return 0

    @property
    def days_remaining(self):
        """Days left in the plan. Returns 0 if expired."""
        if self.expiry_date:
            remaining = (self.expiry_date - timezone.now().date()).days
            return max(remaining, 0)
        return 0

    @property
    def utilisation_percent(self):
        """Percentage of plan used (0–100). Used for the progress bar."""
        if self.total_plan_days > 0:
            return min(int((self.days_used / self.total_plan_days) * 100), 100)
        return 0

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def __str__(self):
        return f"{self.name} ({self.status})"


# ─── PAYMENT ─────────────────────────────────────────────────────────────────

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Mpesa', 'Mpesa'),
        ('Bank', 'Bank Transfer'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.member.name} - KES {self.amount} on {self.payment_date}"


# ─── STAFF ───────────────────────────────────────────────────────────────────

class Staff(models.Model):
    ROLE_CHOICES = [
        ('Trainer', 'Trainer'),
        ('Receptionist', 'Receptionist'),
        ('Cleaner', 'Cleaner'),
        ('Manager', 'Manager'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_joined = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, help_text="Any extra info about this staff member.")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.role})"


# ─── SHIFT ───────────────────────────────────────────────────────────────────

class Shift(models.Model):
    """A scheduled shift for a staff member."""
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'),
        ('Saturday', 'Saturday'), ('Sunday', 'Sunday'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='shifts')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['staff', 'day']  # One shift per staff per day

    def __str__(self):
        return f"{self.staff.name} — {self.day} {self.start_time:%H:%M}–{self.end_time:%H:%M}"


# ─── ATTENDANCE ───────────────────────────────────────────────────────────────

class Attendance(models.Model):
    """Records whether a staff member showed up for a given date."""
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['staff', 'date']  # One attendance record per staff per day

    def __str__(self):
        return f"{self.staff.name} — {self.date} ({self.status})"