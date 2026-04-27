import os

from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import (
    add_professional,
    add_tag_to_professional,
    get_connection,
)

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")


def _image(filename):
    return os.path.join(IMAGES_DIR, filename)


REAL_PROFESSIONALS = [
    {
        "name": "Nathan Arnold",
        "title": "CEO",
        "organization": "Photon Queue Inc.",
        "quantum_area": "Quantum Entrepreneur",
        "short_bio": "I run a young quantum hardware startup.",
        "long_bio": (
            "I speak with investors, meet with prospective hires, meet with my team, "
            "write documents, decide on company strategies, and make sure things get done."
        ),
        "image_path": _image("nathan_arnold.jpg"),
        "fun_fact": None,
        "video_url": None,
        "tags": ["Quantum Scientist", "Quantum Hardware", "Quantum Entrepreneur"],
    },
    {
        "name": "Aaron Fluitt",
        "title": "Senior Director, Technology Partnerships",
        "organization": "PsiQuantum",
        "quantum_area": "Quantum Collaboration Building",
        "short_bio": (
            "I build and lead PsiQuantum's scientific partnerships platform. I engage with "
            "universities, national laboratories, research centers, companies, and science "
            "agencies who are interested in collaborating with PsiQuantum."
        ),
        "long_bio": (
            "I identify and develop opportunities for the company to collaborate with other "
            "organizations on research, education, and workforce development, with the goal "
            "of increasing the utility of fault-tolerant quantum computing. I meet with many "
            "people who are developing technology for quantum computers, scientific or commercial "
            "applications of quantum computing, or who are involved in education or workforce "
            "development. Collaborations may involve joint proposals, technical programming, "
            "funded projects, outreach, or other activities."
        ),
        "image_path": _image("aaron_fluitt.jpg"),
        "fun_fact": (
            "The quantum computing industry needs people from many different technical and "
            "non-technical backgrounds. My scientific training wasn't in quantum information "
            "science, and in fact it was closer to chemistry -- a field that, as it turns out, "
            "will be one of the first to benefit from fault-tolerant quantum computers. "
            "You never know where your interests will lead you."
        ),
        "video_url": None,
        "tags": ["Quantum Collaboration Building"],
    },
    {
        "name": "Colin Lualdi",
        "title": "Postdoctoral Research Associate",
        "organization": "Kwiat Quantum Information Group, University of Illinois Urbana-Champaign",
        "quantum_area": "Quantum Scientist",
        "short_bio": "I explore how we can use quantum forms of light to develop new technologies.",
        "long_bio": (
            "I build and perform experiments in the lab, both by myself and in collaboration "
            "with other scientists. I also analyze the data that I collect and prepare them "
            "for presentations and publications."
        ),
        "image_path": _image("colin_lualdi.jpg"),
        "fun_fact": (
            "Because quantum can be highly interdisciplinary, I encourage you to take the "
            "opportunity to learn about some new field as a part of your work in quantum!"
        ),
        "video_url": None,
        "tags": ["Quantum Scientist", "Quantum Hardware"],
    },
    {
        "name": "Ujaan Purakayastha",
        "title": "Graduate Research Assistant",
        "organization": "Kwiat Lab, UIUC",
        "quantum_area": "Quantum Student",
        "short_bio": (
            "I work in Experimental Quantum Optics. Specifically, I study how to encode, "
            "manipulate, and preserve quantum information stored in single particles of light (photons)."
        ),
        "long_bio": (
            "Designing and building optical setups in lab, collecting and analyzing data, "
            "and sharing my findings with colleagues and the community at large."
        ),
        "image_path": _image("ujaan_purakayastha.jpg"),
        "fun_fact": (
            "What drew me to this field was how you could 'squeeze' light to boost measurement "
            "precision -- they did this in LIGO to measure gravitational waves!"
        ),
        "video_url": None,
        "tags": ["Quantum Scientist", "Quantum Hardware", "Quantum Student"],
    },
    {
        "name": "Kristina Meier, PhD",
        "title": "Staff Scientist",
        "organization": "Los Alamos National Lab",
        "quantum_area": "Quantum Scientist",
        "short_bio": "I use optics and quantum technology to develop sensors and imagers for making our world safer.",
        "long_bio": (
            "My day-to-day is split between laboratory work, field work, and administrative work "
            "(including writing proposals!). For me, the mix works really well, but I know others "
            "who prefer to stick to one thing. In the lab, I'm typically building something with "
            "optics that is meant to be used in some larger system -- many times for systems that "
            "will be used in the field (such as at telescope observatories or in large open spaces "
            "for long free-space laser beam paths)."
        ),
        "image_path": _image("kristina_meier.jpg"),
        "fun_fact": (
            "I have made it quite far in my career with a healthy dose of persistence. However, "
            "you have to make sure that your persistence can pivot when the goal changes."
        ),
        "video_url": None,
        "tags": ["Quantum Scientist", "Quantum Hardware"],
    },
    {
        "name": "Andrew Conrad",
        "title": "Quantum Cryptography Researcher",
        "organization": "JPMorganChase",
        "quantum_area": "Quantum Engineer",
        "short_bio": "I work on building quantum systems that make banks more secure.",
        "long_bio": "I work on building quantum systems that make banks more secure.",
        "image_path": _image("andrew_conrad.jpg"),
        "fun_fact": (
            "I fell in love with quantum after learning that quantum particles could be in two "
            "different places at the same time (called quantum superposition). This was a "
            "beautiful mystery that compelled me to learn more."
        ),
        "video_url": None,
        "tags": ["Quantum Scientist", "Quantum Hardware", "Quantum Engineer"],
    },
]


def _professional_exists(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM professionals WHERE name = ?", (name,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def populate():
    initialize_database()

    for p in REAL_PROFESSIONALS:
        existing_id = _professional_exists(p["name"])
        if existing_id is not None:
            print(f"  SKIP  {p['name']} (already in DB, id={existing_id})")
            continue

        prof_id = add_professional(
            name=p["name"],
            title=p["title"],
            organization=p["organization"],
            quantum_area=p["quantum_area"],
            short_bio=p["short_bio"],
            long_bio=p["long_bio"],
            image_path=p["image_path"],
            fun_fact=p["fun_fact"],
            video_url=p["video_url"],
        )

        for tag in p["tags"]:
            add_tag_to_professional(prof_id, tag)

        print(f"  ADDED {p['name']} (id={prof_id})  tags={p['tags']}")

    print("Done.")


if __name__ == "__main__":
    populate()
