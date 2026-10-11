from django.test import TestCase


class HomePageTests(TestCase):
    def test_home_renders_stack(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("__TITLE__", html)
        self.assertIn('class="btn', html)  # django-basecoat <c-button>
        self.assertIn("unpoly", html)
        self.assertIn('data-testid="count"', html)  # Tetra component
