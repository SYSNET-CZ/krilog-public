import json
import uuid
from datetime import datetime

import openpyxl
import stanza
from django import db
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, TemplateView
from elasticsearch import ApiError, NotFoundError
from shopping.elk import ELASTICSEARCH_CLIENT, get_all_elk, filter_by_source_elk, filter_by_word_and_source_elk
from shopping.preprocess import clean_address_coords, get_address, twitter_offer_mining, strip_accents
from shopping.scripts import sbazar_one_word, elk_sbazar_one_word, bazos_one_word

from . import models
from .forms import TypeForm, WordForm, TweetSearchForm, SbazarFilterForm, DemandForm, LocalityForm, FileForm, \
    SbazarElkFilterForm
from .models import Word, SALE_RELATED_WORDS, MEDICAL_RELATED_WORDS, CURRENCY, Offer, Demand, AdminText, \
    Locality
from .serializers import DemandSerializer, OfferSerializer, WordSerializer

sale_words = " OR ".join(SALE_RELATED_WORDS)
medical_words = " OR ".join(MEDICAL_RELATED_WORDS)
currency_words = " OR ".join(CURRENCY)


# Create your views here.


def new_type(request):
    if request.method == "POST":
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('portal:home'))
        else:
            form = TypeForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('portal:home'))
    else:
        form = TypeForm()
    return render(request, "portal/new_type.html", context={'form': form})


def new_word(request):
    if request.method == "POST":
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('portal:word_list'))
        else:
            form = WordForm(request.POST)
            form_type = TypeForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('portal:word_list'))
            if form_type.is_valid():
                form_type.save()
                return HttpResponseRedirect(reverse('portal:new_word'))
    else:
        form = WordForm()
        form_type = TypeForm()
    return render(request, "portal/new_word.html", context={'form': form, 'form_type': form_type})


def check_clean_create_locality(pid, region="", city="", street=""):
    if city is None:
        city = ""
    if street is None:
        street = ""
    address_orig = [region, city, street]
    locality = Locality.objects.filter(id=pid)
    if not locality:
        locality = Locality.objects.filter(region=address_orig[0], city=address_orig[1], street=address_orig[2])
    if locality and (locality[0].coordinates_LAT not in [None, ""] and locality[0].coordinates_LON not in [None, ""]):
        locality = locality[0]
    else:
        lat, lon, city = clean_address_coords(region=region, city=city, street=street)

        if locality and (locality[0].coordinates_LAT in [None, ""] or locality[0].coordinates_LON in [None, ""]) and \
                lon is not None and lat is not None:
            Locality.objects.filter(region=address_orig[0], city=address_orig[1], street=address_orig[2]).update(
                coordinates_LAT=lat, coordinates_LON=lon)
            locality = Locality.objects.filter(region=address_orig[0], city=address_orig[1], street=address_orig[2])[0]
            if not locality:
                locality = Locality.objects.get(id=pid)
                if not locality:
                    locality, created = Locality.objects.get_or_create(
                        id=pid, region=address_orig[0], city=address_orig[1],
                        street=address_orig[2], coordinates_LAT=lat, coordinates_LON=lon)
        elif locality and (lon is None) and (lat is None):
            locality, created = Locality.objects.get_or_create(
                id=pid, region=address_orig[0], city=address_orig[1], street=address_orig[2])
        else:
            locality, created = Locality.objects.get_or_create(
                id=pid, region=address_orig[0], city=address_orig[1],
                street=address_orig[2], coordinates_LAT=lat, coordinates_LON=lon)
    return locality


def check_coordinates_and_find_location(pid, lat, lon):
    locality = Locality.objects.filter(coordinates_LAT=lat, coordinates_LON=lon)
    if locality and locality[0].city not in [None, ""]:
        locality = locality[0]
    else:
        a = get_address(lat, lon)
        if locality and locality[0].city in [None, ""]:
            Locality.objects.filter(coordinates_LAT=lat, coordinates_LON=lon).update(city=a)
            locality = Locality.objects.filter(coordinates_LAT=lat, coordinates_LON=lon)[0]
        else:
            locality = Locality.objects.create(
                id=pid, region="", city=a, street="", coordinates_LAT=lat, coordinates_LON=lon)
    return locality


