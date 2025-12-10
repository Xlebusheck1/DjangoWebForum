import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Question, Answer, Tag

User = get_user_model()

FAKE_QUESTION_DETAILED = (
    "Curabitur lobortis mattis mattis. Duis at orci lorem. Donec id massa at "
    "tellus placerat ullamcorper vel nec tellus. Phasellus iaculis sed enim non dictum. "
    "Cras vel lobortis velit, ac pharetra erat. Integer et dapibus lorem, "
    "nec suscipit felis. Pellentesque elementum mollis nisl, at iaculis justo fermentum at."
)

FAKE_ANSWER_TEXT = "Это тестовый ответ на вопрос. Для разработки форума."


class Command(BaseCommand):
    help = "Генерация вопросов и ответов"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=50,
                            help='Количество вопросов для генерации')

    def get_author(self) -> User:
        # любой существующий пользователь (сначала суперюзер, потом любой)
        user = User.objects.filter(is_superuser=True).first()
        if user:
            return user
        return User.objects.first()

    def handle(self, *args, **options):
        count = options['count']

        author = self.get_author()
        if author is None:
            self.stdout.write(self.style.ERROR(
                'Нет пользователей. Сначала запусти команду generate_users.'
            ))
            return

        tags = list(Tag.objects.all())
        if not tags:
            self.stdout.write(self.style.ERROR(
                'Нет тегов. Сначала запусти команду generate_tags.'
            ))
            return

        existing_count = Question.objects.count()
        questions_to_create = []

        for n in range(count):
            questions_to_create.append(
                Question(
                    title=f'Тестовый вопрос #{existing_count + n + 1}',
                    detailed=FAKE_QUESTION_DETAILED,
                    author=author,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
            )

        Question.objects.bulk_create(questions_to_create, batch_size=100)

        # нужно перечитать из БД, чтобы были id
        questions = list(
            Question.objects.order_by('-id')[:count]
        )

        # назначаем теги и создаём ответы
        for q in questions:
            # 1–3 случайных тега
            q_tags = random.sample(tags, k=min(len(tags), random.randint(1, 3)))
            q.tags.set(q_tags)

            # 1–4 ответа к каждому вопросу
            answers_to_create = []
            for _ in range(random.randint(1, 4)):
                answers_to_create.append(
                    Answer(
                        question=q,
                        author=author,
                        answer_text=FAKE_ANSWER_TEXT,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                )
            Answer.objects.bulk_create(answers_to_create, batch_size=100)

        self.stdout.write(self.style.SUCCESS(
            f'Создано вопросов: {len(questions)}'
        ))
