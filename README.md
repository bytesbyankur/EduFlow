EduFlow | AI-Powered Smart Attendance System
============================================

**EduFlow** is a next-generation university platform that automates attendance using Computer Vision and Artificial Intelligence. By integrating **Google's TensorFlow** and facial recognition technology, it eliminates manual roll calls, prevents "proxy" attendance, and provides students with real-time analytics on their academic standing.

🚀 Key Features
===============

### 🧠 AI & Automation

-   **Touchless Attendance:** Mark attendance in milliseconds using a webcam and facial recognition.

-   **Class-Specific Intelligence:** The system understands context---scanning a student for "Neural Networks" won't mistakenly mark them present for "Ethics in AI."

-   **Anti-Spoofing/Proxy Prevention:** Biometric verification ensures only the actual student can mark attendance.

### 🎓 Student Portal

-   **Real-Time Analytics:** Interactive graphs showing attendance trends over the last 7 days.

-   **Full History Log:** A scrollable, date-wise record of every class attended.

-   **"At Risk" Alerts:** Automatic warnings if attendance drops below the 75% threshold.

### 👨‍🏫 Faculty Dashboard

-   **Instant Registration:** Onboard new students in seconds by capturing their face and assigning them to classes.

-   **Live Roster:** View real-time stats on who is present, absent, or enrolled.

-   **Data Export:** Download attendance logs as CSV files for official records.

🛠️ Tech Stack
==============

**Frontend (Client Layer)**

-   **HTML5 / CSS3:** Core structure and animations.

-   **Tailwind CSS:** Utility-first framework for a modern, responsive UI.

-   **Vanilla JavaScript (ES6+):** Handles webcam streaming, API calls (`fetch`), and state management.

**Backend (Server Layer)**

-   **Python 3.10+:** The core programming language.

-   **FastAPI:** High-performance web framework for handling REST API requests.

-   **SQLite:** Lightweight relational database for storing students, logs, and rosters.

**Artificial Intelligence (The "Google" Tech)**

-   **TensorFlow / Keras:** The deep learning engine powering the inference.

-   **DeepFace:** Computer vision library for face detection and embedding generation.

-   **OpenCV:** Image processing and real-time video capture.

📥 Installation & Setup
=======================

### Prerequisites

-   **Python 3.8 or higher** installed on your system.

-   A working **Webcam**.

-   An internet connection (for downloading Python libraries and Tailwind/Icon CDNs).

### Step 1: Install Dependencies

Open your terminal or command prompt in the `backend` folder and run:

Bash

```
pip install fastapi uvicorn numpy pandas opencv-python deepface tensorflow

```

*(Note: The first run might take a moment to download the DeepFace weights).*

### Step 2: Start the Backend Server

In the same terminal (inside the `backend` folder), run:

Bash

```
python -m uvicorn main:app --reload

```

You should see a message saying: `Uvicorn running on http://127.0.0.1:8000`.

### Step 3: Launch the Application

1.  Go to the `Frontend/frontpage` folder and double-click `index.html`.

2.  Click **"Enter Experience"**.

3.  **Log in:**

    -   **Teacher:** User: `admin`, Pass: `admin`

    -   **Student:** Use the Roll Number generated after registration (e.g., `REG-2025-001`) and default password `password123`.

🏃‍♂️ How to Run the Demo (Hackathon Flow)
==========================================

1.  **Start the Server:** Ensure the black terminal window is running the FastAPI server.

2.  **Open Teacher Portal:** Login as Admin.

3.  **Register a User:**

    -   Click "Add Student".

    -   Enter your name (e.g., "Swaraj").

    -   **Select a Class** from the dropdown (e.g., "Advanced Neural Networks").

    -   Click "Capture & Save".

4.  **Mark Attendance:**

    -   Select the **SAME class** ("Advanced Neural Networks") from the dashboard dropdown.

    -   Click "Mark Attendance".

    -   Look at the camera -> See the **Green Verified Message**.

5.  **Check Analytics:**

    -   Logout and Login as the Student (`REG-2025-XXX`).

    -   Show the **Attendance Graph** (it should show activity for today).

    -   Scroll down to the **History Log** to see the exact timestamp.

📁 Project Structure
====================

Plaintext

```
EduFlow/
├── backend/
│   ├── main.py                # The Brain (FastAPI + AI Logic)
│   ├── attendance.db          # Database (Auto-created)
│   ├── known_faces/           # Folder storing registered student faces
│   └── seed_history.py        # Script to generate fake past data for demos
│
└── Frontend/
    ├── frontpage/             # The Landing Page
    │   └── index.html
    ├── Teacher Portal/        # Faculty Dashboard
    │   ├── index.html
    │   └── script.js
    └── Student Portal/        # Student Dashboard
        ├── index.html
        └── script.js

```

* * * * *

*Developed with ❤️ for the Hackathon.*
