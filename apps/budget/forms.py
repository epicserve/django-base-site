import datetime

from django import forms
from django.forms import inlineformset_factory

from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Layout, Submit

from apps.budget.models import Budget, BudgetMembership, Category, RecurringTransaction, Transaction, TransactionLine



class MemberInviteForm(forms.Form):
    email = forms.EmailField(label="Email address")
    role = forms.ChoiceField(choices=BudgetMembership.ROLE_CHOICES, initial=BudgetMembership.ROLE_MEMBER)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("email"),
            Field("role"),
            FormActions(Submit("submit", "Invite Member", css_class="btn btn-primary")),
        )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "category_type"]
        widgets = {
            "category_type": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            FloatingField("name"),
        )


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["description", "due_date", "paid_date", "is_paid", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "paid_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            FloatingField("description"),
            Field("due_date"),
            Field("is_paid"),
            Field("paid_date"),
            Field("notes", rows=3),
        )


class TransactionLineForm(forms.ModelForm):
    class Meta:
        model = TransactionLine
        fields = ["category", "amount", "description"]

    def __init__(self, *args, budget=None, **kwargs):
        super().__init__(*args, **kwargs)
        if budget is not None:
            self.fields["category"].queryset = Category.objects.filter(budget=budget)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("category"),
            FloatingField("amount"),
            FloatingField("description"),
        )


def make_transaction_line_formset(budget=None, extra=1):
    FormSet = inlineformset_factory(
        Transaction,
        TransactionLine,
        form=TransactionLineForm,
        extra=extra,
        min_num=1,
        validate_min=True,
        can_delete=True,
    )

    class BudgetTransactionLineFormSet(FormSet):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for form in self.forms:
                form.fields["category"].queryset = Category.objects.filter(budget=budget) if budget else Category.objects.none()

        def clean(self):
            super().clean()
            types = set()
            for form in self.forms:
                if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                    cat = form.cleaned_data.get("category")
                    if cat:
                        types.add(cat.category_type)
            if len(types) > 1:
                raise forms.ValidationError("All lines must belong to the same type (all income or all expense).")

    return BudgetTransactionLineFormSet


class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ["name", "description", "amount", "category", "frequency", "interval", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, budget=None, **kwargs):
        super().__init__(*args, **kwargs)
        if budget is not None:
            self.fields["category"].queryset = Category.objects.filter(budget=budget)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("name"),
            Field("description", rows=3),
            FloatingField("amount"),
            Field("category"),
            Field("frequency"),
            Field("interval", id="id_interval"),
            Field("start_date"),
            Field("end_date"),
            Field("is_active"),
            FormActions(Submit("submit", "Save", css_class="btn btn-primary")),
        )

    def clean(self):
        cleaned = super().clean()
        frequency = cleaned.get("frequency")
        interval = cleaned.get("interval")
        if frequency == RecurringTransaction.FREQ_EVERY_N:
            if not interval or interval < 1:
                raise forms.ValidationError({"interval": "Interval must be at least 1 month."})
        return cleaned
