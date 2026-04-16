from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    """Return query string with one field replaced, preserving others."""
    request = context["request"]
    params: QueryDict = request.GET.copy()
    params[field] = str(value)
    return params.urlencode()
