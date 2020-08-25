from django.test import Client, TestCase
from django.urls import reverse

from .models import Group, Post, User


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch',
            email='h.finch@contoso.com',
            password='qweerty12'
        )

    def test_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                'profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(
            response.status_code,
            200,
            msg='Профиль пользователя не найден'
        )


class TestPostCreaton(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch',
            email='h.finch@contoso.com',
            password='qweerty12'
        )
        self.user2 = User.objects.create_user(
            username='JohnReese',
            email='j.reeseh@contoso.com',
            password='qweerty12'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title='Person of Interest',
            slug='PoV',
            description='Different characters from Person of Interest'
        )
        self.group2 = Group.objects.create(
            title='Game of Thrones',
            slug='GoT',
            description='Game of Thrones characters'
        )
        self.post_text = 'Only the paranoid survive'
        self.post_edited_text = 'No, not your rules.'

    def test_new_post_auth(self):
        self.client.force_login(self.user)
        self.client.post(reverse('new_post'),
                         {'text': self.post_text, 'group': self.group.id})
        post = Post.objects.select_related(
            'author',
            'group'
        ).filter(
            author=self.user.id
        ).last()
        post_list = [post.text, post.author.username, post.group.slug]
        user_list = [self.post_text, self.user.username, self.group.slug]
        self.assertEqual(
            post_list,
            user_list,
            msg='Набор значений из БД не соответсвует заданным'
        )
        response = self.client.get(reverse('index'))
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(
                paginator.count, 1,
                msg='Paginator работает некорректно'
            )
            post = response.context['page'][0]
        else:
            post = response.context['post']
        self.assertEqual(
            post.text,
            self.post_text,
            msg='Запись не найдена на главной странице'
        )
        self.post = Post.objects.get(group__slug=self.group.slug)
        self.assertEqual(
            post.text,
            self.post_text,
            msg='Запись не найдена на странице сообщества'
        )
        response = self.client.get(
            reverse(
                'profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertContains(
            response,
            self.post_text,
            msg_prefix='Запись не найдена на странице пользователя'
        )
        response = self.client.get(
            reverse('post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.pk
                    }
                    )
        )
        self.assertContains(
            response,
            self.post_text,
            msg_prefix='Запись не найдена на странице поста')

    def test_edit(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            text=self.post_text,
            author=self.user,
            group=self.group
        )
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.post_text)
        response = self.client.post(
            reverse(
                    'post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id
                    }
            ),
                    {'text': self.post_edited_text,
                    'group': self.group2.id}
        )
        self.assertRedirects(
            response, reverse(
                'post',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            )
        )
        response = self.client.get(reverse('index'))
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(
                paginator.count, 1,
                msg='Paginator работает некорректно'
            )
            post = response.context['page'][0]
        else:
            post = response.context['post']
        self.assertEqual(
            post.text, self.post_edited_text,
            msg='Измененная запись не найдена на главной странице'
        )
        self.assertContains(
            response,
            self.post_edited_text,
            msg_prefix='Измененная запись на главной странице отутствует')
        response = self.client.get(
            reverse(
                'group',
                kwargs={'slug': self.group2.slug}
            ))
        self.assertContains(
            response,
            self.post_edited_text,
            msg_prefix='Измененная страница в'
                       ' сообществах не найдена'
        )
        response = self.client.get(
            reverse('profile', args={self.user.username})
        )
        self.assertContains(
            response, self.post_edited_text,
            msg_prefix='Измененная запись в '
                       'профиле пользователя отутствует'
        )
        response = self.client.get(
            reverse(
                'post',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.pk}
            )
        )
        self.assertContains(
            response, self.post_edited_text,
            msg_prefix='Измененная запись не найдена на странице поста'
        )

    def test_wrong_user(self):
        self.post = Post.objects.create(
            text=self.post_text,
            author=self.user, group=self.group
        )
        self.client.force_login(self.user2)
        self.client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            {'text': self.post_edited_text,
             'group': self.group2.id}
        )
        post = Post.objects.last()
        self.assertNotEqual(
            post.text,
            self.post_edited_text,
            msg='Пост, не принадлежащий пользователю, изменен'
        )


class TestUnAuthAccess(TestCase):
    def setUp(self):
        self.post_text = 'Only the paranoid survive'
        self.group = Group.objects.create(
            title='Person of Interest',
            slug='PoV',
            description='Different characters from Person of Interest'
        )

    def test_unathorized_new_post(self):
        response = self.client.post(
            reverse('new_post'),
            {'text': self.post_text, 'group': self.group.slug}
        )
        login_url = reverse('login')
        new_post_url = reverse('new_post')
        target_url = f'{login_url}?next={new_post_url}'
        self.assertRedirects(
            response,
            target_url,
            msg_prefix='Редирект для неавторизованного пользователя '
                       'работает неправильно'
        )
        response = self.client.get(reverse('index'))
        self.assertNotContains(
            response,
            self.post_text,
            msg_prefix='Сайт позволяет создавать посты'
                       ' неавторизованным пользователям'
        )
