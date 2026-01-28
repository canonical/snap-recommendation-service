import flask


def api_response(data, success=True, message="", status_code=200):
    return flask.jsonify({
        "data": data,
        "success": success,
        "message": message
    }), status_code


def slugify(s: str) -> str:
    """
    Slugifies a string.
    """
    slug = s.lower().replace(" ", "_")

    for char in "!@#$%^&*()+=[]{}|;:,.<>?/":
        slug = slug.replace(char, "")

    return slug


def get_icon(media):
    icons = [m["url"] for m in media if m["type"] == "icon"]
    if len(icons) > 0:
        return icons[0]
    return ""
