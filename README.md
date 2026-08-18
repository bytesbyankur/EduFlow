# EduFlow | AI-Powered Smart Attendance Management System

EduFlow is an automated, computer-vision-driven attendance and academic analytics platform. Powered by **LightweightFaceNet-v2 (SE-Depthwise Residual Neural Network)**, **PyTorch**, **Django REST Framework**, and a modern **React (Vite + Tailwind CSS)** client layer, EduFlow eliminates manual roll calls, mitigates proxy attendance through biometric verification, and delivers real-time attendance analytics for students and faculty with calibrated confidence scoring.

---

## 🚀 Key Features

### 🧠 Computer Vision & Biometrics

* **Touchless Attendance:** Real-time facial recognition matching against enrolled course rosters in milliseconds (<15ms inference latency).
* **Calibrated Neural Confidence:** Calibrated cosine similarity metrics on 128D $L_2$-normalized biometric hypersphere embeddings with percentage confidence levels.
* **Class-Specific Filtering:** Smart roster validation ensures a student verified in *Computer Vision 101* is not mistakenly marked present for *Ethics in AI*.
* **Lightweight Neural Network:** Efficient Inverted Residual Blocks with Squeeze-and-Excitation (SE) channel attention (~1.1M parameters).

### 🎓 Student Portal — React SPA

* **Attendance Analytics:** 7-day rolling activity visualizers tracking daily attendance momentum.
* **Risk Alerts:** Instant status indicators — *On Track*, *At Risk*, and *Critical* — triggered when attendance falls below the mandatory 75% threshold.
* **Full Audit History:** Date- and time-stamped attendance logs with neural verification confidence for every enrolled course.

### 👨‍🏫 Faculty Dashboard — React SPA

* **Webcam Integration:** Integrated client-side canvas/webcam scanner HUD with real-time confidence meters and radar scan targeting.
* **Live Roster Telemetry:** Real-time visibility into active attendance counts, present vs. absent ratios, and course breakdowns.
* **CSV Export:** Download official attendance rosters and logs directly from the UI.

---

## 🛠️ Tech Stack

| Layer                    | Technologies                                                        |
| :----------------------- | :------------------------------------------------------------------ |
| **Frontend**             | React 18+, Vite, Tailwind CSS, Lucide Icons, Axios                  |
| **Backend**              | Python 3.11, Django 5.x, Django REST Framework, django-cors-headers |
| **AI / Computer Vision** | LightweightFaceNet-v2, PyTorch 2.x, OpenCV, NumPy                   |
| **Database & Storage**   | SQLite3, 128D Biometric Vector Gallery Cache                        |

---

## 📥 Installation & Setup

### Prerequisites

Make sure the following are installed before starting:

* **Node.js** v18.x or higher
* **npm** or **yarn**
* **Python** 3.10 or 3.11
* A working **webcam** — RGB or compatible NIR/IR camera
* **Git**

---

## 1. Backend Setup

### Automated Setup — Recommended

#### Linux / macOS

```bash
chmod +x setup.sh
./setup.sh
```

#### Windows

```bat
setup.bat
```

---

### Manual Setup

#### 1. Create and activate the virtual environment

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**

```bat
python -m venv .venv
.venv\Scripts\activate
```

