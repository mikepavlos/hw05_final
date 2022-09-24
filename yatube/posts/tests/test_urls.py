from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.author = User.objects.create_user(username='autor')
        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.url_address_public = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test-user/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        cls.url_address_authorized = {
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.url_address_author = {
            '/posts/1/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.post.author)

    def test_public_url_exists_at_desired_location(self):
        """Страницы, доступные любому пользователю."""
        for address in PostURLTests.url_address_public.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_url_exists_at_desired_location(self):
        """Старницы, доступные авторизованному пользователю."""
        for address in PostURLTests.url_address_authorized.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_url_exists_at_desired_location(self):
        """Страница, доступная автору."""
        response = self.author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_found_page(self):
        """При запросе несуществующего адреcа, возвращается not found."""
        response_404 = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response_404.status_code, HTTPStatus.NOT_FOUND)

    def test_url_authorized_redirect_anonymous(self):
        """Страницы для авторизованных пользователей перенаправляют
        анонимного пользователя на страницу логина.
        """
        url_address_authorized = {
            **PostURLTests.url_address_authorized,
            **PostURLTests.url_address_author
        }

        for address in url_address_authorized.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, '/auth/login/?next=' + address)

    def test_url_author_redirect_anonymous(self):
        """Страница /edit/ перенаправляет авторизованного пользователя -
        не автора поста на страницу просмотра поста.
        """
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """Страницы использцют соответствующие шаблоны."""
        url_address = {
            **PostURLTests.url_address_public,
            **PostURLTests.url_address_authorized,
        }

        for address, template in url_address.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

        response = self.author_client.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
