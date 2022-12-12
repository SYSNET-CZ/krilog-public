from django import forms
from shopping.elk import get_words, get_demands

from portal.models import Word, Demand


class MapForm(forms.Form):
    word = forms.ModelChoiceField(label="Poptávaná věc", queryset=Word.objects.all(), required=False)
    demand = forms.ModelChoiceField(label="Poptávka", queryset=Demand.objects.all(), required=False)
    radius = forms.IntegerField(label="Radius v km od poptávky", initial=50, required=False,
                                help_text="Výpočet blízkých nabídek se projeví pouze po vybrání konkrétní poptávky.")
    offers_only = forms.BooleanField(label="Pouze nabídky", required=False, initial=False)


class MapElkForm(forms.Form):
    word = forms.CharField(label="Poptávaná věc", widget=forms.Select(), required=False)
    demand = forms.CharField(label="Poptávka", widget=forms.Select(), required=False)
    radius = forms.IntegerField(label="Radius v km od poptávky", initial=50, required=False,
                                help_text="Výpočet blízkých nabídek se projeví pouze po vybrání konkrétní poptávky.")
    offers_only = forms.BooleanField(label="Pouze nabídky", required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.word = get_words()
        if self.word:
            self.word.insert(0, ['', '----------'])
            self.fields['word'].widget.choices = self.word

        self.demand = get_demands()
        if self.demand:
            self.demand.insert(0, ['', '----------'])
            self.fields['demand'].widget.choices = self.demand
