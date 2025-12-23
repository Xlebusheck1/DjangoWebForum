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
    rating = models.PositiveIntegerField(default=0, verbose_name="Рейтинг")
    rank = models.PositiveIntegerField(default=0, verbose_name="Позиция в топе")
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Question(DefaultModel):
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    title = models.CharField(max_length=200)
    detailed = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_questions')
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Теги")
    likes = models.ManyToManyField(User, through='QuestionLike', related_name='question_likes')

    likes = models.ManyToManyField(User, through='QuestionLike', blank=True)
    rating = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.title)
    
    def likes_count(self):
        return self.likes.count()


class Answer(DefaultModel):
    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_answers')
    answer_text = models.TextField()
    likes = models.ManyToManyField(User, through='AnswerLike', related_name='answer_likes')
    
    likes = models.ManyToManyField(User, through='AnswerLike', blank=True)
    rating = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")


    def __str__(self):
        return "Ответ на вопрос с ID = " + str(self.question_id)
    
    def likes_count(self):
        return self.likes.count()


class Tag(models.Model):
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    name = models.CharField(max_length=200, verbose_name="Название тега")

    def __str__(self):
        return self.name  


class QuestionLike(models.Model):
    class Meta:
        verbose_name = "Лайки вопросов"
        unique_together = ('question', 'author')
    

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_like = models.BooleanField(default=True)


class AnswerLike(models.Model):
    class Meta:
        verbose_name = "Лайки ответов"
        unique_together = ('answer', 'author')

        
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_like = models.BooleanField(default=True)