import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_IMAGES_REL_DIR = os.path.join("hand_tracking", "database", "images")


def database_image_path(filename):
    return os.path.join(DATABASE_IMAGES_REL_DIR, filename)


def resolve_image_path(image_path):
    if not image_path:
        return image_path

    expanded_path = os.path.expanduser(image_path)
    candidates = []

    if os.path.isabs(expanded_path):
        candidates.append(expanded_path)
    else:
        candidates.append(os.path.join(REPO_ROOT, expanded_path))
        candidates.append(expanded_path)

    filename = os.path.basename(expanded_path)
    if filename:
        candidates.append(os.path.join(REPO_ROOT, DATABASE_IMAGES_REL_DIR, filename))
        candidates.append(os.path.join(REPO_ROOT, "assets", "images", filename))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return expanded_path
