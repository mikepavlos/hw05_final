import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Group, Post, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост больше пятнадцати символов',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.address_templates = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:follow_index'
            ): 'posts/follow.html',
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates = PostPagesTests.address_templates

        for address, template in templates.items():
            with self.subTest(address=address):
                response = PostPagesTests.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def get_context_post(self, response):
        context_post = response.context['page_obj']
        self.assertEqual((len(context_post)), 1)
        self.assertEqual(context_post[0], PostPagesTests.post)
        self.assertEqual(context_post[0].text, PostPagesTests.post.text)
        self.assertEqual(context_post[0].image, PostPagesTests.post.image)
        return context_post

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(reverse('posts:index'))
        context_post = self.get_context_post(response)[0]
        self.assertEqual(context_post.author, PostPagesTests.user)
        self.assertEqual(context_post.group, PostPagesTests.group)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        context_group = response.context['group']
        context_post = self.get_context_post(response)[0]
        self.assertEqual(context_post.group, context_group)
        self.assertEqual(context_group, PostPagesTests.group)
        self.assertEqual(context_post.author, PostPagesTests.user)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse('posts:profile', kwargs={'username': PostPagesTests.user})
        )
        context_author = response.context['author']
        context_post = self.get_context_post(response)[0]
        self.assertEqual(context_post.author, context_author)
        self.assertEqual(context_author, PostPagesTests.user)
        self.assertEqual(context_post.group, PostPagesTests.group)
        self.assertIn('following', response.context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            )
        )
        form_comment = response.context['form'].fields['text']
        self.assertEqual(
            response.context['post'].id,
            PostPagesTests.post.id
        )
        self.assertEqual(
            response.context['post'].author,
            PostPagesTests.post.author
        )
        self.assertEqual(
            response.context['post'].text,
            PostPagesTests.post.text
        )
        self.assertEqual(
            response.context['post'].image,
            PostPagesTests.post.image
        )
        self.assertEqual(
            response.context['post'].comments.all()[0],
            PostPagesTests.comment
        )
        self.assertIsInstance(form_comment, forms.fields.CharField)

    def test_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse('posts:post_create')
        )

        for value, expected in PostPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_with_group_correct_templates(self):
        """Пост группы при его создании отображается на страницах."""
        self.new_group = Group.objects.create(
            title='Тестовая новая группа',
            slug='test_slug_new',
            description='Тестовое описание'
        )
        self.new_post = Post.objects.create(
            text='Тестовый текст создания нового поста',
            author=PostPagesTests.user,
            group=self.new_group
        )
        response_index = PostPagesTests.authorized_client.get(
            reverse('posts:index')
        )
        response_group = PostPagesTests.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.new_group.slug}
            )
        )
        response_any_group = PostPagesTests.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        response_profile = PostPagesTests.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
        )
        self.assertIn(self.new_post, response_index.context['page_obj'])
        self.assertIn(self.new_post, response_group.context['page_obj'])
        self.assertIn(self.new_post, response_profile.context['page_obj'])
        self.assertNotIn(self.new_post, response_any_group.context['page_obj'])

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': PostPagesTests.post.id}
        ))

        for value, expected in PostPagesTests.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context['post'].id, PostPagesTests.post.id)
        self.assertTrue(response.context['post'])
        self.assertTrue(response.context['is_edit'])


class PaginatorViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.author = User.objects.create_user(username='following_author')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        posts = [
            Post(
                author=self.author,
                text=f'Тестовый пост {i}',
                group=self.group) for i in range(13)
        ]
        self.posts = Post.objects.bulk_create(posts)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.view_names = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ),
            reverse('posts:follow_index'),
        )

    def test_paginator_ten_records_per_page(self):
        """Пагинатор выдает не более 10 записей на страницу"""
        page_posts = {'': 10, '?page=2': 3}

        for current_page in self.view_names:
            with self.subTest(current_page=current_page):
                for next_page, number_of_posts in page_posts.items():
                    response = self.authorized_client.get(
                        current_page + next_page
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), number_of_posts
                    )


class CacheTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='user_cache_test')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_cache_posts(self):
        """При удалении записи, она остается в кэше страницы
        до принудительной очистки кэша.
        """
        response = self.authorized_client.get(reverse('posts:index'))

        self.post.text = 'Проверка кэширования поста'
        self.post.save()
        response_cache = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_cache.content, response.content)

        Post.objects.get(id=self.post.pk).delete()
        response_del = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_del.content, response.content)

        cache.clear()
        response_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_clear.content, response.content)


class FollowTests(TestCase):

    def setUp(self):
        self.user_fol = User.objects.create_user(username='follower_user')
        self.user_unfol = User.objects.create_user(username='unfollower_user')
        self.author = User.objects.create_user(username='following_author')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_fol)
        self.authorized_unfol_client = Client()
        self.authorized_unfol_client.force_login(self.user_unfol)
        self.follow = Follow.objects.filter(
            author=self.author,
            user=self.user_fol
        )

    def test_authorized_follow_unfollow(self):
        follow_count = self.follow.count()
        response_follow = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            )
        )
        new_follow = self.follow
        self.assertTrue(new_follow.exists())
        self.assertEqual(new_follow.count(), follow_count + 1)
        self.assertRedirects(
            response_follow,
            reverse('posts:follow_index')
        )

        response_unfollow = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            )
        )
        unfollow = self.follow
        self.assertFalse(unfollow.exists())
        self.assertEqual(unfollow.count(), follow_count)
        self.assertRedirects(
            response_unfollow,
            reverse(
                'posts:profile',
                kwargs={'username': self.author}
            )
        )

    def test_anonymous_cant_follow_unfollow(self):
        follow_count = self.follow.count()
        response_follow = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            ),
            follow=True
        )
        response_unfollow = self.guest_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            ),
            follow=True
        )
        self.assertRedirects(
            response_follow,
            '/auth/login/?next=/profile/following_author/follow/'
        )
        self.assertRedirects(
            response_unfollow,
            '/auth/login/?next=/profile/following_author/unfollow/'
        )
        self.assertFalse(self.follow.exists())
        self.assertEqual(self.follow.count(), follow_count)

    def test_new_post_on_page_by_follow(self):
        Follow.objects.create(
            user=self.user_fol,
            author=self.author
        )
        new_post = Post.objects.create(
            author=self.author,
            text='Новый текст в подписку'
        )
        response_user_fol = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        response_user_unfol = self.authorized_unfol_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, response_user_fol.context['page_obj'])
        self.assertNotIn(new_post, response_user_unfol.context['page_obj'])