def new_demand(request):
    if request.method == "POST":
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('portal:home'))
        else:
            form = DemandForm(request.POST)
            form_loc = LocalityForm(request.POST)
            if form.is_valid() and form_loc.is_valid():
                region = form_loc.cleaned_data["region"]
                city = form_loc.cleaned_data["city"]
                street = form_loc.cleaned_data["street"]
                pid = uuid.uuid4()
                locality = check_clean_create_locality(pid=pid, region=region, city=city, street=street)
                Demand.objects.create(
                    id=uuid.uuid4(),
                    word=form.cleaned_data["word"],
                    created=datetime.now(),
                    quantity=form.cleaned_data["quantity"],
                    units="ks",
                    organization=form.cleaned_data["organization"],
                    locality=locality
                )
                return HttpResponseRedirect(reverse('portal:demand_list'))
    else:
        form = DemandForm()
        form_loc = LocalityForm()
    return render(request, "portal/new_demand.html", context={'form': form, 'form_loc': form_loc})


def edit_demand(request, identifier):
    if request.method == "POST":
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('portal:demand_list'))
        else:
            form = DemandForm(request.POST)
            form_loc = LocalityForm(request.POST)
            if form.is_valid() and form_loc.is_valid():
                region = form_loc.cleaned_data["region"]
                city = form_loc.cleaned_data["city"]
                street = form_loc.cleaned_data["street"]
                locality = check_clean_create_locality(pid=identifier, region=region, city=city, street=street)
                Demand.objects.filter(id=identifier).update(
                    word=form.cleaned_data["word"],
                    quantity=form.cleaned_data["quantity"],
                    units="ks",
                    organization=form.cleaned_data["organization"],
                    active=form.cleaned_data["active"],
                    locality=locality)
                return HttpResponseRedirect(reverse('portal:demand_list'))
    else:
        dem = Demand.objects.get(id=identifier)
        form = DemandForm(instance=dem)
        form_loc = LocalityForm(instance=dem.locality)
    return render(request, "portal/edit_demand.html", context={'form': form, 'form_loc': form_loc,
                                                               "identifier": identifier})


def deactivate_demand(request, identifier):
    Demand.objects.filter(id=identifier).update(active=False)
    return HttpResponseRedirect(reverse('portal:demand_list'))


def new_demand_plus(request):  # https://pythoncircle.com/post/591/how-to-upload-and-process-the-excel-file-in-django/
    if request.method == "POST":
        if "cancel" in request.POST:
            return HttpResponseRedirect(reverse('portal:home'))
        else:
            form = FileForm(request.POST, request.FILES)
            if form.is_valid():
                # data = request.FILES['file_upload']
                # filename = form.cleaned_data['filename']
                data = form.save()
                wb = openpyxl.load_workbook(data.file_upload)
                worksheet = wb["List1"]
                excel_data = list()
                for row in worksheet.iter_rows():
                    row_data = list()
                    for cell in row:
                        row_data.append(str(cell.value))
                    excel_data.append(row_data)
                # header = excel_data[0]
                nlp = stanza.Pipeline("cs")
                new_data = excel_data[1:len(excel_data)]
                for row in new_data:
                    pid = uuid.uuid4()
                    word = Word.objects.filter(name=row[2]).first()
                    if row[4] == "":
                        quantity = 0
                    elif row[4] == "None":
                        quantity = 0
                    elif row[4] is not None:
                        quantity = int(row[4])
                    else:
                        quantity = 0
                    locality = None
                    if quantity > 0:
                        if row[1] != "":
                            if row[1] == "None":
                                doc = nlp(row[0]).sentences[0].to_dict()
                                locality = []
                                for item in doc:
                                    if item["upos"] == "PROPN":
                                        locality.append(item["lemma"])
                                if locality:
                                    locality = " ".join(locality)
                                else:
                                    locality = ""
                            elif len(row[1].lstrip().rstrip()) > 0:
                                locality = row[1]
                        locality = check_clean_create_locality(pid=uuid.uuid4(), city=locality)
                        try:
                            Demand.objects.create(
                                id=pid,
                                word=word,
                                created=datetime.now(),
                                quantity=row[4],
                                units="ks",
                                organization=row[0],
                                locality=locality
                            )
                        except db.Error:
                            print("nepovedlo se vztvořit objekt Demand")
                return HttpResponseRedirect(reverse('portal:demand_list'))
    else:
        form = FileForm()
    return render(request, "portal/new_demand_plus.html", context={'form': form})


