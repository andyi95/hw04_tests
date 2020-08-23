from django.test import Client, TestCase
from django.urls import reverse

from .models import Group, Post, User


class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = User.objects.create_user(
            username='HaroldFinch',
            email='j.reese@contoso.com',
            password='qweerty12'
        )
        self.group = Group.objects.create(
            title='Person of Interest',
            slug='PoV',
            description='Different characters from Person of Interest'
        )
        self.singup_info = {
            'first_name': 'Harold',
            'last_name': 'Finch',
            'username': 'HaroldFinch2',
            'email': 'harold2@decimal.com',
            'password1': 'qweerty12',
            'password2': 'qweerty12'
        }

    def test_unathorized_new_post(self):
        response = self.client.post(
            reverse('new_post'), {'text': 'Пост, которого быть не должно'})
        self.assertRedirects(
            response, '/auth/login/?next=/new/', status_code=302)

    def test_profile(self):
        # Пробуем создать профиль стандартным средствами
        self.client.post('/auth/signup/', self.singup_info)
        self.client.login(username='HaroldFinch2', password='qweerty12')
        # Проверяем возможность создания записи и наличия профиля
        response = self.client.get('/new/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/HaroldFinch2/')
        self.assertEqual(response.status_code, 200)
        # Заодно проверим основной профиль
        response = self.client.get(f'/{self.username}/')
        self.assertEqual(response.status_code, 200, msg='here we are')

    def test_new_post_auth(self):
        # Логинимся, создаем пост и проверяем наличие в index
        post_text: str = 'Only the paranoid survive'
        self.client.login(username='HaroldFinch', password='qweerty12')
        self.client.post(
            '/new/',
            {'text': post_text, 'group': self.group.id},
            follow=True
        )
        response = self.client.get('/')
        self.assertContains(response, post_text)
        self.assertContains(response, self.username)
        # Проверим, отображается-ли пост на странице сообщества
        response = self.client.get(
            reverse(
                'group',
                kwargs={'slug': self.group.slug}
            ))
        self.assertContains(response, post_text)
        post = Post.objects.filter(
            author=self.username,
            text=post_text).first()
        self.assertIsNotNone(post)
        response = self.client.get(f'/{self.username}/')
        self.assertContains(response, post_text)
        # И пробуем открыть пост по ключу
        response = self.client.get(f'/{self.username}/{post.pk}/')
        self.assertContains(response, post_text)

    def test_edit(self):
        post_text = 'I have played by the rules for so long.'
        post_edited_text = 'No, not your rules.'
        Group.objects.create(
            title='Game of Thrones',
            slug='GoT',
            description='Game of Thrones characters'
        )
        self.client.force_login(self.username)
        # self.client.post(
        #     reverse('new_post'),
        #     kwargs={
        #         'text': post_text,
        #         'group': self.group.id
        #     })
        self.client.post('/new/', {'text': post_text})
        post = Post.objects.first()
        # Попытка редактирования нашего поста и перехода по редиректу
        response = self.client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.username,
                    'post_id': post.id}),
            {'text': post_edited_text},
            follow=True
        )
        # Проверяем правильность редиректа
        redir_url = response.redirect_chain[-1][0]
        self.assertRedirects(response, f'/{self.username}/{post.id}/')
        response = self.client.get(redir_url)
        self.assertContains(response, post_edited_text)
        # Ожидаем увидеть изменения на главной...
        response = self.client.get(reverse('index'))
        self.assertContains(response, post_edited_text, status_code=200)
        response = self.client.get(f'/{self.username}/{post.pk}/')
        # ... а также на странице поста
        self.assertContains(response, post_edited_text)

    def test_new_post_unauth(self):
        # Пытаемся создать пост и проверяем,
        # есть ли редирект на страницу авторизации
        response = self.client.post(
            "/new/",
            {"text": 'Another creation of post',
             'author': 'self.user'},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/new/', 302)
        # Проверяем, нет-ли текста на главной странице
        response = self.client.get('/')
        self.assertNotContains(response, 'Another creation of post')

    def test_404(self):
        self.client.force_login(self.username)
        response = self.client.get(f'/{self.username}/154/edit/')
        self.assertEqual(response.status_code, 404)
