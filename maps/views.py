from django.shortcuts import render
from shopping.elk import get_all_elk, filter_by_word_elk, ELASTICSEARCH_CLIENT

from portal.models import Demand, Offer
from portal.serializers import DemandSerializer, OfferSerializer
import json
from .forms import MapForm, MapElkForm
# from data_mining.elk import ELASTICSEARCH_CLIENT, get_all_elk, filter_by_word_elk

import pyproj as proj
from shapely import geometry

# Create your views here.

# projections setup
crs_wgs = proj.Proj('epsg:3034')  # assuming you're using WGS84 geographic https://epsg.io/ espg:3034 nebo 3035


def basic_map(request):
    o_list = Offer.objects.all()
    count_o = len(o_list)
    serializer_o = OfferSerializer(o_list, many=True)

    d_list = Demand.objects.all()
    count_d = len(d_list)
    serializer_d = DemandSerializer(d_list, many=True)

    points_o_no_lonlat = []
    count_o_no_loc = len(points_o_no_lonlat)
    demand_no_latlon = False
    demand_id = None

    if request.method == "POST":
        form = MapForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data["word"]
            demand = form.cleaned_data["demand"]
            if form.cleaned_data["radius"]:
                radius = form.cleaned_data["radius"] * 1000
            else:
                radius = 10000000
            offers_only = form.cleaned_data["offers_only"]
            if word:
                o_list = Offer.objects.filter(word=word.id)
            else:
                o_list = Offer.objects.filter()
            points_o_no_lonlat = []
            for offer in o_list:
                if offer.locality.coordinates_LON is None or offer.locality.coordinates_LAT is None:
                    points_o_no_lonlat.append(offer)
            count_o_no_loc = len(points_o_no_lonlat)
            if offers_only:
                d_list = []
            else:
                if demand:
                    d_list = Demand.objects.filter(id=demand.id)
                    dem = d_list[0]
                    demand_id = dem.id
                    if dem.locality.coordinates_LON is None or dem.locality.coordinates_LAT is None:
                        demand_no_latlon = True
                    else:
                        o_list = Offer.objects.filter(word=dem.word.id)
                        point_d = [dem.locality.coordinates_LON, dem.locality.coordinates_LAT]
                        point_d = geometry.Point(crs_wgs(point_d[0], point_d[1]))
                        points_o = []
                        points_o_no_lonlat = []
                        for offer in o_list:
                            point_o = [offer.locality.coordinates_LON, offer.locality.coordinates_LAT]
                            if offer.locality.coordinates_LON is None or offer.locality.coordinates_LAT is None:
                                points_o_no_lonlat.append(offer)
                            else:
                                x, y = crs_wgs(point_o[0], point_o[1])
                                point_o = geometry.Point(x, y)
                                if point_o.distance(point_d) < radius:
                                    points_o.append(offer)
                        o_list = points_o
                        count_o_no_loc = len(points_o_no_lonlat)
                elif word and demand is None:
                    d_list = Demand.objects.filter(word=word.id)
                else:
                    d_list = Demand.objects.filter()
            count_d = len(d_list)
            serializer_d = DemandSerializer(d_list, many=True)
            count_o = len(o_list)
            serializer_o = OfferSerializer(o_list, many=True)
    else:
        form = MapForm()

    return render(request, "maps/basic_map.html", context={'d_json': json.dumps(serializer_d.data),
                                                           'o_json': json.dumps(serializer_o.data),
                                                           "form": form, "count_d": count_d, "count_o": count_o,
                                                           "offers_no_lonlat": points_o_no_lonlat,
                                                           "count_o_no_loc": count_o_no_loc,
                                                           "demand_no_latlon": demand_no_latlon,
                                                           "demand_id": demand_id})


def basic_elk_map(request):
    form = MapElkForm(None)

    o_list = get_all_elk("krilog-offer")["results"]
    count_o = get_all_elk("krilog-offer")["count"]

    d_list = get_all_elk("krilog-demand")["results"]
    count_d = get_all_elk("krilog-demand")["count"]

    points_o_no_lonlat = []
    count_o_no_loc = len(points_o_no_lonlat)
    demand_no_latlon = False
    demand_id = None

    if request.method == "POST":
        form = MapElkForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data["word"]
            demand = form.cleaned_data["demand"]
            if form.cleaned_data["radius"]:
                radius = form.cleaned_data["radius"] * 1000
            else:
                radius = 10000000
            offers_only = form.cleaned_data["offers_only"]
            if word:
                o_list = filter_by_word_elk("krilog-offer", word)["results"]
            else:
                o_list = get_all_elk("krilog-offer")["results"]
            points_o_no_lonlat = []
            for offer in o_list:
                if offer["locality"]["coordinates_LON"] is None or offer["locality"]["coordinates_LAT"] is None:
                    points_o_no_lonlat.append(offer)
            count_o_no_loc = len(points_o_no_lonlat)
            if offers_only:
                d_list = []
            else:
                if demand:
                    dem = ELASTICSEARCH_CLIENT.get(index="krilog-demand", id=demand)["_source"]
                    d_list = [dem]
                    if dem["locality"]["coordinates_LON"] is None or dem["locality"]["coordinates_LAT"] is None:
                        demand_no_latlon = True
                    else:
                        o_list = filter_by_word_elk("krilog-offer", dem["word"]["id"])["results"]
                        point_d = [dem["locality"]["coordinates_LON"], dem["locality"]["coordinates_LAT"]]
                        point_d = geometry.Point(crs_wgs(point_d[0], point_d[1]))
                        points_o = []
                        points_o_no_lonlat = []
                        for offer in o_list:
                            point_o = [offer["locality"]["coordinates_LON"], offer["locality"]["coordinates_LAT"]]
                            if (offer['locality']['coordinates_LON'] is None) or \
                                    (offer['locality']['coordinates_LAT'] is None):
                                points_o_no_lonlat.append(offer)
                            else:
                                x, y = crs_wgs(point_o[0], point_o[1])
                                point_o = geometry.Point(x, y)
                                if point_o.distance(point_d) < radius:
                                    points_o.append(offer)
                        o_list = points_o
                        count_o_no_loc = len(points_o_no_lonlat)
                elif word and demand is None:
                    d_list = filter_by_word_elk("krilog-offer", word)["results"]
                else:
                    d_list = get_all_elk("krilog-demand")["results"]

            count_d = len(d_list)
            # serializer_d = DemandSerializer(d_list, many=True)
            count_o = len(o_list)
            # serializer_o = OfferSerializer(o_list, many=True)

    return render(
        request,
        'maps/basic_map.html',
        context={
            'd_json': json.dumps(d_list),
            'o_json': json.dumps(o_list),
            "form": form, "count_d": count_d, "count_o": count_o,
            "offers_no_lonlat": points_o_no_lonlat,
            "count_o_no_loc": count_o_no_loc,
            "demand_no_latlon": demand_no_latlon,
            "demand_id": demand_id})