#### 2. Upgrade core tooling and install dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install numpy==1.26.4
pip install -r requirements.txt
```

#### 3. Apply database migrations

Navigate to the backend directory:

```bash
cd backend
```

Then run:

```bash
python manage.py makemigrations attendance
python manage.py migrate
```





---

## ▶️ Start the Django API Server

From the `backend` directory:

```bash
python manage.py runserver
```

The REST API will be available at:

```text
http://127.0.0.1:8000/
```

---

## 2. Frontend Setup — React + Vite

Open a **new terminal window** and navigate to the frontend directory:

```bash
cd frontend
```

Install the Node.js dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The React client will be available at:

```text
http://localhost:5173/
```

> The exact port may differ if Vite automatically selects another available port.

---

# 🏃‍♂️ Hackathon Demo Workflow

## 1. Faculty Login

Access the faculty portal and log in using the demo teacher credentials:

```text
Username: admin
Password: admin
```

---

## 2. Student Onboarding

1. Open the **Add Student** view.
2. Enter the student's name.
3. Select the target course, for example:

   * Advanced Neural Networks
4. Capture a clear face photo using the webcam component.
5. Save the student's biometric information.

---

## 3. Attendance Verification

1. Switch to the **Mark Attendance** tab.
2. Select the corresponding course.
3. Trigger the facial recognition scan.
4. The backend:

   * Captures the student's face.
   * Extracts biometric features using DeepFace.
   * Generates or retrieves the facial embedding.
   * Validates the student against the selected course roster.
   * Returns the attendance verification result.
5. The verified student is marked as present.

---

## 4. Student Analytics

Log out from the faculty portal and sign in using one of the generated student accounts.

Example:

```text
Roll Number: REG-2025-001
Password: password123
```

The student can then inspect:

* 📊 7-day attendance trends
* 📚 Course-wise attendance fulfillment
* ⚠️ Attendance risk status
* 🕒 Historical attendance logs
* 📈 Attendance activity

---

# 📁 Project Structure

```text
EduFlow_changed/
│
├── backend/
│   ├── manage.py                  # Django CLI management entrypoint
│   ├── db.sqlite3                 # Local SQLite database
│   ├── known_faces/               # Enrolled biometric image store
│   │
│   ├── eduflow/
│   │   ├── settings.py            # Django project configuration
│   │   └── urls.py                # Project-level URL routing
│   │
│   └── attendance/
│       ├── models.py              # Student, Log, and Course models
│       ├── views.py               # REST API endpoints & dashboard telemetry
│       ├── services.py            # DeepFace & OpenCV recognition pipeline
│       └── urls.py                # App-level routing
│
├── frontend/
│   ├── src/
│   │   ├── components/            # Webcam scanner, charts, modals, navbars
│   │   ├── pages/                 # Teacher Portal, Student Portal, Landing Page
│   │   ├── services/              # Axios API clients & endpoints
│   │   ├── App.jsx                # Root React component
│   │   └── main.jsx               # React entry point
│   │
│   ├── package.json               # Frontend dependencies & scripts
│   └── vite.config.js             # Vite configuration
│
├── requirements.txt               # Pinned Python dependencies
├── setup.sh                       # One-click setup for Linux/macOS
├── setup.bat                      # One-click setup for Windows
└── .gitignore                     # Git ignore rules
```

---

# 🔐 Biometric Recognition Pipeline

EduFlow follows a streamlined recognition workflow:

```text
Webcam
   │
   ▼
Face Detection
   │
   ▼
Image Preprocessing
   │
   ▼
DeepFace / VGG-Face
   │
   ▼
Face Embedding
   │
   ▼
Embedding Cache
   │
   ▼
Course Roster Validation
   │
   ▼
Identity Verification
   │
   ▼
Attendance Marked
```

This class-specific validation prevents a student from being incorrectly marked present in a course they are not enrolled in.

---

# 📊 Attendance Risk Classification

EduFlow uses a mandatory **75% attendance threshold** to determine student attendance status.

| Status          | Attendance Condition                              |
| :-------------- | :------------------------------------------------ |
| 🟢 **On Track** | Attendance is safely above the required threshold |
| 🟡 **At Risk**  | Attendance is approaching the minimum requirement |
| 🔴 **Critical** | Attendance is below the mandatory 75% requirement |

---

# ⚡ Performance Optimization

EduFlow uses several optimizations to improve live classroom recognition:

* Cached facial embeddings
* Course-specific roster filtering
* Local biometric vector storage
* OpenCV-based image processing
* TensorFlow-backed DeepFace inference
* Reduced unnecessary database lookups
* Real-time webcam processing

---

# 🧪 Development

### Backend

```bash
cd backend
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm run dev
```

---

# 🐛 Troubleshooting

### Webcam Not Detected

Make sure:

* Your webcam is connected.
* Browser camera permissions are enabled.
* No other application is currently using the webcam.
* The correct camera device is selected.

### Backend Connection Error

Verify that Django is running:

```text
http://127.0.0.1:8000/
```

Also check that the frontend API configuration points to the correct backend URL.

### Dependency Installation Issues

Ensure you are using a supported Python version:

```bash
python --version
```

Recommended:

```text
Python 3.10 or Python 3.11
```

Then recreate the virtual environment if necessary:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

# 🗺️ Future Improvements

Potential future enhancements include:

* ☁️ Cloud-based biometric storage
* 🔐 JWT-based authentication
* 📱 Mobile application
* 📡 Multi-camera classroom support
* 🧠 Improved anti-spoofing mechanisms
* 📈 Advanced academic performance prediction
* 🔔 Automated attendance notifications
* 📊 Faculty-level analytics and reporting
* 🏫 Multi-classroom and multi-campus deployment
* 🗄️ PostgreSQL/MySQL production database support

---

# 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Built With

**EduFlow** combines modern web development, artificial intelligence, and computer vision to create a smarter, faster, and more reliable attendance management experience.

> **Automate attendance. Prevent proxies. Understand performance.**
