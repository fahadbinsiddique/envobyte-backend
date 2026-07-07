from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'is_favorite',
            'personal_note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_favorite']


class ContactCreateUpdateSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Contact
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
        ]


class ContactNoteSerializer(serializers.ModelSerializer):
   

    class Meta:
        model = Contact
        fields = ['personal_note']

    def validate_personal_note(self, value):
        if value is not None and len(value) > 5000:
            raise serializers.ValidationError(
                "Personal note cannot exceed 5000 characters."
            )
        return value


class ContactFavoriteSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Contact
        fields = ['id', 'full_name', 'is_favorite']


class ContactStatsSerializer(serializers.Serializer):
    
    total_contacts = serializers.IntegerField()
    favorite_contacts = serializers.IntegerField()
    contacts_with_notes = serializers.IntegerField()