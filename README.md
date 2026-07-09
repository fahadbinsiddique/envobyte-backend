# Envobyte Backend Internship Assignment — Contact Management API

A Django REST Framework API that recreates Monica CRM's Contact module features:
Favorite Contacts, Personal Notes, Search, Filtering, and Statistics.

> **Note:** The original assignment specified PHP/Laravel. Per Envobyte HR's updated
> email, this assignment was completed using Python/Django REST Framework, an
> alternative stack explicitly permitted for this submission. Monica CRM was used
> only as a functional reference — no Laravel code was modified or forked.

---

## Tech Stack

- Python 3
- Django
- Django REST Framework (DRF)
- django-filter
- SQLite (default Django database)
- Token Authentication (DRF built-in)

---

## Project Structure

envobyte-backend/
├── config/ # Project settings, URLs
├── contacts/ # Core app: models, serializers, views, filters, tests
│ ├── models.py
│ ├── serializers.py
│ ├── views.py
│ ├── filters.py
│ ├── urls.py
│ ├── admin.py
│ └── tests.py  
├── requirements.txt
├── manage.py
└── README.md

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd envobyte-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (for admin panel + testing)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

### 7. Get an auth token (required for all API requests)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=<your_username>&password=<your_password>"
```

Use the returned token in all requests:

Authorization: Token <your_token>

### 8. Run automated tests

```bash
python manage.py test contacts
```

---

## Note on Monica's API Conventions

Monica's public API documentation (monicahq.com/api) uses a Fractal-based
response envelope (`{"data": {...}}` with Laravel-style `links`/`meta`
pagination), a `query` search parameter, and does not use the `PATCH` verb.
The `main` branch linked in this assignment is Monica's in-development beta
rewrite, whose actual route structure differs from the documented v1 API.

Since this assignment was implemented in Django REST Framework (per Envobyte's
updated stack-flexibility email) rather than extending Monica's Laravel code,
this project follows DRF's own idiomatic conventions (standard pagination,
`search` query param, and `PATCH` for the toggle action) rather than mirroring
Monica's Fractal response format one-to-one. The core requirements — consistent
JSON structure, RESTful endpoints, filtering, and statistics — are fully met.

## API Endpoints

All endpoints require authentication (`Authorization: Token <token>` header) and only
return/modify data belonging to the authenticated user.

| Method | Endpoint                       | Description                                                        |
| ------ | ------------------------------ | ------------------------------------------------------------------ |
| GET    | `/api/contacts/`               | List contacts (paginated, filterable, searchable)                  |
| POST   | `/api/contacts/`               | Create a contact                                                   |
| GET    | `/api/contacts/{id}/`          | Retrieve contact details (includes `is_favorite`, `personal_note`) |
| PUT    | `/api/contacts/{id}/`          | Update a contact                                                   |
| DELETE | `/api/contacts/{id}/`          | Delete a contact                                                   |
| GET    | `/api/contacts/favorites/`     | List favorite contacts only                                        |
| POST   | `/api/contacts/{id}/favorite/` | Mark contact as favorite                                           |
| DELETE | `/api/contacts/{id}/favorite/` | Remove contact from favorites                                      |
| PATCH  | `/api/contacts/{id}/favorite/` | Toggle favorite status                                             |
| PUT    | `/api/contacts/{id}/note/`     | Update personal note                                               |
| GET    | `/api/contacts/stats/`         | Get statistics (total, favorites, contacts with notes)             |

### Filtering & Search

GET /api/contacts/?favorite=1
GET /api/contacts/?favorite=0
GET /api/contacts/?search=john
GET /api/contacts/?favorite=1&search=john

Pagination and ordering (`?ordering=first_name`, etc.) continue to work alongside
filters and search.

### Response Format

All endpoints return a consistent JSON structure:

**Success:**

```json
{
  "success": true,
  "message": "Contact retrieved successfully.",
  "data": {}
}
```

**Error:**

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {}
}
```

**Statistics example:**

```json
{
  "success": true,
  "message": "Statistics retrieved successfully.",
  "data": {
    "total_contacts": 125,
    "favorite_contacts": 18,
    "contacts_with_notes": 42
  }
}
```

---

## Implementation Approach

- **Architecture:** Standard DRF `ModelViewSet` with custom `@action` routes for
  favorite/note/stats endpoints, registered through `DefaultRouter`. This keeps
  routing RESTful and consistent with DRF conventions.
- **Filtering:** Centralized in `contacts/filters.py` using `django-filter`'s
  `FilterSet`, so search and favorite-filtering logic exists in exactly one place
  and is reused by both the main list endpoint and the favorites endpoint.
- **Serializers:** Split by responsibility — a main `ContactSerializer` for
  reads, a restricted `ContactCreateUpdateSerializer` for core field writes, and
  dedicated `ContactNoteSerializer` / `ContactFavoriteSerializer` for their
  respective endpoints — so `is_favorite` can never be changed through a generic
  update call.
- **Statistics:** Computed with a single `aggregate()` query using conditional
  `Count`/`Case`/`When` expressions, avoiding any Python-side loops over contacts.
- **Consistent responses:** Shared `success_response()` / `error_response()`
  helpers ensure every endpoint returns the same JSON shape.
- **Data isolation:** Every queryset is filtered by `request.user`, so users can
  never view, modify, or count another user's contacts.

---

## Assumptions

- Each contact belongs to exactly one user (`ForeignKey` to Django's built-in
  `User` model), matching Monica CRM's per-account contact ownership model.
- `personal_note` empty string (`""`) is treated as "no note" for the
  `contacts_with_notes` statistic — only non-null, non-empty notes are counted.
- Token Authentication was used instead of session/JWT auth for simplicity,
  since the assignment did not mandate a specific auth mechanism.
- Search matches `first_name`, `last_name`, `email`, and `phone` fields
  case-insensitively.

---

## Limitations / Trade-offs

- No JWT refresh-token flow — a simple static DRF token is used per user.
- No Swagger/OpenAPI schema generation is included (would add `drf-spectacular`
  or similar with more time).
- SQLite is used for simplicity; PostgreSQL would be a straightforward swap via
  `DATABASES` settings for production use.
- No rate limiting or caching layer, since it was out of scope for this
  assignment's requirements.

**Given more time, I would add:**

- JWT authentication
- Swagger/OpenAPI documentation
- Docker support
- PostgreSQL + CI/CD pipeline
- Redis caching for the stats endpoint

---

## Testing

21 automated feature tests covering:

- Marking/removing/toggling favorites (including cross-user access denial)
- Personal note updates (including validation and cross-user access denial)
- Favorite filtering, search, combined filtering, and pagination
- Statistics accuracy and per-user isolation
- Authentication requirements and 404 handling

Run with:

```bash
python manage.py test contacts
```

---

## Time Spent

Approximately 5–6 hours, including requirement analysis, implementation,
manual testing, automated tests, and documentation.
