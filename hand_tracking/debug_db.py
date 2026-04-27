import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "mirror.db")


def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("=" * 60)
    print(f"DATABASE: {DB_PATH}")
    print("=" * 60)

    # ── 1. Raw quantum_area values (repr for hidden spaces / casing) ──
    print("\n── DISTINCT quantum_area VALUES (raw repr) ──")
    cur.execute(
        "SELECT DISTINCT quantum_area FROM professionals ORDER BY quantum_area"
    )
    for (area,) in cur.fetchall():
        print(f"  {repr(area)}")

    # ── 2. Per-career breakdown ──────────────────────────────────────
    print("\n── PER-CAREER BREAKDOWN ──")

    cur.execute(
        "SELECT DISTINCT quantum_area FROM professionals ORDER BY quantum_area"
    )
    areas = [row[0] for row in cur.fetchall()]

    for area in areas:
        cur.execute(
            "SELECT id, name FROM professionals WHERE quantum_area = ? ORDER BY name",
            (area,),
        )
        professionals = cur.fetchall()
        total = len(professionals)

        ids = [p[0] for p in professionals]
        placeholders = ",".join("?" * len(ids))
        cur.execute(
            f"SELECT DISTINCT professional_id FROM face_embeddings WHERE professional_id IN ({placeholders})",
            ids,
        )
        embedded_ids = {row[0] for row in cur.fetchall()}

        with_embedding = len(embedded_ids)
        without_embedding = total - with_embedding
        missing = [(pid, name) for pid, name in professionals if pid not in embedded_ids]

        flag = "  *** MISSING EMBEDDINGS ***" if without_embedding > 0 else ""
        print(f"\n  Career : {area!r}")
        print(f"  Total  : {total}")
        print(f"  With embedding   : {with_embedding}")
        print(f"  Without embedding: {without_embedding}{flag}")
        if missing:
            for pid, name in missing:
                print(f"    !! id={pid}  {name}")

    # ── 3. Totals ────────────────────────────────────────────────────
    print("\n── TOTALS ──")

    cur.execute("SELECT COUNT(*) FROM professionals")
    total_profs = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(DISTINCT professional_id) FROM face_embeddings"
    )
    total_with = cur.fetchone()[0]

    total_without = total_profs - total_with
    print(f"  Total professionals : {total_profs}")
    print(f"  With embeddings     : {total_with}")
    print(f"  Without embeddings  : {total_without}")
    if total_without > 0:
        print("  *** Some professionals have no face embedding and cannot be matched. ***")

    print("\n" + "=" * 60)
    con.close()


if __name__ == "__main__":
    main()
