# ECE445 Smart Mirror Project Handoff

## Project Summary

This repository is an `ECE445` smart mirror prototype for career exploration in the quantum industry.

Core user flow:
1. A user stands in front of the mirror.
2. The system waits in standby.
3. The user uses hand tracking to control a cursor and hover-select `Start Demo Mode`.
4. Once the demo is active, the system performs face matching.
5. The system displays the matched professional's profile information and image.

Current live test setup:
- Real enrolled profiles:
  - `Connor Tan`
  - `Krish Sahni`
- The live demo currently matches against those two enrolled profiles.


## Current Status

### Working

- SQLite database schema and CRUD helpers
- Seed script for dummy professionals
- Read-only seed verification script
- Hand-tracking hover UI
- InsightFace embedding pipeline for still images
- Enrollment of profile images into `face_embeddings`
- Querying top matches from a still image
- Live camera demo:
  - starts in standby
  - uses hand cursor UI to toggle demo on
  - performs face matching only when demo is active
  - shows matched image/profile info on screen

### Not Finished

- No full Raspberry Pi deployment pass yet
- No ToF presence sensor integration
- No polished kiosk-state flow beyond standby/start/reset
- No import pipeline yet for real Google Form data
- No multi-image enrollment strategy per person
- No robust production identity evaluation


## Repository Layout

```text
ECE445_handtracking/
├── README.md
├── LLM_PROJECT_HANDOFF.md
├── assets/
│   └── images/
│       ├── connor_tan.png
│       └── krish_sahni.png
├── hand_tracking/
│   ├── __init__.py
│   ├── live_match_demo.py
│   ├── seed_dummy_professionals.py
│   ├── test_database.py
│   ├── verify_seed_data.py
│   ├── hand_track_pi_style.py
│   ├── hand_track_test.py
│   ├── hand_landmarker.task
│   ├── face_landmarker.task
│   ├── UI_Cursor/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── hand_tracker.py
│   │   ├── user_interface.py
│   │   └── send_data.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_init.py
│   │   ├── db_operations.py
│   │   └── mirror.db
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── embedder.py
│   │   ├── match.py
│   │   ├── enroll_professional.py
│   │   ├── enroll_from_database_paths.py
│   │   ├── query_image_demo.py
│   │   ├── match_demo.py
│   │   └── bootstrap_mock_embeddings.py
│   └── models/
│       └── insightface/
│           └── models/
│               └── buffalo_sc/
│                   ├── det_500m.onnx
│                   └── w600k_mbf.onnx
```


## Product Architecture

### 1. Database Layer

Purpose:
- store professional profiles
- store profile tags
- store interaction logs
- store face embeddings for matching

Files:
- [hand_tracking/database/db_init.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/database/db_init.py)
- [hand_tracking/database/db_operations.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/database/db_operations.py)

Tables:
- `professionals`
- `profile_tags`
- `interaction_logs`
- `face_embeddings`

Important `face_embeddings` fields:
- `professional_id`
- `model_name`
- `embedding_json`


### 2. Seed / Test Data Layer

Files:
- [hand_tracking/seed_dummy_professionals.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/seed_dummy_professionals.py)
- [hand_tracking/verify_seed_data.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/verify_seed_data.py)
- [hand_tracking/test_database.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/test_database.py)

Important behavior:
- `seed_dummy_professionals.py`
  - initializes DB
  - clears `face_embeddings`, `profile_tags`, `interaction_logs`, and `professionals`
  - inserts 12 dummy professionals
- `verify_seed_data.py`
  - read-only verification for seeded profiles
- `test_database.py`
  - mutates the DB
  - inserts a sample record for CRUD testing
  - should not be treated as read-only validation


### 3. Hand Cursor UI

Files:
- [hand_tracking/UI_Cursor/hand_tracker.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/UI_Cursor/hand_tracker.py)
- [hand_tracking/UI_Cursor/user_interface.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/UI_Cursor/user_interface.py)
- [hand_tracking/UI_Cursor/main.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/UI_Cursor/main.py)

