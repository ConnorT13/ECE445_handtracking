import os


DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(DATABASE_DIR)
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
DATABASE_IMAGES_DIR = os.path.join(DATABASE_DIR, "images")
ASSETS_IMAGES_DIR = os.path.join(REPO_ROOT, "assets", "images")


def _normalized_relative_path(path):
    return path.replace("\\", "/")


def normalize_image_path_for_storage(image_path):
    if not image_path:
        return image_path

    if os.path.isabs(image_path):
        try:
            relative_path = os.path.relpath(image_path, REPO_ROOT)
            if not relative_path.startswith(".."):
                return _normalized_relative_path(relative_path)
        except ValueError:
            return image_path

    return _normalized_relative_path(image_path)


def resolve_image_path(image_path):
    if not image_path:
        return None

    normalized_input = image_path.replace("\\", "/")
    candidates = []

    if os.path.isabs(image_path):
        candidates.append(image_path)
    else:
        candidates.append(os.path.join(REPO_ROOT, image_path))
        candidates.append(os.path.join(DATABASE_DIR, image_path))

    basename = os.path.basename(normalized_input)
    if basename:
        candidates.append(os.path.join(DATABASE_IMAGES_DIR, basename))
        candidates.append(os.path.join(ASSETS_IMAGES_DIR, basename))

    lowered = normalized_input.lower()
    if "/hand_tracking/database/images/" in lowered:
        candidates.append(os.path.join(DATABASE_IMAGES_DIR, basename))
    if "/assets/images/" in lowered:
        candidates.append(os.path.join(ASSETS_IMAGES_DIR, basename))

    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        normalized_candidate = os.path.normpath(candidate)
        if normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)
        if os.path.exists(normalized_candidate):
            return normalized_candidate

    return None
