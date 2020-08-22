from django.forms import ModelForm

from .models import Post


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text')
        required = {
            'group': False,
        }
        labels = {
            'group': 'Сообщества',
            'text': 'Текст записи',
        }