Behavior:
- webcam feed
- MediaPipe hand tracking
- index-fingertip cursor
- hover-to-select buttons
- buttons:
  - `Toggle Overlay`
  - `Start Demo Mode`
  - `Reset / Clear`

Notes:
- `main.py` is the older modular hand UI demo
- it still includes Arduino serial logic via `send_data.py`
- it is separate from the live face-matching demo


### 4. Matching Layer

Files:
- [hand_tracking/matching/embedder.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/embedder.py)
- [hand_tracking/matching/match.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/match.py)
- [hand_tracking/matching/enroll_professional.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/enroll_professional.py)
- [hand_tracking/matching/enroll_from_database_paths.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/enroll_from_database_paths.py)
- [hand_tracking/matching/query_image_demo.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/query_image_demo.py)

Current matching architecture:
- default backend: `InsightFace`
- fallback backend: `MediaPipe` landmark-based embedding
- matcher: cosine similarity over stored embeddings

Important detail:
- The MediaPipe landmark embedding path exists only as fallback/plumbing.
- The real usable identity backend is now InsightFace.


### 5. Live Integrated Demo

File:
- [hand_tracking/live_match_demo.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/live_match_demo.py)

Behavior:
- opens webcam
- shows hand-tracking cursor UI immediately
- starts in standby
- user hover-selects `Start Demo Mode`
- only then performs face matching every ~1.5 seconds
- displays:
  - top matched image
  - name
  - title
  - organization
  - quantum area
  - short bio
  - fun fact
  - ranked matches list

Important UX rule:
- standby first, match only after explicit hover-toggle


## Database Schema

### `professionals`

Fields:
- `id`
- `name`
- `title`
- `organization`
- `quantum_area`
- `short_bio`
- `long_bio`
- `image_path`
- `fun_fact`
- `video_url`
- `created_at`

### `profile_tags`

Fields:
- `id`
- `professional_id`
- `tag`

### `interaction_logs`

Fields:
- `id`
- `event_type`
- `matched_professional_id`
- `notes`
- `created_at`

### `face_embeddings`

Fields:
- `id`
- `professional_id`
- `model_name`
- `embedding_json`
- `created_at`


## Current Seeded Professionals

There are 12 seeded professionals. Two names were customized to match local testing:
- `Connor Tan`
- `Krish Sahni`

Those replaced:
- `Leo Chen` -> `Connor Tan`
- `Noah Patel` -> `Krish Sahni`

Current image paths for the real local test users:
- `assets/images/connor_tan.png`
- `assets/images/krish_sahni.png`


## Matching Backend Details

### Default Backend: InsightFace

Used for:
- enrollment
- still-image query
- live demo matching

Implementation:
- `InsightFaceEmbedder` in [hand_tracking/matching/embedder.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/embedder.py)

Model pack:
- `buffalo_sc`

Stored under:
- [hand_tracking/models/insightface/models/buffalo_sc](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/models/insightface/models/buffalo_sc)

Files:
- `det_500m.onnx`
- `w600k_mbf.onnx`

Why this was chosen:
- MediaPipe landmark embeddings were too similar across different people
- InsightFace produced much better separation for the two real test users


### Fallback Backend: MediaPipe

Still available in:
- `create_embedder("mediapipe")`

Use case:
- fallback / debugging only

Why not primary:
- it gave poor identity separation
- example result was roughly:
  - self-match: `1.0000`
  - different person: `0.9940`

That was too weak for actual recognition.


## Important Commands

### 1. Seed the database

```bash
python3 hand_tracking/seed_dummy_professionals.py
```

### 2. Verify seeded data without modifying DB

```bash
python3 hand_tracking/verify_seed_data.py
```

### 3. Run CRUD DB test

```bash
cd hand_tracking
python3 test_database.py
```

### 4. Enroll available images from DB paths

```bash
.venv/bin/python -m hand_tracking.matching.enroll_from_database_paths
```

### 5. Query a still image

