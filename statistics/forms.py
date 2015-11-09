from django import forms
from django.utils import timezone


class InThePastDaysForm(forms.Form):
    days = forms.IntegerField(label=u'Days', required=True)

    def clean(self):
        cleaned_data = super(InThePastDaysForm, self).clean()

        try:
            n = int(cleaned_data.get('days'))
        except Exception:
            raise forms.ValidationError('<i>days</i> should be a number');

        if n < 1:
            raise forms.ValidationError('<i>days</i> field should be greater than 0')
        elif n > 999:
            raise forms.ValidationError('<i>days</i> field should be lower than 999')


class BetweenDatesForm(forms.Form):
    start = forms.DateTimeField(label=u'From', required=True)
    end = forms.DateTimeField(initial=timezone.now(), label=u'To', required=True)

    def clean(self):
        cleaned_data = super(BetweenDatesForm, self).clean()
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start is None:
            raise forms.ValidationError('<i>start</i> date does not exist.')
        if end is None:
            raise forms.ValidationError('<i>end</i> date does not exist.')
        if start > end:
            raise forms.ValidationError("<i>from</i> date is bigger than <i>to</i> date")
        if start > timezone.now():
            raise forms.ValidationError("Typed date is in the future")
        if end > timezone.now():
            raise forms.ValidationError("Typed date is in the future")