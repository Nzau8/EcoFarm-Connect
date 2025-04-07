from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def reaction_icon(reaction_type):
    icons = {
        'LIKE': '<i class="bi bi-hand-thumbs-up-fill"></i>',
        'LOVE': '<i class="bi bi-heart-fill"></i>',
        'HAHA': '<i class="bi bi-emoji-laughing-fill"></i>',
        'HELPFUL': '<i class="bi bi-lightbulb-fill"></i>',
    }
    return mark_safe(icons.get(reaction_type, ''))