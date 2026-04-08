from django import forms
from .models import Member, Payment, Staff, Shift, Attendance


# ─── MEMBER FORMS ────────────────────────────────────────────────────────────

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name', 'phone', 'email', 'join_date', 'duration_months', 'membership_type']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
            'duration_months': forms.NumberInput(attrs={'min': 1, 'max': 24}),
        }
        labels = {'duration_months': 'Duration (months)'}

    def clean_duration_months(self):
        duration = self.cleaned_data.get('duration_months')
        if duration is not None and duration < 1:
            raise forms.ValidationError("Duration must be at least 1 month.")
        return duration

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone.lstrip('+').isdigit():
            raise forms.ValidationError("Phone must contain only digits (with optional leading +).")
        return phone


class MemberSearchForm(forms.Form):
    q = forms.CharField(
        required=False, label='',
        widget=forms.TextInput(attrs={'placeholder': 'Search name, phone or email...'})
    )


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional notes...'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


# ─── STAFF FORMS ─────────────────────────────────────────────────────────────

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'phone', 'email', 'role', 'date_joined', 'status', 'notes']
        widgets = {
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone.lstrip('+').isdigit():
            raise forms.ValidationError("Phone must contain only digits (with optional leading +).")
        return phone


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['staff', 'date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }