from django import forms
from django.utils import timezone
from datetime import date


class BetweenDatesForm(forms.Form):
    start = forms.DateField(label=u'From', required=True)
    end = forms.DateField(initial=timezone.now(), label=u'To', required=True)

    def clean(self):
        cleaned_data = super(BetweenDatesForm, self).clean()
        if cleaned_data.get('start') > cleaned_data.get('end'):
            raise forms.ValidationError("start date is bigger than end")
        if cleaned_data.get('start') > date.today():
            raise forms.ValidationError("Date in future")
        if cleaned_data.get('end') > date.today():
            raise forms.ValidationError("Date in future")