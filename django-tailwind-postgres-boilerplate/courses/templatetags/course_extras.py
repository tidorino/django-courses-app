import re

from django import template

register = template.Library()

YOUTUBE_PATTERNS = [
    re.compile(r"youtube\.com/watch\?v=([\w-]+)"),
    re.compile(r"youtu\.be/([\w-]+)"),
    re.compile(r"youtube\.com/embed/([\w-]+)"),
]


@register.filter
def youtube_embed_url(url):
    """Return a YouTube embed URL if `url` is a YouTube link, else None."""
    if not url:
        return None
    for pattern in YOUTUBE_PATTERNS:
        match = pattern.search(url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"
    return None


@register.filter
def is_youtube(url):
    return youtube_embed_url(url) is not None
