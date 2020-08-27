from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch',
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

    def test_404(self):
        self.client.force_login(self.user)
        response = self.client.get(f'{self.user.username}/256')
        self.assertEqual(response.status_code, 404,
                         msg='Несоответствующий код ответа на несуществующую '
                             'страницу')


class TestPostCreaton(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch',
            password='qweerty12'
        )
        self.user2 = User.objects.create_user(
            username='JohnReese',
            password='qweerty12'
        )
        self.client.force_login(self.user)
        self.group = Group.objects.create(
            title='Person of Interest',
            slug='PoV'
        )
        self.group2 = Group.objects.create(
            title='Game of Thrones',
            slug='GoT'
        )
        self.post_text = 'Only the paranoid survive'
        self.post_edited_text = 'No, not your rules.'
        self.client.force_login(self.user)

    # Вынесли метод для получения объекта поста из страниц сайта
    def get_page(self, page, pArgs={}):
        if page is None:
            pass
        response = self.client.get(reverse(page, kwargs=pArgs))
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(
                paginator.count, 1,
                msg='Несоответствие количества записей'
                    'илиPaginator работает некорректно'
            )
            post = response.context['page'][0]
        else:
            post = response.context['post']
        return post

    # В  следующем тесте создаем пост через HTTP и сверяем соответствие в
    # БД
    def test_new_post_auth(self):
        self.client.post(reverse('new_post'),
                         {'text': self.post_text, 'group': self.group.id})
        post = Post.objects.select_related(
            'author',
            'group'
        ).filter(
            author=self.user.id
        )
        self.assertEqual(post.count(), 1,
                         msg='Количество постов не соответствует заданным')
        post = post.last()
        self.assertEqual(post.text, self.post_text,
                         msg='Текст поста не соотвествует заданному или '
                             'отсутствует')
        self.assertEqual(post.author, self.user,
                         msg='Автор поста не соотвествует заданному')
        self.assertEqual(post.group, self.group,
                         msg='Сообщество поста не соответствует заданному')

    # Создаем пост в БД и сверяем отображение через http запросы к сайту
    def test_post_display(self):
        self.test_post = Post.objects.create(text=self.post_text,
                                             group=self.group,
                                             author=self.user)
        pages = {
            'index': {},
            'group': {'slug': self.group.slug},
            'profile': {'username': self.user.username},
            'post': {
                'username': self.user.username,
                'post_id': self.test_post.pk
            }
        }
        for page in pages:
            with self.subTest(page=page, msg=f'Запись не найдена'
                                             f' на странице {page}'):
                post = self.get_page(page, pages[page])
                self.assertEqual(post, self.test_post)

    # Создаем пост в БД, редактируем через http и сверяем содержимое на всех
    # связанных страницах
    def test_edit(self):
        self.post = Post.objects.create(
            text=self.post_text,
            author=self.user,
            group=self.group
        )
        response = self.client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id
                }
            ),
            {
                'text': self.post_edited_text,
                'group': self.group2.id
            }, follow=True
        )
        self.assertEqual(response.status_code, 200,
                         msg='Сервер вернул неожиданный ответ')
        post = Post.objects.select_related(
            'author',
            'group'
        ).filter(
            author=self.user.id
        )
        self.assertEqual(post.count(), 1,
                         msg='Количество постов не соответствует заданным')
        post = post.last()
        pages = {
            'index': {},
            'group': {'slug': self.group2.slug},
            'profile': {'username': self.user.username},
            'post': {
                'username': self.user.username,
                'post_id': post.pk
            }
        }
        # Проверяем соответствие изменений в БД...
        self.assertEqual(post.text, self.post_edited_text,
                         msg='Текст поста не соотвествует заданному или '
                             'отсутствует')
        self.assertEqual(post.author, self.user,
                         msg='Автор поста не соотвествует заданному')
        self.assertEqual(post.group, self.group2,
                         msg='Сообщество поста не соответствует заданному')
        # А также на соответствующих страницах. Сверяем объектами из
        # контекста, поскольку поля объектов уже проверены выше
        for page in pages:
            with self.subTest(page=page,
                              msg=f'Измененная запись не найдена на странице '
                                  f'{page}'):
                post = self.get_page(page, pages[page])
                self.assertEqual(post.text, self.post_edited_text)

    # Создаем пост через БД, далее логинимся под вторым пользователем и
    # пытаемся изменить текст и сообщество через http,
    # далее проверяем изменения в БД
    def test_wrong_user_edit(self):
        self.post = Post.objects.create(
            text=self.post_text,
            author=self.user, group=self.group
        )
        self.client.force_login(self.user2)
        response = self.client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.post.author,
                    'post_id': self.post.id
                }
            ),
            {
                'text': self.post_edited_text,
                'group': self.group2.id
            }, follow=True
        )
        target_url = reverse('post', kwargs={
            'username': self.user.username, 'post_id': self.post.id
        })
        self.assertRedirects(response, target_url,
                             msg_prefix='Редирект для неверного пользователя '
                                        'работает неправильно')
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(
            post.text,
            self.post_edited_text,
            msg='Текст поста другого пользователя изменен'
        )
        self.assertNotEqual(
            post.group,
            self.group2,
            msg='Сообщество поста другого пользователя изменено'
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
        self.assertEqual(Post.objects.count(), 0,
                         msg='Сайт позволяет создавать посты'
                             ' неавторизованным пользователям')
