from django import forms
from .models import WasteSchedule

class WasteScheduleForm(forms.ModelForm):
    class Meta:
        model = WasteSchedule
        fields = ['collection_day', 'start_time', 'end_time', 'active']
        widgets = {
            'collection_day': forms.Select(choices=WasteSchedule.DAYS_OF_WEEK),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }