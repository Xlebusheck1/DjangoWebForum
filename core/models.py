from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class DefaultModel(models.Model):
    class Meta:
        abstract = True

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания", null=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время обновления", null=True, editable=False)

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Question(DefaultModel):
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    title = models.CharField(max_length=200)
    detailed = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Теги")
    likes = models.ManyToManyField(User, through='QuestionLike', related_name='question_likes')

    def __str__(self):
        return str(self.title)
    
    def likes_count(self):
        return self.likes.count()


class Answer(DefaultModel):
    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    answer_text = models.TextField()
    likes = models.ManyToManyField(User, through='AnswerLike', related_name='answer_likes')
    
    def __str__(self):
        return "Ответ на вопрос с ID = " + str(self.question_id)
    
    def likes_count(self):
        return self.likes.count()

class Tag(models.Model):
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    title = models.CharField(max_length=200, verbose_name="Название тега")

    def __str__(self):
        return self.title

class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)