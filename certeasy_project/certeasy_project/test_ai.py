from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

class AITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_ai_generate_flashcards(self):
        url = reverse('ai_generate')
        data = {
            'type': 'flashcards',
            'prompt': 'Python decorators',
            'count': 1
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertIn('data', resp_data)

    def test_ai_generate_resource(self):
        url = reverse('ai_generate')
        data = {
            'type': 'resource',
            'prompt': 'Data Structures',
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertIn('content', resp_data)

    def test_ai_generate_quiz(self):
        url = reverse('ai_generate')
        data = {
            'type': 'quiz',
            'prompt': 'Machine Learning basics',
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertIn('data', resp_data)
