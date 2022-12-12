from django.forms import ModelForm
from django import forms
from shopping.elk import get_words

from .models import Word, Demand, Type, Locality, UploadFile


class TypeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Název'

    class Meta:
        model = Type
        fields = "__all__"


class WordForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Název'
        self.fields['type'].label = 'Typ'
        self.fields['synonyms'].label = 'Synonyma'
        self.fields['family'].label = 'Skupina pojmů'
        self.fields['declention'].label = 'Tvary'
        self.fields['restricted_words'].label = 'Zakázaná slova'
        self.fields['word_core'].label = 'Kořen slova'

    class Meta:
        model = Word
        fields = "__all__"


class DemandForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['word'].label = 'Požadovaná věc'
        self.fields['quantity'].label = 'Množství'
        self.fields['organization'].label = 'Organizace'
        self.fields['active'].label = 'Aktivní'

    class Meta:
        model = Demand
        fields = ["word", "quantity", "organization", "active"]


class LocalityForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['region'].label = 'Kraj'
        self.fields['city'].label = 'Město'
        self.fields['street'].label = 'Ulice a č.p.'

    class Meta:
        model = Locality
        fields = ["region", "city", "street"]


class TweetSearchForm(forms.Form):
    word = forms.ModelChoiceField(label="Hledané slovo", queryset=Word.objects.all(), required=False, blank=True)
    search = forms.CharField(label="Doplňující výraz", max_length=100, required=False)
    medical_words = forms.BooleanField(label="Zdravotnický kontext", initial=True, required=False)
    sale_words = forms.BooleanField(label="Kontext prodeje", initial=True, required=False)
    count = forms.IntegerField(label="Maximální počet výsledků", initial=10, required=False)
    lang = forms.CharField(label="Jazyk příspěvků", initial="cs", required=False)


class SbazarFilterForm(forms.Form):
    word = forms.ModelChoiceField(label="Hledané slovo", queryset=Word.objects.all(), required=True)


class FileForm(forms.ModelForm):
    class Meta:
        model = UploadFile
        fields = '__all__'


SOURCE_CHOICES = [
    ("T", "Twitter"),
    ("S", "sBazar"),
    ("B", "Bazoš")
]


class DemandFilterForm(forms.Form):
    word = forms.ModelChoiceField(label="Hledané slovo", queryset=Word.objects.all(), required=False)
    source = forms.ChoiceField(label="Zdroj", choices=SOURCE_CHOICES, required=False)


class SbazarElkFilterForm(forms.Form):
    word = forms.CharField(label="Hledané slovo", widget=forms.Select(), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.word = get_words()
        if self.word:
            self.word.insert(0, ['', '----------'])
            self.fields['word'].widget.choices = self.word
