from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import Member, Payment, Staff, Shift, Attendance
from .forms import (
    MemberForm, MemberSearchForm, PaymentForm,
    StaffForm, ShiftForm, AttendanceForm,
)


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def dashboard(request):
    """Manager overview — key stats at a glance."""
    today = timezone.now().date()

    # Member stats
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='Active').count()
    expired_members = Member.objects.filter(status='Expired').count()
    new_this_month = Member.objects.filter(
        join_date__year=today.year,
        join_date__month=today.month
    ).count()

    # Revenue stats
    total_revenue = Payment.objects.aggregate(t=Sum('amount'))['t'] or 0
    revenue_this_month = Payment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month
    ).aggregate(t=Sum('amount'))['t'] or 0

    # Staff stats
    total_staff = Staff.objects.count()
    active_staff = Staff.objects.filter(status='Active').count()
    present_today = Attendance.objects.filter(date=today, status='Present').count()

    # Membership type breakdown for chart
    basic_count = Member.objects.filter(membership_type='Basic').count()
    premium_count = Member.objects.filter(membership_type='Premium').count()

    # Recent activity
    recent_members = Member.objects.order_by('-join_date')[:5]
    recent_payments = Payment.objects.select_related('member').order_by('-payment_date')[:5]

    return render(request, 'members/dashboard.html', {
        'total_members': total_members,
        'active_members': active_members,
        'expired_members': expired_members,
        'new_this_month': new_this_month,
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'total_staff': total_staff,
        'active_staff': active_staff,
        'present_today': present_today,
        'basic_count': basic_count,
        'premium_count': premium_count,
        'recent_members': recent_members,
        'recent_payments': recent_payments,
        'today': today,
    })


# ─── MEMBER VIEWS ────────────────────────────────────────────────────────────

def member_list(request):
    search_form = MemberSearchForm(request.GET)
    members = Member.objects.all()

    if search_form.is_valid():
        q = search_form.cleaned_data.get('q')
        if q:
            members = members.filter(
                Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
            )

    paginator = Paginator(members, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'members/list.html', {
        'members': page_obj,
        'search_form': search_form,
    })


def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    payments = member.payments.all()
    return render(request, 'members/detail.html', {
        'member': member,
        'payments': payments,
    })


def add_member(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Member added successfully.")
            return redirect('core:member_list')
    else:
        form = MemberForm()
    return render(request, 'members/add.html', {'form': form})


def edit_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.name}'s details updated.")
            return redirect('core:member_list')
    else:
        form = MemberForm(instance=member)
    return render(request, 'members/edit.html', {'form': form, 'member': member})


def delete_member(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.name
        member.delete()
        messages.success(request, f"{name} has been removed.")
        return redirect('core:member_list')
    return render(request, 'members/delete_confirm.html', {'member': member})


def update_statuses(request):
    today = timezone.now().date()
    expired_count = 0
    for member in Member.objects.filter(status='Active'):
        if member.expiry_date and member.expiry_date < today:
            member.status = 'Expired'
            member.save()
            expired_count += 1
    messages.info(request, f"Done. {expired_count} member(s) marked as Expired.")
    return redirect('core:member_list')


# ─── PAYMENT VIEWS ───────────────────────────────────────────────────────────

def add_payment(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.member = member
            payment.save()
            messages.success(request, f"Payment of KES {payment.amount} recorded for {member.name}.")
            return redirect('core:member_detail', pk=member.pk)
    else:
        form = PaymentForm()
    return render(request, 'members/add_payment.html', {'form': form, 'member': member})


# ─── STAFF VIEWS ─────────────────────────────────────────────────────────────

def staff_list(request):
    staff = Staff.objects.all()
    return render(request, 'members/staff_list.html', {'staff': staff})


def staff_detail(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    shifts = staff.shifts.all()
    attendance = staff.attendance.all()[:30]  # Last 30 records

    # Attendance summary
    present_count = staff.attendance.filter(status='Present').count()
    absent_count = staff.attendance.filter(status='Absent').count()
    late_count = staff.attendance.filter(status='Late').count()

    return render(request, 'members/staff_detail.html', {
        'staff': staff,
        'shifts': shifts,
        'attendance': attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    })


def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff member added.")
            return redirect('core:staff_list')
    else:
        form = StaffForm()
    return render(request, 'members/add_staff.html', {'form': form})


def edit_staff(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, f"{staff.name}'s details updated.")
            return redirect('core:staff_detail', pk=staff.pk)
    else:
        form = StaffForm(instance=staff)
    return render(request, 'members/edit_staff.html', {'form': form, 'staff': staff})


def delete_staff(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        name = staff.name
        staff.delete()
        messages.success(request, f"{name} has been removed from staff.")
        return redirect('core:staff_list')
    return render(request, 'members/delete_staff_confirm.html', {'staff': staff})


def add_shift(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.staff = staff
            shift.save()
            messages.success(request, f"Shift added for {staff.name}.")
            return redirect('core:staff_detail', pk=staff.pk)
    else:
        form = ShiftForm()
    return render(request, 'members/add_shift.html', {'form': form, 'staff': staff})


def log_attendance(request):
    """Log attendance for any staff member on any date."""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance recorded.")
            return redirect('core:staff_list')
    else:
        form = AttendanceForm()
    return render(request, 'members/log_attendance.html', {'form': form})