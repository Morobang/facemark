# Facemark

A generic face recognition attendance system. Register members with a photo, scan faces live via webcam, and mark attendance automatically — deployable for any school, company, or organisation.

---

## What It Does

```
Member walks in
      ↓
Webcam captures their face
      ↓
128-dimensional face vector compared against registered members
      ↓
Match found → attendance marked in database (once per day)
      ↓
Admin queries the REST API for attendance reports
```

---

## Project Structure

```
facemark/
├── engine/
│   └── face_engine.py        # Core recognition logic — register, recognise, mark
├── database/
│   ├── models.py             # Table definitions
│   └── init_db.py            # Creates database on first run
├── api/
│   ├── main.py               # FastAPI app entry point
│   └── routes/
│       ├── members.py        # Register and list members
│       └── attendance.py     # Recognise faces and query records
├── scanner/
│   └── live_scanner.py       # Standalone entrance camera app
├── config/
│   └── settings.py           # Reads .env — single source of config
├── .env.example              # Config template
└── requirements.txt
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Face detection & encoding | `face_recognition` (dlib) |
| Camera | OpenCV |
| Database | SQLite |
| API | FastAPI |
| Config | python-dotenv |
| Logging | Loguru |

---

## Setup

### 1. Prerequisites

- Python 3.11
- CMake
- Visual Studio Build Tools (Windows) or `build-essential` (Linux)

### 2. Clone and install

```bash
git clone https://github.com/Morobang/facemark.git
cd facemark
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Configure

```bash
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
```

Open `.env` and set your organisation details:

```env
ORG_NAME="Your Organisation Name"
MEMBER_LABEL="learner"       # or employee, student, staff
```

### 4. Initialise the database

```bash
python -m database.init_db
```

### 5. Register a member

```python
from engine.face_engine import FaceEngine

engine = FaceEngine()
engine.register_member(
    member_id="STU001",
    full_name="Full Name",
    group_label="Grade 12",
    image_path="photo.jpg"
)
```

---

## Running

### Live camera scanner (entrance station)

```bash
python -m scanner.live_scanner
```

| Key | Action |
|---|---|
| `Q` | Quit |
| `R` | Register new member from camera |
| `S` | Print today's attendance |

### REST API

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/members/register` | Register member with photo |
| GET | `/members/` | List all members |
| POST | `/attendance/recognize` | Recognise face + mark attendance |
| GET | `/attendance/today` | Today's attendance records |
| GET | `/attendance/range` | Attendance between two dates |

---

## How Recognition Works

1. Registration photo is processed — face location detected
2. `face_recognition` generates a 128-dimensional vector unique to that face
3. Vector saved to `encodings/face_encodings.pkl`
4. At scan time — new vector generated from webcam frame
5. Euclidean distance calculated against all saved vectors
6. Closest match below tolerance threshold (default 0.5) = identified
7. Attendance record inserted — one per member per day, duplicates ignored

---

## Configuration

All settings live in `.env`:

| Variable | Default | Description |
|---|---|---|
| `ORG_NAME` | My Organisation | Shown in scanner UI and API title |
| `MEMBER_LABEL` | member | Label used in UI (learner/employee/student) |
| `FACE_TOLERANCE` | 0.5 | Match threshold — lower is stricter |
| `FACE_MODEL` | hog | `hog` for CPU, `cnn` for GPU |
| `SCAN_INTERVAL` | 2 | Seconds between recognition attempts |

---

## Roadmap

- [ ] Connect to school website frontend
- [ ] Admin attendance dashboard
- [ ] Supabase cloud database
- [ ] API deployment to Render
- [ ] Liveness detection (anti-spoofing)
- [ ] PDF/Excel attendance export
- [ ] Multi-location support

---

## Author

Morobang Tshigidimisa  
[GitHub](https://github.com/Morobang)