from database.db_init import initialize_database
from database.db_operations import (
    add_professional,
    add_tag_to_professional,
    get_all_professionals,
    get_professional_by_id,
    get_tags_for_professional,
    get_professionals_by_tag,
    log_interaction,
    get_recent_logs
)


def main():
    initialize_database()

    professional_id = add_professional(
        name="Dr. Maya Patel",
        title="Quantum Hardware Engineer",
        organization="Quantum Labs",
        quantum_area="Quantum Hardware",
        short_bio="Builds machines that help power quantum computers.",
        long_bio="Dr. Patel works on the hardware side of quantum systems, helping design and test the physical devices that make quantum computing possible.",
        image_path="assets/images/maya_patel.png",
        fun_fact="She loved building circuits when she was younger.",
        video_url="https://example.com/maya-video"
    )

    add_tag_to_professional(professional_id, "hardware")
    add_tag_to_professional(professional_id, "hands_on")
    add_tag_to_professional(professional_id, "engineering")

    print("Inserted professional ID:", professional_id)

    print("\nAll professionals:")
    for professional in get_all_professionals():
        print(professional)

    print("\nProfessional by ID:")
    print(get_professional_by_id(professional_id))

    print("\nTags for professional:")
    print(get_tags_for_professional(professional_id))

    print("\nProfessionals with tag 'hardware':")
    for professional in get_professionals_by_tag("hardware"):
        print(professional)

    log_interaction(
        event_type="match_shown",
        matched_professional_id=professional_id,
        notes="Demo match for testing UI output."
    )

    print("\nRecent logs:")
    for log in get_recent_logs():
        print(log)


if __name__ == "__main__":
    main()