```bash
.venv/bin/python -m hand_tracking.matching.query_image_demo --image-path assets/images/connor_tan.png --top-k 3
```

### 6. Run live hover-to-start face matching demo

```bash
.venv/bin/python -m hand_tracking.live_match_demo
```


## Known Good Matching Behavior

After enrolling the two real images, these results were observed with InsightFace:

```text
Connor query:
1. Connor Tan - score=1.0000
2. Krish Sahni - score=0.1266

Krish query:
1. Krish Sahni - score=1.0000
2. Connor Tan - score=0.1266
```

This is currently the strongest signal that the matching stack is working correctly.


## Current UI Behavior

### Standby State

- Camera feed is open
- Hand cursor is active
- Match panel says standby / hover to start
- No face matching is performed

### Active State

- Triggered by hover-selecting `Start Demo Mode`
- Face matching runs every `1.5` seconds
- Right-side black panel shows the best profile card

### Reset State

- Triggered by hover-selecting `Reset / Clear`
- Clears last matches
- Stops matching
- Returns to standby


## Important Implementation Decisions

### Why the live demo is separate from `UI_Cursor/main.py`

`UI_Cursor/main.py` is still tied to Arduino/serial behavior and an older UI test path.

The new integrated face-matching experience was added as:
- [hand_tracking/live_match_demo.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/live_match_demo.py)

This avoids breaking the older module while allowing the smart mirror flow to evolve independently.


### Why `face_embeddings` needed to be cleared on reseed

There was a bug earlier where reseeding only cleared `professionals`, `profile_tags`, and `interaction_logs`, but not `face_embeddings`.

That created stale embeddings for deleted professional IDs and caused ranked results to collapse unexpectedly.

This has been fixed in:
- [hand_tracking/seed_dummy_professionals.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/seed_dummy_professionals.py)


### Why InsightFace model files were manually cached

`insightface` was installed into the venv, but its model pack download from GitHub failed in the restricted environment.

The `buffalo_sc` model files were then placed in:
- [hand_tracking/models/insightface/models/buffalo_sc](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/models/insightface/models/buffalo_sc)

This made the backend usable offline within the repo.


## Known Limitations

- Only two real enrolled users currently exist
- Most seeded professionals still point to non-existent placeholder image paths
- The UI card currently only shows the top match as a full profile card
- There is no camera-capture confirmation step before matching
- Matching runs directly on the live camera frame
- No temporal smoothing or majority-vote logic yet for repeated match stability
- `cv2.CAP_AVFOUNDATION` is Mac-specific; Raspberry Pi deployment will need a different camera backend
- `UI_Cursor/main.py` still uses a hardcoded Arduino port (`COM5`) from older demo work


## Recommended Next Steps

### Short Term

1. Add a short "position your face" state after `Start Demo Mode`.
2. Add match stability logic:
   - sample multiple frames
   - take majority vote or average score
3. Add more real enrolled images per person.
4. Add more real professional headshots to the DB.

### Medium Term

5. Build a full-screen mirrored kiosk layout.
6. Add a transition from match card to richer biography/profile page.
7. Add presence detection / wake-on-user flow.
8. Add import pipeline from structured real data source.

### Long Term

9. Optimize for Raspberry Pi.
10. Evaluate whether InsightFace runtime/performance is acceptable on target hardware.
11. If needed, replace or quantize the recognition model for Pi deployment.


## If Another LLM Continues This Project

The highest-signal entry points are:
- [hand_tracking/live_match_demo.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/live_match_demo.py)
- [hand_tracking/matching/embedder.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/embedder.py)
- [hand_tracking/matching/match.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/matching/match.py)
- [hand_tracking/database/db_operations.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/database/db_operations.py)
- [hand_tracking/seed_dummy_professionals.py](/Users/connortan/Desktop/ECE445_handtracking/hand_tracking/seed_dummy_professionals.py)

Suggested first question for any follow-on work:
- "Are we optimizing the current demo UX, expanding the profile dataset, or preparing for Raspberry Pi deployment?"