class TypeListView(ListView):
    model = models.Type
    paginate_by = 10
    context_object_name = 'object_list'
    template_name = 'portal/word_list.html'


def word_list(request):
    w_list = Word.objects.all()
    return render(request, "portal/word_list.html", context={'w_list': w_list})


def demand_list(request):
    d_list = Demand.objects.all()
    count = len(d_list)
    return render(request, "portal/demand_list.html", context={'d_list': d_list, "count": count})


def offer_list(request):
    o_list = Offer.objects.all()
    count = len(o_list)
    return render(request, "portal/offer_list.html", context={'o_list': o_list, "count": count})  # , "form": form


def offer_elk_list(request):
    response = ELASTICSEARCH_CLIENT.search(
        index="krilog-offer",
        body={
            "query": {
                "match_all": {}
            },
            "size": 10000

        }
    )

    o_list = [offer["_source"] for offer in response['hits']['hits']]
    for offer in o_list:
        try:
            offer["created"] = offer["created"][0:10]
        except [TypeError, ValueError, IndexError]:
            offer["created"] = None

    count = response['hits']['total']['value']

    return render(request, "portal/elk_offer_list.html", context={'o_list': o_list, "count": count})  # , "form": form


class HomeView(TemplateView):
    template_name = 'portal/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['text'] = AdminText.objects.first()
        return context


def get_word_declension(word):
    queryset = Word.objects.filter(name=word)
    word_decl = ""
    if [w.declention for w in queryset] is not None:
        word_decl = " OR ".join([w.declention for w in queryset][0].split(", "))
        word_decl_re = "|".join([w.declention for w in queryset][0].split(", "))
    else:
        word_decl_re = ""
    return word_decl, word_decl_re


def twitter_synchro(count_per_word, include_word_context):
    offers_all = []
    words = Word.objects.all()
    for w in words:
        word = w.name
        word_dict = word
        # word_id = w.id
        word_decl_re = ""
        if w.declention is not None:
            word_decl = " OR ".join(w.declention.split(", "))
            word_decl_re = "|".join(w.declention.split(", "))
            word = f"({word} OR {word_decl})"
        else:
            word = f"({word})"
        if include_word_context:
            word_context = f"({sale_words}) ({currency_words}) ({medical_words})"
            q = f"{word} {word_context} -filter:retweets"
        else:
            q = f"{word} -filter:retweets"
        offers, cols, count_results = twitter_offer_mining(q=q, lang="cs", count=count_per_word, word=word_dict,
                                                           word_decl=word_decl_re, search="")
        if offers:
            for offer in offers:
                queryset_offer = Offer.objects.filter(id=offer["id"]).first()
                if not queryset_offer:
                    locality = check_clean_create_locality(pid=offer["id"], region="", city=offer["locality"],
                                                           street="")
                    # locality = Locality.objects.get(id=offer["locality"])

                    Offer.objects.create(id=offer["id"], url=offer["url"], name_offer="",
                                         name_user=offer["name_user"], word=w, search="",
                                         created=offer["created"], fulltext=offer["fulltext"],
                                         locality=locality, price=offer["price"],
                                         currency=offer["currency"], quantity=offer["quantity"],
                                         units=offer["units"], source="Twitter")
            offers_all.append(offers)
    return offers_all


