from django.db.models import signals
from django.dispatch import receiver
from core.models import Tag
from core.caches import TagCache


@receiver(signals.post_save, sender=Tag)
def tag_saved(sender, **kwargs):
    TagCache.set_items([{
        'id': tag.id,
        'title': tag.title,
    } for tag in Tag.objects.all()])


@receiver(signals.post_delete, sender=Tag)
def tag_delete(sender, **kwargs):
    TagCache.set_items([{
        'id': tag.id,
        'title': tag.title,
    } for tag in Tag.objects.all()])