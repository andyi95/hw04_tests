from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch'
        )

    def test_profile(self):
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
        self.client2 = Client()
        self.user = User.objects.create_user(
            username='HaroldFinch'
        )
        self.user2 = User.objects.create_user(
            username='JohnReese'
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
        self.client2.force_login(self.user2)

    # Вынесли метод для получения объекта поста из страниц сайта
    # Упустил момент, что TestCase принудительно выполняет только методы с
    # test в начале сигнатуры метода :)
    def get_page(self, page, pArgs={}):
        response = self.client.get(reverse(page, kwargs=pArgs))
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(
                paginator.count, 1,
                msg='Несоответствие количества записей'
                    'или Paginator работает некорректно'
            )
            post = response.context['page'][0]
        else:
            post = response.context['post']
        return post

    # Отдельный общий метод сверки всех полей, вывода соответсвующих
    # сообщений об ошибках и получения собственно поста на выходе
    def check_equality(self, e_posts=None, text=None, user=None, group=None):
        self.assertEqual(e_posts.count(), 1,
                         msg='Количество постов не соответствует заданным')
        e_post = e_posts.last()
        self.assertEqual(e_post.text, text,
                         msg='Текст поста не соотвествует заданному или '
                             'отсутствует')
        self.assertEqual(e_post.author.username, user.username,
                         msg='Автор поста не соотвествует заданному')
        self.assertEqual(e_post.group.slug, group.slug,
                         msg='Сообщество поста не соответствует заданному')
        return e_post

    # В  следующем тесте создаем пост через HTTP и сверяем соответствие в
    # БД
    def test_new_post_auth(self):
        response = self.client.post(reverse('new_post'),
                                    {
                                        'text': self.post_text,
                                        'group': self.group.id
                                    }, follow=True)
        self.assertRedirects(response, reverse('index'))
        posts = Post.objects.all()
        self.check_equality(posts, self.post_text, self.user, self.group)

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
                self.assertEqual(post.text, self.test_post.text)
                self.assertEqual(post.group.slug, self.group.slug)
                self.assertEqual(post.author.username, self.user.username)

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
        posts = Post.objects.all()
        # Проверяем соответствие объекта из БД с заданными и получаем сам пост
        post = self.check_equality(posts, self.post_edited_text, self.user,
                                   self.group2)
        pages = {
            'index': {},
            'group': {'slug': self.group2.slug},
            'profile': {'username': self.user.username},
            'post': {
                'username': self.user.username,
                'post_id': post.pk
            }
        }
        # А также на соответствующих страницах. Сверяем объектами из
        # контекста, поскольку поля объектов уже проверены выше
        # Обещаю занести этот кусок в get_page() в hw05! :)
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
        response = self.client2.post(
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
        posts = Post.objects.all()
        # Убедимся, что пост остался в неизменном виде и в БД не появилось
        # новых постов
        self.check_equality(posts, self.post_text, self.user, self.group)
        # И что на страницах сайта также всё в порядке
        pages = {
            'profile': {'username': self.user.username},
            'post': {
                'username': self.post.author,
                'post_id': self.post.id
            }
        }
        for page in pages:
            with self.subTest(page=page,
                              msg='Пост был несанкционированно изменен'):
                post = self.get_page(page, pages[page])
                self.assertNotEqual(post.text, self.post_edited_text)
        # Убедимся, что не появилось страницы с постом
        response = self.client.get(
            reverse('post', args=[self.user2.username, 1]))
        self.assertEqual(response.status_code, 404)

class TestUnAuthAccess(TestCase):
    def setUp(self):
        self.client = Client()
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
