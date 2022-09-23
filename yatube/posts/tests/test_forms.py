import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Group, Post, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new_test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.uploaded_new = SimpleUploadedFile(
            name='new_small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """При отправке формы со страницы создания поста
        создаётся новая запись в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': PostFormTests.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.post.author}
        ))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый новый пост',
                author=PostFormTests.user,
                group=PostFormTests.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_change_data_on_id(self):
        """При отправке формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст редактируемого поста',
            'group': PostFormTests.new_group.pk,
            'image': self.uploaded_new
        }
        old_post = Post.objects.get(pk=PostFormTests.post.pk)
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.get(pk=PostFormTests.post.pk)
        self.assertNotEqual(old_post.text, new_post.text)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.pk}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                id=PostFormTests.post.pk,
                text='Текст редактируемого поста',
                group=PostFormTests.new_group,
                image='posts/new_small.gif'
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                id=PostFormTests.post.pk,
                text='Текст поста',
                group=PostFormTests.group,
                image='posts/small.gif'
            )
        )

    def test_anonymous_cant_create_post(self):
        """При попытке создания поста неавторизованным пользователем
        не создаётся новая запись в базе данных, происходит редирект.
        """
        posts_count = Post.objects.count()
        post_last = Post.objects.last()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': PostFormTests.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.last(), post_last)


class CommentFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='comment_user')
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.form_data = {'text': 'Тестовый комментарий'}
        self.comment = Comment.objects.filter(id=self.post.pk)

    def test_create_comment(self):
        """После успешной отправки у поста появляется комментарий."""
        comments_before_count = self.comment.count()
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        comments_after = Post.objects.get(id=self.post.pk).comments.all()
        self.assertEqual(comments_after.count(), comments_before_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertTrue(
            Comment.objects.filter(
                text=self.form_data['text'],
                post=self.post.pk,
                author=self.user.pk,
            ).exists()
        )

    def test_anonymous_cant_create_comment(self):
        """Комментарий к посту может создать только
        авторизованный пользователь.
        """
        comment_last = self.comment.last()
        comments_count = self.comment.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')
        self.assertEqual(self.comment.count(), comments_count)
        self.assertEqual(self.comment.last(), comment_last)
