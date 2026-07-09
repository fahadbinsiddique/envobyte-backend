from django_filters import widgets
import django_filters
from .models import Contact


class ContactFilter(django_filters.FilterSet):

    favorite = django_filters.BooleanFilter(
        field_name="is_favorite", widget=widgets.BooleanWidget
    )
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Contact
        fields = ['favorite', 'search']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value)
        )
