from django.contrib import admin
from .models import Member, Payment, Staff, Shift, Attendance


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_date']


class ShiftInline(admin.TabularInline):
    model = Shift
    extra = 0


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    readonly_fields = ['date']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'membership_type', 'join_date', 'expiry_date', 'status']
    list_filter = ['membership_type', 'status']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['expiry_date']
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'payment_method', 'payment_date']
    list_filter = ['payment_method']
    search_fields = ['member__name']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'phone', 'date_joined', 'status']
    list_filter = ['role', 'status']
    search_fields = ['name', 'phone', 'email']
    inlines = [ShiftInline, AttendanceInline]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['staff', 'day', 'start_time', 'end_time']
    list_filter = ['day']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['staff__name']