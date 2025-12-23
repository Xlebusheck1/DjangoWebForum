from core.models import Tag
from django.core.cache import cache


class TagCache:
    key = 'tag_cache'
    timeout = 60 * 60 * 24 * 7

    @classmethod
    def get_items(cls):
        items = cache.get(cls.key)
        if not items:
            items = [{
                'id': tag.id,
                'name': tag.name,
            } for tag in Tag.objects.all()]
            cache.set(cls.key, items)
            return items
        return items

    @classmethod
    def set_items(cls, items):
        cache.set(cls.key, items, cls.timeout)