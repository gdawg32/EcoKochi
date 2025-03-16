from django import forms
from .models import WasteSchedule, WasteCollector, Resident

class WasteScheduleForm(forms.ModelForm):
    class Meta:
        model = WasteSchedule
        fields = ['collection_day', 'start_time', 'end_time', 'active']
        widgets = {
            'collection_day': forms.Select(choices=WasteSchedule.DAYS_OF_WEEK),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
class CollectorAssignmentForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={
        'id': 'id_date',
        'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-green-600 focus:border-green-600',
        'placeholder': 'Select a future date'
    }))

    collector = forms.ModelChoiceField(
        queryset=WasteCollector.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-green-600 focus:border-green-600'
        })
    )

    residents = forms.ModelMultipleChoiceField(
        queryset=Resident.objects.none(),
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        ward = kwargs.pop('ward', None)
        super().__init__(*args, **kwargs)

        if ward:
            self.fields['collector'].queryset = WasteCollector.objects.filter(ward=ward)
            self.fields['residents'].queryset = Resident.objects.filter(ward=ward)

class AutoAssignmentForm(forms.Form):
    date = forms.DateField(widget=forms.TextInput(attrs={
        'id': 'id_date',
        'class': 'w-full border-gray-300 rounded-md shadow-sm focus:ring-green-600 focus:border-green-600',
        'placeholder': 'Select a date'
    }))
