from django.test import Client, TestCase
from django.urls import reverse

from ..forms import User


class UsersNameTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(
            User.objects.create_user(username='test_user')
        )
        self.namespace_templates = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_reset_confirm', kwargs={
                'uidb64': 'uid',
                'token': 'token'
            }): 'users/password_reset_confirm.html',
            reverse('users:password_reset_complete'):
                'users/password_reset_complete.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        self.auth_namespace_templates = {
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
        }

    def test_users_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.auth_namespace_templates.update(self.namespace_templates)
        for address, template in self.auth_namespace_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_authorized_pages_redirect_anonymous(self):
        """Адреса смены пароля перенаправляют анонимного пользователя
        на страницу логина.
        """
        for address in self.auth_namespace_templates.keys():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertRedirects(response, '/auth/login/?next=' + address)

    def test_signup_show_correct_context(self):
        """На страницу signup передается в контексте
        форма для создания нового пользователя.
        """
        fields = ('first_name', 'last_name', 'username', 'email')
        response = self.client.get(reverse('users:signup'))
        self.assertIn('form', response.context)
        for value in fields:
            with self.subTest(value=value):
                self.assertIn(value, response.context['form'].fields)
