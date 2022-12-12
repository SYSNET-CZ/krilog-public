from rest_framework import serializers
from .models import Demand, Locality, Offer, Word, RestrictedWord, Type

class LocalitySerializer(serializers.ModelSerializer):

  class Meta:
    model = Locality
    fields = "__all__"


class BasicWordSerializer(serializers.ModelSerializer):

    class Meta:
        model = Word
        fields = ["id", "name"]


class RestrictedWordSerializer(serializers.ModelSerializer):
    class Meta:
      model = RestrictedWord
      fields ="__all__"


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
      model = Type
      fields ="__all__"


class DemandSerializer(serializers.ModelSerializer):
    locality = LocalitySerializer(many=False)
    word = BasicWordSerializer(many=False)

    class Meta:
      model = Demand
      fields ="__all__"


class OfferSerializer(serializers.ModelSerializer):
    locality = LocalitySerializer(many=False)
    word = BasicWordSerializer(many=False)

    class Meta:
      model = Offer
      fields ="__all__"


class WordSerializer(serializers.ModelSerializer):
    restricted_words = RestrictedWordSerializer(many=True)
    synonyms = BasicWordSerializer(many=True)
    type = TypeSerializer(many=True)

    class Meta:
        model = Word
        fields = "__all__"