def tweet_list(request):
    form = TweetSearchForm()
    text = AdminText.objects.first()

    offers_list = Offer.objects.filter(source="Twitter")
    context = []
    cols = []
    count_results = 0
    if request.method == "POST":
        if "synchronize" in request.POST:
            twitter_synchro(count_per_word=100, include_word_context=True)
        elif "save" not in request.POST:
            form = TweetSearchForm(request.POST)
            if form.is_valid():
                # word_id = None
                if form.cleaned_data["word"]:
                    word = form.cleaned_data["word"].name
                    # word_id = form.cleaned_data["word"].id
                    word_dict = word
                    queryset = Word.objects.filter(name=word)
                    word_decl_re = ""
                    if [w.declention for w in queryset] != [None]:
                        word_decl = " OR ".join([w.declention for w in queryset][0].split(", "))
                        word_decl_re = "|".join([w.declention for w in queryset][0].split(", "))
                        word = f"({word} OR {word_decl})"
                    else:
                        word = f"({word})"
                else:
                    word = ""
                    word_dict = ""
                    word_decl_re = ""
                search = form.cleaned_data["search"]
                if form.cleaned_data["sale_words"] and form.cleaned_data["medical_words"]:
                    word_context = f"({sale_words}) ({currency_words}) ({medical_words})"
                elif form.cleaned_data["sale_words"] and form.cleaned_data["medical_words"] is False:
                    word_context = f"({sale_words}) ({currency_words}))"
                elif form.cleaned_data["sale_words"] is False and form.cleaned_data["medical_words"]:
                    word_context = f"(({medical_words})"
                else:
                    word_context = ""

                if word != "":
                    q = f"{word} {word_context} {search} -filter:retweets"
                else:
                    q = f"{word_context} {search} -filter:retweets"
                count = form.cleaned_data["count"]
                lang = form.cleaned_data["lang"]
                context, cols, count_results = twitter_offer_mining(q=q, lang=lang, count=count, word=word_dict,
                                                                    word_decl=word_decl_re,
                                                                    search=search)
                cols = ["url", "name_user", "word", "search", "created", "fulltext", "locality", "price", "currency",
                        "quantity", "units"]
                request.session["offers_dict"] = context
                for offer in context:
                    locality = check_clean_create_locality(pid=offer["id"], region="", city=offer["locality"],
                                                           street="")
                    # locality = Locality.objects.get(id=offer["locality"])
                    offer["locality_city"] = locality.city
                    offer["LAT"] = locality.coordinates_LAT
                    offer["LON"] = locality.coordinates_LON
        elif "save" in request.POST and "offers_dict" in request.session:
            offers_dict = request.session["offers_dict"]
            for offer in offers_dict:
                queryset_offer = Offer.objects.filter(id=offer["id"]).first()
                if not queryset_offer:
                    locality = Locality.objects.get(id=offer["locality"])
                    word = Word.objects.filter(name=offer["word"]).first()
                    Offer.objects.create(id=offer["id"], url=offer["url"], name_offer=offer["name_offer"],
                                         name_user=offer["name_user"], word=word, search=offer["search"],
                                         created=offer["created"], fulltext=offer["fulltext"],
                                         locality=locality, price=offer["price"],
                                         currency=offer["currency"], quantity=offer["quantity"],
                                         units=offer["units"], source=offer["source"])
    return render(request, "portal/tweet_search.html", context={'form': form, "context": context, "cols": cols,
                                                                "count": count_results, "offers_list": offers_list,
                                                                "text": text})


def get_word_context(word_id):
    word_object = Word.objects.get(id=word_id)
    exp = word_object.name
    blacklist = [res.name for res in word_object.restricted_words.all()]
    wordcore = [word_object.word_core, strip_accents(word_object.word_core.lower())]
    return exp, blacklist, wordcore, word_object


