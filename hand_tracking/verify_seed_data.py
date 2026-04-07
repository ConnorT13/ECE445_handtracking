from database.db_init import initialize_database
from database.db_operations import get_all_professionals, get_tags_for_professional


EXPECTED_PROFESSIONAL_COUNT = 12
EXPECTED_TAGS_PER_PROFESSIONAL = 4
EXPECTED_NAMES = {
    "Dr. Elena Ramirez",
    "Marcus Lee",
    "Dr. Priya Nandakumar",
    "Jordan Kim",
    "Dr. Simone Carter",
    "Krish Sahni",
    "Dr. Aisha Bello",
    "Connor Tan",
    "Dr. Hannah Brooks",
    "Ethan Walker",
    "Dr. Mei Tanaka",
    "Gabriel Foster",
}


def print_result(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {test_name}{suffix}")


def main():
    initialize_database()
    professionals = get_all_professionals()
    seeded_professionals = [professional for professional in professionals if professional[1] in EXPECTED_NAMES]

    print_result(
        "All expected seeded professionals are present",
        len(seeded_professionals) == EXPECTED_PROFESSIONAL_COUNT,
        f"found {len(seeded_professionals)}, expected {EXPECTED_PROFESSIONAL_COUNT}",
    )

    names = [professional[1] for professional in seeded_professionals]
    unique_names = set(names)
    print_result(
        "Seeded professional names are unique",
        len(unique_names) == len(names),
        f"found {len(names) - len(unique_names)} duplicates",
    )

    extra_professionals = [professional[1] for professional in professionals if professional[1] not in EXPECTED_NAMES]
    print_result(
        "No unexpected professionals are present",
        len(extra_professionals) == 0,
        f"found extras: {', '.join(extra_professionals)}" if extra_professionals else "",
    )

    all_tags_present = True
    for professional in seeded_professionals:
        professional_id = professional[0]
        name = professional[1]
        tags = get_tags_for_professional(professional_id)

        has_expected_tag_count = len(tags) == EXPECTED_TAGS_PER_PROFESSIONAL
        print_result(
            f"{name} has {EXPECTED_TAGS_PER_PROFESSIONAL} tags",
            has_expected_tag_count,
            f"found {len(tags)}",
        )

        if not has_expected_tag_count:
            all_tags_present = False

    print_result("Every seeded professional has the expected tag count", all_tags_present)


if __name__ == "__main__":
    main()
