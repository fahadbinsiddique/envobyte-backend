from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import Contact


class ContactTestSetupMixin:
    """
    Shared setup logic for all Contact feature tests.
    Avoids duplicating user/auth/contact creation across test classes.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.other_user = User.objects.create_user(
            username="otheruser", password="otherpass123"
        )

    def create_contact(self, user=None, **kwargs):
        defaults = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }
        defaults.update(kwargs)
        return Contact.objects.create(user=user or self.user, **defaults)


class FavoriteContactTests(ContactTestSetupMixin, APITestCase):
    """Mark a contact as favorite, plus related edge cases."""

    def test_mark_contact_as_favorite(self):
        contact = self.create_contact(is_favorite=False)
        url = f"/api/contacts/{contact.id}/favorite/"

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["data"]["is_favorite"])

        contact.refresh_from_db()
        self.assertTrue(contact.is_favorite)

    def test_remove_contact_from_favorite(self):
        contact = self.create_contact(is_favorite=True)
        url = f"/api/contacts/{contact.id}/favorite/"

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["is_favorite"])
        contact.refresh_from_db()
        self.assertFalse(contact.is_favorite)

    def test_toggle_contact_favorite_status(self):
        contact = self.create_contact(is_favorite=False)
        url = f"/api/contacts/{contact.id}/favorite/"

        first_response = self.client.patch(url)
        self.assertTrue(first_response.data["data"]["is_favorite"])

        second_response = self.client.patch(url)
        self.assertFalse(second_response.data["data"]["is_favorite"])

    def test_mark_favorite_invalid_contact_returns_404(self):
        response = self.client.post("/api/contacts/9999/favorite/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_favorite_another_users_contact(self):
        other_contact = self.create_contact(user=self.other_user)
        response = self.client.post(f"/api/contacts/{other_contact.id}/favorite/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PersonalNoteTests(ContactTestSetupMixin, APITestCase):
    """Update a personal note"""

    def test_update_personal_note(self):
        contact = self.create_contact(personal_note=None)
        url = f"/api/contacts/{contact.id}/note/"

        response = self.client.put(
            url, {"personal_note": "Met at a conference in 2025."}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        contact.refresh_from_db()
        self.assertEqual(contact.personal_note, "Met at a conference in 2025.")

    def test_update_note_with_empty_string(self):
        contact = self.create_contact(personal_note="Old note")
        url = f"/api/contacts/{contact.id}/note/"

        response = self.client.put(url, {"personal_note": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact.refresh_from_db()
        self.assertEqual(contact.personal_note, "")

    def test_update_note_exceeding_max_length_fails(self):
        contact = self.create_contact()
        url = f"/api/contacts/{contact.id}/note/"
        long_note = "a" * 5001

        response = self.client.put(url, {"personal_note": long_note}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_cannot_update_note_on_another_users_contact(self):
        other_contact = self.create_contact(user=self.other_user)
        response = self.client.put(
            f"/api/contacts/{other_contact.id}/note/",
            {"personal_note": "hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ContactFilterTests(ContactTestSetupMixin, APITestCase):
    """Filter contacts using favorite=1"""

    def setUp(self):
        super().setUp()
        self.fav_contact = self.create_contact(
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            is_favorite=True,
        )
        self.non_fav_contact = self.create_contact(
            first_name="Bob",
            last_name="Brown",
            email="bob@example.com",
            is_favorite=False,
        )

    def test_filter_contacts_by_favorite(self):
        response = self.client.get("/api/contacts/?favorite=1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.fav_contact.id)
        self.assertTrue(results[0]["is_favorite"])

    def test_filter_contacts_by_non_favorite(self):
        response = self.client.get("/api/contacts/?favorite=0")

        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.non_fav_contact.id)

    def test_search_contacts_by_name(self):
        response = self.client.get("/api/contacts/?search=alice")

        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["first_name"], "Alice")

    def test_search_is_case_insensitive(self):
        response = self.client.get("/api/contacts/?search=ALICE")

        results = response.data["results"]
        self.assertEqual(len(results), 1)

    def test_combined_favorite_and_search_filter(self):
        response = self.client.get("/api/contacts/?favorite=1&search=alice")

        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["first_name"], "Alice")

    def test_pagination_still_works_with_filters(self):
        response = self.client.get("/api/contacts/?favorite=0")

        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_filter_returns_only_authenticated_users_contacts(self):
        self.create_contact(user=self.other_user, first_name="Hidden", is_favorite=True)

        response = self.client.get("/api/contacts/?favorite=1")

        results = response.data["results"]
        names = [c["first_name"] for c in results]
        self.assertNotIn("Hidden", names)


class ContactStatsTests(ContactTestSetupMixin, APITestCase):

    def test_stats_with_empty_database(self):
        response = self.client.get("/api/contacts/stats/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["total_contacts"], 0)
        self.assertEqual(data["favorite_contacts"], 0)
        self.assertEqual(data["contacts_with_notes"], 0)

    def test_stats_with_multiple_contacts(self):
        self.create_contact(first_name="A", is_favorite=True, personal_note="note 1")
        self.create_contact(first_name="B", is_favorite=True, personal_note=None)
        self.create_contact(first_name="C", is_favorite=False, personal_note="note 2")

        response = self.client.get("/api/contacts/stats/")

        data = response.data["data"]
        self.assertEqual(data["total_contacts"], 3)
        self.assertEqual(data["favorite_contacts"], 2)
        self.assertEqual(data["contacts_with_notes"], 2)

    def test_stats_only_count_authenticated_users_contacts(self):
        self.create_contact(
            user=self.other_user, is_favorite=True, personal_note="hidden note"
        )

        response = self.client.get("/api/contacts/stats/")

        data = response.data["data"]
        self.assertEqual(data["total_contacts"], 0)


class ContactDetailTests(ContactTestSetupMixin, APITestCase):

    def test_retrieve_contact_includes_new_fields(self):
        contact = self.create_contact(is_favorite=True, personal_note="Some note")

        response = self.client.get(f"/api/contacts/{contact.id}/")

        data = response.data["data"]
        self.assertIn("is_favorite", data)
        self.assertIn("personal_note", data)
        self.assertTrue(data["is_favorite"])
        self.assertEqual(data["personal_note"], "Some note")

    def test_unauthenticated_request_is_rejected(self):
        self.client.credentials()  # remove auth header
        response = self.client.get("/api/contacts/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