def get_and_save_offers_sbazar(word_id, exp, blacklist, wordcore, word_object, word_decl, word_decl_re,
                               delete_existing=False, source="Sbazar"):
    if delete_existing:
        Offer.objects.filter(word=word_id, source=source).delete()
    offers = sbazar_one_word(exp, blacklist, wordcore, word_decl, word_decl_re)
    for offer in offers:
        # podmínku mazání ponechat, i když je nahoře delete všeho - jeden inzerát se může najít vícekrát pro různé
        # výrazy a docházelo by k jeho multiplikaci
        offer_exists = Offer.objects.filter(id=offer["id"])
        if offer_exists:
            Offer.objects.filter(id=offer["id"]).delete()
        locality = check_clean_create_locality(pid=offer["locality"]["pid"], region=offer["locality"]["region"],
                                               city=offer["locality"]["city"], street=offer["locality"]["street"])
        Offer.objects.create(id=offer["id"], url=offer["url"], name_offer=offer["name_offer"],
                             name_user=offer["name_user"], word=word_object, search="",
                             created=offer["created"], fulltext=offer["fulltext"],
                             locality=locality, price=offer["price"],
                             currency=offer["currency"], quantity=offer["quantity"],
                             units=offer["units"], source=offer["source"])


def sbazar_synchro():
    # smažu všechny sbazarové inzeráty v db - mohou být neaktuální
    Offer.objects.filter(source="Sbazar").delete()
    searched_expressions = Word.objects.all()
    list_of_search = [w.id for w in searched_expressions]
    for word_id in list_of_search:
        exp, blacklist, wordcore, word_object = get_word_context(word_id=word_id)
        word_decl, word_decl_re = get_word_declension(exp)
        get_and_save_offers_sbazar(delete_existing=False, word_id=word_id, exp=exp, blacklist=blacklist,
                                   wordcore=wordcore, word_object=word_object, word_decl=word_decl,
                                   word_decl_re=word_decl_re)
    offers_list = Offer.objects.filter(source="Sbazar")
    return offers_list


def sbazar_elk_synchro():
    # smažu všechny sbazarové inzeráty v db - mohou být neaktuální
    """
    offers_to_delete = filter_by_source_elk("Sbazar")
    for offer_old in offers_to_delete:
        es.delete(index="krilog-offer", id=offer_old["id"])
        print("Offer s id {} byl vymazán z elk".format(offer_old["id"]))
    """

    searched_expressions = get_all_elk("krilog-word")["results"]
    list_of_search = [w["id"] for w in searched_expressions]
    for word_id in list_of_search:
        exp, blacklist, wordcore, word_object = get_word_context(word_id=word_id)
        word_decl, word_decl_re = get_word_declension(exp)
        elk_sbazar_one_word(word_id, word_decl, word_decl_re, delete_existing=False)

    offers_list = filter_by_source_elk("Sbazar")
    return offers_list


def sbazar_list(request):
    form = SbazarFilterForm(None)

    # ukladani inzeratu na tlacitko
    offers_list = None
    if request.method == "POST":
        if "synchronize" in request.POST:
            offers_list = sbazar_synchro()

        # nacteni existujicich nabidek
        elif "filter" in request.POST:
            form = SbazarFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"].name
                queryset = Word.objects.filter(name=searched_word)
                word_id = [w.pk for w in queryset][0]
                offers_list = Offer.objects.filter(word=word_id, source="Sbazar")

        # synchro jednoho vyrazu - pro pridavani
        elif "synchro_choose" in request.POST:
            form = SbazarFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"].name
                queryset = Word.objects.filter(name=searched_word)
                word_id = [w.pk for w in queryset][0]
                exp, blacklist, wordcore, word_object = get_word_context(word_id=word_id)
                word_decl, word_decl_re = get_word_declension(exp)
                get_and_save_offers_sbazar(delete_existing=True, word_id=word_id, exp=exp, blacklist=blacklist,
                                           wordcore=wordcore, word_object=word_object, word_decl=word_decl,
                                           word_decl_re=word_decl_re)
                offers_list = Offer.objects.filter(source="Sbazar", word=word_id)
    else:
        offers_list = Offer.objects.filter(source="Sbazar")
    text = AdminText.objects.first()
    return render(request, "portal/sbazar_list.html", context={"offers_list": offers_list, "form": form,
                                                               "headline": "Sbazar", "text": text})


