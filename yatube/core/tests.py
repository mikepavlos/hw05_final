from http import HTTPStatus

from django.test import TestCase, Client


class CoreTests(TestCase):

    def test_not_found_custom(self):
        """На запрос неизвестной страницы вызывается кастомный шаблон 404."""
        client = Client()
        response = client.get('/unknown_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
