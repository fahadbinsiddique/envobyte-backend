from django.db.models import Q, Count, Case, When, IntegerField
from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Contact
from .filters import ContactFilter
from .serializers import (
    ContactSerializer,
    ContactCreateUpdateSerializer,
    ContactNoteSerializer,
    ContactFavoriteSerializer,
    ContactStatsSerializer,
)


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
   
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors if errors is not None else {},
        },
        status=status_code,
    )


class ContactViewSet(viewsets.ModelViewSet):
    """
    Handles all Contact-related operations:
    - list / retrieve / create / update / delete
    - favorites list
    - mark / remove / toggle favorite
    - update personal note
    - statistics
    """
    permission_classes = [IsAuthenticated]
    filterset_class = ContactFilter
    filter_backends = [
        __import__('django_filters.rest_framework', fromlist=['DjangoFilterBackend']).DjangoFilterBackend,
        drf_filters.OrderingFilter,
    ]
    ordering_fields = ['first_name', 'last_name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # only the authenticated user's own contacts are visible.
        return Contact.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContactCreateUpdateSerializer
        return ContactSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ContactSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ContactSerializer(queryset, many=True)
        return success_response("Contacts retrieved successfully.", serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ContactSerializer(instance)
        return success_response("Contact retrieved successfully.", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        self.perform_create(serializer)
        return success_response(
            "Contact created successfully.",
            ContactSerializer(serializer.instance).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            "Contact updated successfully.",
            ContactSerializer(serializer.instance).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response("Contact deleted successfully.")

    # ---------- Favorites ----------

    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        """GET /api/contacts/favorites/ - List only favorite contacts."""
        queryset = self.filter_queryset(self.get_queryset()).filter(is_favorite=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ContactSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ContactSerializer(queryset, many=True)
        return success_response("Favorite contacts retrieved successfully.", serializer.data)

    @action(detail=True, methods=['post', 'delete', 'patch'], url_path='favorite')
    def favorite(self, request, pk=None):
        """
        POST   /api/contacts/{id}/favorite/  -> mark as favorite
        DELETE /api/contacts/{id}/favorite/  -> remove favorite
        PATCH  /api/contacts/{id}/favorite/  -> toggle favorite
        """
        contact = self.get_object()

        if request.method == 'POST':
            contact.is_favorite = True
            message = "Contact marked as favorite."
        elif request.method == 'DELETE':
            contact.is_favorite = False
            message = "Contact removed from favorites."
        else:  # PATCH - toggle
            contact.is_favorite = not contact.is_favorite
            message = "Contact favorite status toggled."

        contact.save(update_fields=['is_favorite', 'updated_at'])
        serializer = ContactFavoriteSerializer(contact)
        return success_response(message, serializer.data)

    # ---------- Personal Note ----------

    @action(detail=True, methods=['put'], url_path='note')
    def note(self, request, pk=None):
        """PUT /api/contacts/{id}/note/ - Update the personal note."""
        contact = self.get_object()
        serializer = ContactNoteSerializer(contact, data=request.data, partial=False)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        serializer.save()
        return success_response(
            "Personal note updated successfully.",
            ContactSerializer(contact).data,
        )

    # ---------- Statistics ----------

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        
        aggregates = Contact.objects.filter(user=request.user).aggregate(
            total_contacts=Count('id'),
            favorite_contacts=Count(Case(
                When(is_favorite=True, then=1),
                output_field=IntegerField(),
            )),
            contacts_with_notes=Count(Case(
                When(Q(personal_note__isnull=False) & ~Q(personal_note=''), then=1),
                output_field=IntegerField(),
            )),
        )
        serializer = ContactStatsSerializer(aggregates)
        return success_response("Statistics retrieved successfully.", serializer.data)