def sbazar_elk_list(request):
    form = SbazarElkFilterForm(None)

    # ukladani inzeratu na tlacitko
    offers_list = None
    if request.method == "POST":
        if "synchronize" in request.POST:
            offers_list = sbazar_elk_synchro()

        # nacteni existujicich nabidek
        elif "filter" in request.POST:
            form = SbazarElkFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"]
                offers_list = filter_by_word_and_source_elk(searched_word, "Sbazar")

        # synchro jednoho vyrazu - pro pridavani
        elif "synchro_choose" in request.POST:
            form = SbazarElkFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"]
                offers_list = elk_sbazar_one_word(word_id=searched_word, word_decl=None, word_decl_re=None, delete_existing=True)
    else:
        offers_list = filter_by_source_elk("Sbazar")

    text = AdminText.objects.first()
    return render(request, "portal/sbazar_list.html", context={"offers_list": offers_list, "form": form,
                                                               "headline": "Sbazar", "text": text})


def get_and_save_offers_bazos(word_id, exp, blacklist, wordcore, word_object, word_decl, word_decl_re,
                              delete_existing=False, source="Bazoš"):
    if delete_existing:
        Offer.objects.filter(word=word_id, source=source).delete()
    offers = bazos_one_word(exp, blacklist, wordcore, word_decl, word_decl_re)
    for offer in offers:
        # podmínku mazání ponechat, i když je nahoře delete všeho - jeden inzerát se může najít vícekrát pro různé
        # výrazy a docházelo by k jeho multiplikaci
        offer_exists = Offer.objects.filter(id=offer["id"])
        if offer_exists:
            Offer.objects.filter(id=offer["id"]).delete()
        locality = check_coordinates_and_find_location(pid=offer["locality"]["pid"],
                                                       lat=offer["locality"]["lat"],
                                                       lon=offer["locality"]["lon"])
        Offer.objects.create(id=offer["id"], url=offer["url"], name_offer=offer["name_offer"],
                             name_user=offer["name_user"], word=word_object, search="",
                             created=offer["created"], fulltext=offer["fulltext"],
                             locality=locality, price=offer["price"],
                             currency=offer["currency"], quantity=offer["quantity"],
                             units=offer["units"], source=offer["source"])


def bazos_synchro():
    # smažu bazošové inzeráty v db - mohou být neaktuální
    Offer.objects.filter(source="Bazoš").delete()
    searched_expressions = Word.objects.all()
    list_of_search = [w.id for w in searched_expressions]
    for word_id in list_of_search:
        exp, blacklist, wordcore, word_object = get_word_context(word_id=word_id)
        word_decl, word_decl_re = get_word_declension(exp)
        get_and_save_offers_bazos(delete_existing=False, word_id=word_id, exp=exp, blacklist=blacklist,
                                  wordcore=wordcore, word_object=word_object, word_decl=word_decl,
                                  word_decl_re=word_decl_re)
    offers_list = Offer.objects.filter(source="Bazoš")
    return offers_list


