from http import HTTPStatus
from django.test import TestCase, Client

from ..forms import User


class UserURLTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(
            User.objects.create_user(username='test_user')
        )
        self.templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        self.auth_templates = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }

    def test_users_public_url_exists_at_desired_location(self):
        """Проверка доступности адресов 'templates'."""
        for address in self.templates.keys():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_authorized_url_exists_at_desired_location(self):
        """Проверка доступности адресов 'templates'
        авторизованных пользователей.
        """
        for address in self.auth_templates.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_authorized_url_redirect_anonymous(self):
        """Страницы для авторизованных клиентов перенаправляют
        анонимного пользователя на страницу логина.
        """
        for address in self.auth_templates.keys():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + address)

    def test_users_authorized_url_uses_correct_template(self):
        """Проверка шаблонов для адресов 'templates'
        авторизованных пользователей.
        """
        self.auth_templates.update(self.templates)
        for address, template in self.auth_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
