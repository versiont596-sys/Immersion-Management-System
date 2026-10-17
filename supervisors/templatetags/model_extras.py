from django import template

register = template.Library()

@register.filter
def getattr(obj, attr_name, default=None):
    try:
        return getattr(obj, attr_name)
    except Exception:
        return default
