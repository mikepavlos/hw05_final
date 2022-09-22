from django.test import Client, TestCase
from django.urls import reverse

from ..forms import User


class UserFormTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_create_new_user(self):
        """При отправке формы со страницы signup
        создаётся новый пользователь.
        """
        user_count = User.objects.count()
        form_data = {
            'username': 'new_user',
            'password1': 'Ujijk34joi',
            'password2': 'Ujijk34joi',
        }
        response = self.client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        new_user = User.objects.filter(username=form_data['username'])
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertRedirects(response, '/')
        self.assertTrue(new_user.exists())
