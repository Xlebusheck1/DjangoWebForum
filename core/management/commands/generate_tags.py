from django.core.management.base import BaseCommand
from core.models import Tag


class Command(BaseCommand):
    help = "Генерация тегов"

    TAGS = [
        'JavaScript', 'Python', 'CSS', 'HTML', 'React',
        'Django', 'Vue', 'Angular', 'Node.js', 'Webpack',
        'TypeScript', 'Java', 'C++', 'PHP', 'Ruby',
        'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Docker',
    ]

    def handle(self, *args, **options):
        created_count = 0
        for name in self.TAGS:
            tag, created = Tag.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(f'Создан тег: {name}')
        self.stdout.write(self.style.SUCCESS(f'Всего создано тегов: {created_count}'))
