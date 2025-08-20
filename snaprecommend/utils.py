def slugify(s: str) -> str:
    """
    Slugifies a string.
    """
    slug = s.lower().replace(" ", "_")

    for char in "!@#$%^&*()+=[]{}|;:,.<>?/":
        slug = slug.replace(char, "")

    return slug
