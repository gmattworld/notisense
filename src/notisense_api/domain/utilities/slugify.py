import re

import unidecode


def generate_slug(name):
    # Remove special characters, convert to lowercase, and replace spaces with hyphens
    slug = unidecode.unidecode(name).lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    return slug
