from django.core.management.base import BaseCommand
from core.models import Tag

class Command(BaseCommand):
    help = 'Генерация тегов'

    def handle(self, *args, **options):
        tags_data = [
            'JavaScript', 'Python', 'CSS', 'HTML', 'React', 
            'Django', 'Vue', 'Angular', 'Node.js', 'Webpack',
            'TypeScript', 'Java', 'C++', 'PHP', 'Ruby',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Docker'
        ]
        
        created_count = 0
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(title=tag_name)
            if created:
                created_count += 1
                print(f'Создан тег: {tag_name}')       
        