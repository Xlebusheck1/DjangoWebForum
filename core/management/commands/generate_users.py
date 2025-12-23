from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Генерация тестовых пользователей"

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10)

    def handle(self, *args, **options):
        count = options['count']
        created = 0

        # суперюзер, если нужен
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin1234',
            )
            self.stdout.write(self.style.SUCCESS('Создан суперюзер admin / admin1234'))
            created += 1

        for i in range(count):
            username = f'user{i+1}'
            if User.objects.filter(username=username).exists():
                continue
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password='test1234',
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Создано пользователей: {created}'))
