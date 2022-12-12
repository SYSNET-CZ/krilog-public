import uuid

import django.db
from django.db import models

# Create your models here.


""" SLOVNIK """
# pro twitter neni treba resit diakritiku a velka mala pismena, sam si to prevadi, jinak
# import string
# string.ascii_lowercase
# import unidecode
# unaccented_string = unidecode.unidecode(accented_string
# nebo vlastnorucne viz https://stackoverflow.com/questions/65833714/how-to-remove-accents-from-a-string-in-python

FAMILY = [
    ("P", "Pandemic"),
    ("F", "Floods")
]

SALE_RELATED_WORDS = [
    "prodám", "prodej", "prodávám", "prodáme", "prodáváme", "nabízím", "nabídka", "nabízíme"
]

MEDICAL_RELATED_WORDS = [
    "zdravotní", "zdravotnictví", "ochranný", "ochranné", "desinfekce", "dezinfekce"
]

CURRENCY = {
    "Kč": ["Kč", "CZK", "kč", "KČ"],
    "EUR": ["Euro", "EUR", "€", "eur", "Eur", "EURO"]
}

UNITS = {
    "ks": ["ks", "kusů", "kusy", "kus", "kusech"]
}


class Type(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class RestrictedWord(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Word(models.Model):
    name = models.CharField(max_length=100)  # primary_key=True,
    type = models.ManyToManyField(Type)
    synonyms = models.ManyToManyField("self", symmetrical=True, blank=True, default="Rouška")
    family = models.CharField(max_length=2, choices=FAMILY, default="P")  # ex. pandemic, floods,...
    declention = models.CharField(max_length=100, blank=True, null=True)
    restricted_words = models.ManyToManyField(RestrictedWord, blank=True)
    word_core = models.CharField(max_length=25, default="")

    def __str__(self):
        return f"{self.name}"


""" NABIDKA A POPTAVKA """


class Locality(models.Model):
    id = models.CharField(primary_key=True, max_length=100, default="1")
    region = models.CharField(max_length=100, blank=True, null=True, default="Hlavní město Praha")
    city = models.CharField(max_length=100, blank=True, null=True, default="Praha")
    street = models.CharField(max_length=100, blank=True, null=True, default="Nová 1")
    coordinates_LAT = models.FloatField(blank=True, null=True)  # , default=50.086855727426276
    coordinates_LON = models.FloatField(blank=True, null=True)  # , default=14.420196124134936

    def __str__(self):
        return f"{self.region}, {self.city}, {self.street}, {self.coordinates_LAT}, {self.coordinates_LON}"


class Offer(models.Model):
    id = models.CharField(primary_key=True, max_length=100)  # id inzeratu
    url = models.CharField(max_length=100)  # odkaz na inzerat
    name_offer = models.CharField(max_length=100, blank=True, null=True)  # nazev inzeratu
    name_user = models.CharField(max_length=100)  # jmeno prodejce
    word = models.ForeignKey(Word, on_delete=models.CASCADE, blank=True, null=True)  # hledani ze slovniku
    search = models.CharField(max_length=100, blank=True, null=True)  # hledany vyraz mimo slovnik
    created = models.DateTimeField()
    price = models.FloatField()
    currency = models.CharField(max_length=10)  # idealne ze slovniku
    quantity = models.IntegerField()
    units = models.CharField(max_length=10)  # idealne ze slovniku
    fulltext = models.CharField(max_length=1000)
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT,
                                 default="1")  # lokality zachovat i při promazání nabídek, aby se nemusely pořád dopočítávat souřadnice
    source = models.CharField(max_length=100, default="Twitter")

    def __str__(self):
        return f"{self.created}, {self.word}, {self.price}, {self.currency}, {self.quantity}, {self.units}, {self.source}"


class Demand(models.Model):
    id = models.CharField(primary_key=True, default=uuid.uuid4, unique=True, max_length=100)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)  # hledani ze slovniku
    created = models.DateTimeField()
    quantity = models.IntegerField()
    units = models.CharField(max_length=10)  # idealne ze slovniku
    organization = models.CharField(max_length=100, blank=True, null=True)
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, default="1")
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.word}, {self.quantity}, {self.units}, {self.organization}"


class UploadFile(models.Model):
    filename = models.CharField(max_length=250)
    file_upload = models.FileField(upload_to='uploads/')

    def __str__(self):
        return self.filename


HOME_TEXT = "Tady bude text o projektu KRILOG."
TWITTER_TEXT = "Twitter je celosvětová sociální síť, která mezi příspěvky obsahuje i nabídky k prodeji, kterých je " \
               "ale v porovnání s ostatními příspěvky na síti minimum.<br> " \
               "Z tohoto důvodu je vyhledávání příspěvků na Twitteru nastaveno jiným způsobem (podrobněji)," \
               " než u inzertních portálů sReality a Bazoš.<br>" \
               " <ul>" \
               "<li>Prohledávání na základě slov ze slovníku nebo ručně zadaných slov.</li>" \
               "<li>Možnost omezení vyhledávání na oblasti se zdravotnickým nebo prodejním kontextem.</li>" \
               "<li>Počet výsledků je defaultně omezen a jazyk nastaven na češtinu.</li>" \
               "</ul>" \
               "Výsledky vyhledávání obsahují málokdy lokalitu, protože nebývá uživateli často uváděna." \
               "Pro podrobnější informace k příspěvku využijte odkaz přímo do Twitteru."
SBAZAR_BAZOS_TEXT = "Aplikace KRILOG vytěžuje z nalezených inzerátů základní údaje, ukládá je pro potřebu dalšího" \
                    "zpracování v rámci této aplikace a odkazuje na inzertní portál." \
                    "<strong>" \
                    "Každou noc probíhá aktualizace inzerátů z portálů Sbazar, Bazoš a sociální sítě Twitter." \
                    "Jsou vyhledávány inzeráty, které obsahují klíčové pojmy (viz Slovník pojmů)." \
                    "</strong>" \
                    "Pro podrobnější informace k příspěvku využijte odkaz přímo do zdroje."


class AdminText(models.Model):
    Home_text = models.TextField(max_length=1000, default=HOME_TEXT)
    Twitter_text = models.TextField(max_length=1000, default=TWITTER_TEXT)
    sBazar_Bazos_text = models.TextField(max_length=1000, default=SBAZAR_BAZOS_TEXT)