def bazos_list(request):
    form = SbazarFilterForm(None)

    # ukladani inzeratu na tlacitko
    offers_list = None
    if request.method == "POST":
        if "synchronize" in request.POST:
            offers_list = bazos_synchro()

        # nacteni existujicich nabidek
        elif "filter" in request.POST:
            form = SbazarFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"].name
                queryset = Word.objects.filter(name=searched_word)
                word_id = [w.pk for w in queryset][0]
                offers_list = Offer.objects.filter(word=word_id, source="Bazoš")

        # synchro jednoho vyrazu - pro pridavani
        elif "synchro_choose" in request.POST:
            form = SbazarFilterForm(request.POST)
            if form.is_valid():
                searched_word = form.cleaned_data["word"].name
                queryset = Word.objects.filter(name=searched_word)
                word_id = [w.pk for w in queryset][0]
                exp, blacklist, wordcore, word_object = get_word_context(word_id=word_id)
                word_decl, word_decl_re = get_word_declension(exp)
                get_and_save_offers_bazos(delete_existing=True, word_id=word_id, exp=exp, blacklist=blacklist,
                                          wordcore=wordcore, word_object=word_object, word_decl=word_decl,
                                          word_decl_re=word_decl_re)
                offers_list = Offer.objects.filter(word=word_id, source="Sbazar")
    else:
        offers_list = Offer.objects.filter(source="Bazoš")

    text = AdminText.objects.first()
    return render(request, "portal/sbazar_list.html", context={"offers_list": offers_list, "form": form,
                                                               "headline": "Bazoš", "text": text})


def elk_offers_synchro():
    # es = create_es_client()
    # es.indices.delete(index='krilog-offer', ignore=[400, 404]) #smaže celý index - pouze pro extrémní případy, např. přetypování pole
    o_list = Offer.objects.all()
    serializer_o = OfferSerializer(o_list, many=True)
    list_of_offers_str = json.dumps(serializer_o.data)
    list_of_offers = json.loads(list_of_offers_str)

    if len(list_of_offers) > 0 and ELASTICSEARCH_CLIENT:
        # seznam offers existujících v ELK = vytvoreni seznamu pro smazani
        try:
            existing_offers = ELASTICSEARCH_CLIENT.search(
                index="krilog-offer",
                body={
                    "query": {
                        "match_all": {}
                    },
                    "_source": ["id"],
                    "size": 10000
                },
            )
            offers_ids_elk = [hit['_source']['id'] for hit in existing_offers['hits']['hits']]
        except ApiError:
            offers_ids_elk = []

        # offer zkusim aktualizovat (jiz existuje), pokud to neprojde, tak ji zalozim (zatim neexistuje)
        for offer in list_of_offers:
            try:
                ELASTICSEARCH_CLIENT.update(
                    index="krilog-offer",
                    id=offer["id"],
                    body={"doc": offer}
                )
                print("Proběhla aktualizace Offer s id {}".format(offer["id"]))
                # aktualizovany inzerat smazu se seznamu na smazani
                if offer["id"] in offers_ids_elk:
                    offers_ids_elk.remove(offer["id"])

            except NotFoundError:
                try:
                    ELASTICSEARCH_CLIENT.index(
                        index="krilog-offer",
                        id=offer["id"],
                        op_type="create",
                        # body=offer,
                        document=offer
                    )
                    print("Byla vytvorena nova Offer s id {}".format(offer["id"]))
                except ApiError:
                    print("Nepodařilo se vytvořit novou Offer s id {}".format(offer["id"]))
            except ApiError:
                print("Nepodařilo se aktualizovat ani založit Offer s id {}".format(offer["id"]))

        # vymazani inzeratu, ktere zbyly po aktualizaci (tj. uz nejsou na trzisti), z elastiku
        if len(offers_ids_elk) > 0:
            for offer_old_id in offers_ids_elk:
                ELASTICSEARCH_CLIENT.delete(index="krilog-offer", id=offer_old_id)
                print("Offer s id {} byl vymazán z elk".format(offer_old_id))

    return True


