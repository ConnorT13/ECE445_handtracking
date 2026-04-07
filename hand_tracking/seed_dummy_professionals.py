from database.db_init import get_database_path, initialize_database
from database.db_operations import add_professional, add_tag_to_professional
import sqlite3


DUMMY_PROFESSIONALS = [
    {
        "name": "Dr. Elena Ramirez",
        "title": "Quantum Hardware Engineer",
        "organization": "Midwest Quantum Lab",
        "quantum_area": "Quantum Hardware",
        "short_bio": "Builds and tests the chips that help quantum computers work.",
        "long_bio": "Dr. Ramirez designs superconducting hardware and helps teams turn lab prototypes into reliable quantum devices for experiments and future products.",
        "image_path": "assets/images/elena_ramirez.png",
        "fun_fact": "She started out repairing old radios with her grandfather.",
        "video_url": "https://example.com/elena-ramirez",
        "tags": ["hardware", "hands_on", "engineering", "experimental"],
    },
    {
        "name": "Marcus Lee",
        "title": "Quantum Software Developer",
        "organization": "Qubit Stack",
        "quantum_area": "Quantum Software",
        "short_bio": "Writes code that helps people run programs on quantum computers.",
        "long_bio": "Marcus creates tools that make it easier for scientists and students to build, test, and understand quantum algorithms on real systems.",
        "image_path": "assets/images/marcus_lee.png",
        "fun_fact": "He built his first video game in middle school.",
        "video_url": "https://example.com/marcus-lee",
        "tags": ["software", "coding", "problem_solving", "algorithms"],
    },
    {
        "name": "Dr. Priya Nandakumar",
        "title": "Quantum Research Scientist",
        "organization": "Photon Research Center",
        "quantum_area": "Quantum Sensing",
        "short_bio": "Studies how quantum science can be used to make super-precise sensors.",
        "long_bio": "Dr. Nandakumar leads experiments on quantum sensing and works with students to turn difficult physics ideas into practical measurement tools.",
        "image_path": "assets/images/priya_nandakumar.png",
        "fun_fact": "She loves explaining science with kitchen experiments.",
        "video_url": "https://example.com/priya-nandakumar",
        "tags": ["research", "experimental", "sensing", "physics"],
    },
    {
        "name": "Jordan Kim",
        "title": "Cryogenics Technician",
        "organization": "Illinois Quantum Systems",
        "quantum_area": "Quantum Hardware",
        "short_bio": "Keeps quantum machines extremely cold so they can run correctly.",
        "long_bio": "Jordan maintains dilution refrigerators, checks wiring, and solves lab hardware issues that affect quantum processor performance.",
        "image_path": "assets/images/jordan_kim.png",
        "fun_fact": "They once built a mini weather station at home.",
        "video_url": "https://example.com/jordan-kim",
        "tags": ["hardware", "hands_on", "technician", "experimental"],
    },
    {
        "name": "Dr. Simone Carter",
        "title": "Quantum Algorithm Researcher",
        "organization": "Lakeview Institute of Technology",
        "quantum_area": "Quantum Algorithms",
        "short_bio": "Designs new ways for quantum computers to solve hard problems.",
        "long_bio": "Dr. Carter studies how quantum algorithms can speed up chemistry and optimization tasks and helps translate theory into testable software.",
        "image_path": "assets/images/simone_carter.png",
        "fun_fact": "She enjoys puzzle hunts and escape rooms.",
        "video_url": "https://example.com/simone-carter",
        "tags": ["theory", "research", "algorithms", "math"],
    },
    {
        "name": "Krish Sahni",
        "title": "Quantum Device Fabrication Engineer",
        "organization": "NanoFab Quantum",
        "quantum_area": "Quantum Hardware",
        "short_bio": "Helps manufacture tiny parts used inside quantum devices.",
        "long_bio": "Noah works in cleanroom environments to fabricate delicate structures that support quantum chips, photonic components, and experimental devices.",
        "image_path": "assets/images/krish_sahni.png",
        "fun_fact": "He learned microscopy by photographing insects.",
        "video_url": "https://example.com/noah-patel",
        "tags": ["hardware", "fabrication", "engineering", "hands_on"],
    },
    {
        "name": "Dr. Aisha Bello",
        "title": "Quantum Education Specialist",
        "organization": "National Quantum Outreach Network",
        "quantum_area": "Quantum Education",
        "short_bio": "Creates lessons and activities that make quantum ideas easier to understand.",
        "long_bio": "Dr. Bello develops classroom programs, museum demos, and teacher workshops that connect quantum careers to students' everyday interests.",
        "image_path": "assets/images/aisha_bello.png",
        "fun_fact": "She uses comic books to teach science vocabulary.",
        "video_url": "https://example.com/aisha-bello",
        "tags": ["education", "communication", "outreach", "mentoring"],
    },
    {
        "name": "Connor Tan",
        "title": "Quantum Control Engineer",
        "organization": "Pulse Logic Labs",
        "quantum_area": "Quantum Control",
        "short_bio": "Builds the signals and electronics that tell qubits what to do.",
        "long_bio": "Leo tunes microwave pulses, calibrates control systems, and works closely with hardware and software teams to improve qubit performance.",
        "image_path": "assets/images/connor_tan.png",
        "fun_fact": "He is a drummer and thinks a lot about timing and rhythm.",
        "video_url": "https://example.com/leo-chen",
        "tags": ["hardware", "control_systems", "engineering", "problem_solving"],
    },
    {
        "name": "Dr. Hannah Brooks",
        "title": "Quantum Chemist",
        "organization": "Molecular Futures Lab",
        "quantum_area": "Quantum Chemistry",
        "short_bio": "Uses quantum computers to study how molecules behave.",
        "long_bio": "Dr. Brooks combines chemistry and computation to test how quantum methods could help discover new medicines and materials.",
        "image_path": "assets/images/hannah_brooks.png",
        "fun_fact": "She collects perfume samples to learn about molecules.",
        "video_url": "https://example.com/hannah-brooks",
        "tags": ["chemistry", "research", "software", "applications"],
    },
    {
        "name": "Ethan Walker",
        "title": "Quantum Systems Integrator",
        "organization": "Quantum Horizon",
        "quantum_area": "Quantum Systems",
        "short_bio": "Makes sure many parts of a quantum system work together smoothly.",
        "long_bio": "Ethan connects lasers, electronics, software, and hardware into one working platform and troubleshoots issues across the full system.",
        "image_path": "assets/images/ethan_walker.png",
        "fun_fact": "He likes restoring bicycles because every part has to fit together.",
        "video_url": "https://example.com/ethan-walker",
        "tags": ["systems", "integration", "hands_on", "engineering"],
    },
    {
        "name": "Dr. Mei Tanaka",
        "title": "Quantum Communications Scientist",
        "organization": "Secure Light Institute",
        "quantum_area": "Quantum Communication",
        "short_bio": "Studies how quantum technology can help send information more securely.",
        "long_bio": "Dr. Tanaka works on quantum networks and secure communication experiments that use photons to protect data in new ways.",
        "image_path": "assets/images/mei_tanaka.png",
        "fun_fact": "She enjoys amateur astronomy and late-night telescope sessions.",
        "video_url": "https://example.com/mei-tanaka",
        "tags": ["communication", "photonics", "research", "physics"],
    },
    {
        "name": "Gabriel Foster",
        "title": "Quantum Product Designer",
        "organization": "Q-Bridge Technologies",
        "quantum_area": "Quantum Applications",
        "short_bio": "Helps turn advanced quantum ideas into tools people can actually use.",
        "long_bio": "Gabriel works with scientists, engineers, and customers to shape software products that make quantum platforms easier to access and understand.",
        "image_path": "assets/images/gabriel_foster.png",
        "fun_fact": "He sketches app ideas on sticky notes before opening a laptop.",
        "video_url": "https://example.com/gabriel-foster",
        "tags": ["product", "software", "communication", "design"],
    },
]


def reset_database():
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM face_embeddings")
    cursor.execute("DELETE FROM profile_tags")
    cursor.execute("DELETE FROM interaction_logs")
    cursor.execute("DELETE FROM professionals")

    connection.commit()
    connection.close()


def seed_database():
    initialize_database()
    reset_database()

    for professional in DUMMY_PROFESSIONALS:
        professional_id = add_professional(
            name=professional["name"],
            title=professional["title"],
            organization=professional["organization"],
            quantum_area=professional["quantum_area"],
            short_bio=professional["short_bio"],
            long_bio=professional["long_bio"],
            image_path=professional["image_path"],
            fun_fact=professional["fun_fact"],
            video_url=professional["video_url"],
        )

        for tag in professional["tags"]:
            add_tag_to_professional(professional_id, tag)


def main():
    seed_database()
    print(f"Seeded {len(DUMMY_PROFESSIONALS)} dummy professionals into mirror.db")


if __name__ == "__main__":
    main()
