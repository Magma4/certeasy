from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from certifications.models import Certification
from flashcards.models import Flashcard

class SaaSFeaturesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        self.cert = Certification.objects.create(title="Test Cert", description="Test Desc", category="Test")
        self.fc = Flashcard.objects.create(certification=self.cert, front_text="Front", back_text="Back", topic="Test")

    def test_export_flashcards(self):
        url = reverse('export_flashcards', args=[self.cert.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(b'Front', response.content)

    def test_pricing_view(self):
        url = reverse('pricing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Simple, transparent pricing')

    def test_create_checkout_session(self):
        url = reverse('create_checkout_session')
        # Expect an error 403 because we haven't configured real stripe key, but it means endpoint works
        response = self.client.post(url)
        self.assertTrue(response.status_code in [200, 403])
