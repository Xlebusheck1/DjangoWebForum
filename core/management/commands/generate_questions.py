import typing as t
import random
from django.core.management.base import BaseCommand
from core.models import Question, User, Tag

FAKE_QUESTION_DETALED = """
Curabitur lobortis mattis mattis. Duis at orci lorem. Donec id massa at 
tellus placerat ullamcorper vel nec tellus. Phasellus iaculis sed enim non dictum.
Cras vel lobortis velit, ac pharetra erat. Integer et dapibus lorem, 
nec suscipit felis. Class aptent taciti sociosqu ad litora torquent per 
conubia nostra, per inceptos himenaeos. Pellentesque elementum mollis nisl, 
at iaculis justo fermentum at. Donec ultricies eu felis nec tempus. In viverra, 
sapien id posuere imperdiet, enim lorem tempus ante, at fermentum nulla metus 
quis ligula. Vivamus ut odio ipsum.
"""

class Command(BaseCommand):
    help = 'Генерация сущностей по модели вопроса'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100)
    
    def get_exists_user(self) -> t.Optional[User]:
        return User.objects.filter(is_superuser=True).first()

    def get_or_create_tags(self):
            """Создание тегов если их нет"""
            tags_data = ['JavaScript', 'Python', 'CSS', 'HTML', 'React', 'Django', 'Vue', 'Angular', 'Node.js', 'Webpack']
            tags = []
            for tag_name in tags_data:
                tag, created = Tag.objects.get_or_create(title=tag_name)
                tags.append(tag)
            return tags

    def handle(self, *args, **options):
        count = options.get('count')
        count_exists_questions = Question.objects.all().count()
        tags = self.get_or_create_tags()
        questions_to_create = []
        for n in range(count):
            questions_to_create.append(Question(
                title=f"Вопрос под номером {count_exists_questions + n + 1}",
                detailed=FAKE_QUESTION_DETALED,
                author=self.get_exists_user()
            ))

        Question.objects.bulk_create(questions_to_create, batch_size=100)
        
        for question in questions_to_create:
            question_tags = random.sample(tags, random.randint(1, 3))
            question.tags.set(question_tags)

        print(f'Создано {len(questions_to_create)} вопросов')