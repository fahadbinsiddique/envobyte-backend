from rest_framework.routers import DefaultRouter
from .views import ContactViewSet

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')

urlpatterns = router.urls

# GET    /contacts/                  -> list
# POST   /contacts/                  -> create
# GET    /contacts/{id}/             -> retrieve
# PUT    /contacts/{id}/             -> update
# PATCH  /contacts/{id}/             -> partial_update
# DELETE /contacts/{id}/             -> destroy

# GET    /contacts/favorites/        -> favorites list
# POST   /contacts/{id}/favorite/    -> mark favorite
# DELETE /contacts/{id}/favorite/    -> remove favorite
# PATCH  /contacts/{id}/favorite/    -> toggle favorite

# PUT    /contacts/{id}/note/        -> update note

# GET    /contacts/stats/            -> statistics