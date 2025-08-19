from flask import request, redirect
from urllib.parse import unquote, urlparse, urlunparse

def slugify(s: str) -> str:
    """
    Slugifies a string.
    """
    slug = s.lower().replace(" ", "_")

    for char in "!@#$%^&*()+=[]{}|;:,.<>?/":
        slug = slug.replace(char, "")

    return slug

def clear_trailing_slash():

    parsed_url = urlparse(unquote(request.url))
    path = parsed_url.path

    if path != "/" and path.endswith("/"):
        new_uri = urlunparse(parsed_url._replace(path=path[:-1]))

        return redirect(new_uri)