def elk_demands_synchro():
    # es = create_es_client()

    d_list = Demand.objects.all()
    serializer_d = DemandSerializer(d_list, many=True)
    list_of_demands_str = json.dumps(serializer_d.data)
    list_of_demands = json.loads(list_of_demands_str)

    if len(list_of_demands) > 0 and ELASTICSEARCH_CLIENT:
        # seznam demands existujících v ELK = vytvoreni seznamu pro smazani
        try:
            existing_demands = ELASTICSEARCH_CLIENT.search(
                index="krilog-demand",
                body={
                    "query": {
                        "match_all": {}
                    },
                    "_source": ["id"],
                    "size": 10000
                },
            )
            demands_ids_elk = [hit['_source']['id'] for hit in existing_demands['hits']['hits']]
        except ApiError:
            demands_ids_elk = []

        for demand in list_of_demands:
            try:
                ELASTICSEARCH_CLIENT.update(
                    index="krilog-demand",
                    id=demand["id"],
                    body={"doc": demand}
                )
                print("Proběhla aktualizace Demand s id {}".format(demand["id"]))
                # aktualizovanou poptavku smazu se seznamu na smazani
                if demand["id"] in demands_ids_elk:
                    demands_ids_elk.remove(demand["id"])
            except NotFoundError:
                try:
                    ELASTICSEARCH_CLIENT.index(
                        index="krilog-demand",
                        id=demand["id"],
                        op_type="create",
                        # body=demand,
                        document=demand
                    )
                    print("Byla vytvorena nova Demand s id {}".format(demand["id"]))
                except ApiError:
                    print("Nepodařilo se vytvořit novou Demand s id {}".format(demand["id"]))
            except ApiError:
                print("Nepodařilo se aktualizovat ani založit Demand s id {}".format(demand["id"]))

        # vymazani poptavek, ktere zbyly po aktualizaci (tj. uz nejsou v sqlitu)
        if len(demands_ids_elk) > 0:
            for demand_old_id in demands_ids_elk:
                ELASTICSEARCH_CLIENT.delete(index="krilog-demand", id=demand_old_id)
                print("Demand s id {} byl vymazán z elk".format(demand_old_id))
    return True


def elk_words_synchro():
    # es = create_es_client()
    word_list_internal = Word.objects.all()
    serializer_w = WordSerializer(word_list_internal, many=True)
    list_of_words_str = json.dumps(serializer_w.data)
    list_of_words = json.loads(list_of_words_str)

    if len(list_of_words) > 0 and ELASTICSEARCH_CLIENT:
        # seznam words existujících v ELK = vytvoreni seznamu pro smazani
        try:
            existing_words = ELASTICSEARCH_CLIENT.search(
                index="krilog-word",
                body={
                    "query": {
                        "match_all": {}
                    },
                    "_source": ["id"],
                    "size": 10000
                },
            )
            words_ids_elk = [hit['_source']['id'] for hit in existing_words['hits']['hits']]
        except ApiError:
            words_ids_elk = []

        for word in list_of_words:
            try:
                ELASTICSEARCH_CLIENT.update(
                    index="krilog-word",
                    id=word["id"],
                    body={"doc": word}
                )
                print("Proběhla aktualizace Word s id {}".format(word["id"]))
                if word["id"] in words_ids_elk:
                    words_ids_elk.remove(word["id"])
            except NotFoundError:
                try:
                    ELASTICSEARCH_CLIENT.index(
                        index="krilog-word",
                        id=word["id"],
                        op_type="create",
                        # body=word,
                        document=word
                    )
                    print("Bylo vytvoreno nove Word s id {}".format(word["id"]))
                except ApiError:
                    print("Nepodařilo se vytvořit nove Word s id {}".format(word["id"]))
            except ApiError:
                print("Nepodařilo se aktualizovat ani založit Word s id {}".format(word["id"]))

        # vymazani poptavek, ktere zbyly po aktualizaci (tj. uz nejsou v sqlitu)
        if len(words_ids_elk) > 0:
            for word_old_id in words_ids_elk:
                ELASTICSEARCH_CLIENT.delete(index="krilog-word", id=word_old_id)
                print("Word s id {} byl vymazán z elk".format(word_old_id))

    return True


def elastic_synchro_view(request):
    if request.method == "POST":
        if "offer" in request.POST:
            elk_offers_synchro()

        if "demand" in request.POST:
            elk_demands_synchro()

        if "word" in request.POST:
            elk_words_synchro()

    return render(request, "portal/elastic_synchro.html", context={})
