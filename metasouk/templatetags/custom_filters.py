# metasouk/templatetags/custom_filters.py
import base64
from django import template

register = template.Library()

@register.filter(name='b64encode')
def b64encode_filter(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return base64.b64encode(value).decode('utf-8')
