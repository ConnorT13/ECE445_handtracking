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


def print_result(test_name, passed):
    if passed:
        print(f"[PASS] {test_name}")
    else:
        print(f"[FAIL] {test_name}")


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

    log_interaction(
        event_type="match_shown",
        matched_professional_id=professional_id,
        notes="Demo match for testing UI output."
    )

    # Test 1: inserted ID is valid
    print_result("Professional ID returned", professional_id is not None)

    # Test 2: retrieve by ID
    professional = get_professional_by_id(professional_id)
    print_result("Retrieve professional by ID", professional is not None)

    if professional is not None:
        print_result("Correct name retrieved", professional[1] == "Dr. Maya Patel")
        print_result("Correct title retrieved", professional[2] == "Quantum Hardware Engineer")
        print_result("Correct organization retrieved", professional[3] == "Quantum Labs")

    # Test 3: retrieve all professionals
    all_professionals = get_all_professionals()
    print_result("Retrieve all professionals", len(all_professionals) > 0)

    # Test 4: retrieve tags
    tags = get_tags_for_professional(professional_id)
    print_result("Retrieve tags for professional", len(tags) == 3)
    print_result("Tag 'hardware' exists", "hardware" in tags)
    print_result("Tag 'hands_on' exists", "hands_on" in tags)
    print_result("Tag 'engineering' exists", "engineering" in tags)

    # Test 5: retrieve professionals by tag
    hardware_professionals = get_professionals_by_tag("hardware")
    hardware_ids = [row[0] for row in hardware_professionals]
    print_result("Retrieve professionals by tag", professional_id in hardware_ids)

    # Test 6: invalid ID retrieval
    invalid_professional = get_professional_by_id(999999)
    print_result("Invalid ID returns None", invalid_professional is None)

    # Test 7: nonexistent tag retrieval
    fake_tag_results = get_professionals_by_tag("not_a_real_tag")
    print_result("Nonexistent tag returns empty list", len(fake_tag_results) == 0)

    # Test 8: recent logs retrieval
    logs = get_recent_logs()
    print_result("Retrieve recent logs", len(logs) > 0)

    if len(logs) > 0:
        print_result("Most recent log has correct event type", logs[0][1] == "match_shown")


if __name__ == "__main__":
    main()