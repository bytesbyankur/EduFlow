import cv2
import numpy as np
import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
from pydantic import BaseModel
import random

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    # Attendance Table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  time TEXT, 
                  date TEXT)''')

    # Students Table (with Passwords)
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  roll_number TEXT UNIQUE,
                  password TEXT)''')
    
    # Seed Data (if empty)
    c.execute("SELECT count(*) FROM students")
    if c.fetchone()[0] == 0:
        print("Seeding Database...")
        students = [
            ("Alice Johnson", "REG-2025-001", "password123"),
            ("Rashmika Mandana", "REG-2025-002", "password123"),
            ("Elon Musk", "REG-2025-003", "password123"),
            ("Shraddha Kapoor", "REG-2025-004", "password123")
        ]
        c.executemany("INSERT INTO students (name, roll_number, password) VALUES (?, ?, ?)", students)
        conn.commit()

    conn.close()

init_db()

# --- 2. LOGIN SYSTEM ---
class LoginRequest(BaseModel):
    user_id: str
    password: str
    role: str

@app.post("/login")
def login(request: LoginRequest):
    if request.role == 'teacher':
        if request.user_id == "admin" and request.password == "admin":
            return {"status": "success", "name": "Professor Miller", "role": "teacher"}
        else:
            raise HTTPException(status_code=401, detail="Invalid Faculty Credentials")
            
    elif request.role == 'student':
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT name FROM students WHERE roll_number=? AND password=?", (request.user_id, request.password))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {"status": "success", "name": row[0], "role": "student"}
        else:
            raise HTTPException(status_code=401, detail="Invalid Student ID or Password")

# --- 3. DASHBOARD DATA (For Teacher) ---
@app.get("/get-dashboard-data")
def get_dashboard_data():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    # Recent Logs
    c.execute("SELECT * FROM attendance_logs ORDER BY id DESC LIMIT 10")
    recent_logs = c.fetchall()
    
    # Stats
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(DISTINCT name) FROM attendance_logs WHERE date=?", (today,))
    present_today = c.fetchone()[0]
    
    conn.close()
    
    return {
        "stats": {
            "total_students": total_students,
            "present_today": present_today
        },
        "recent_logs": recent_logs
    }

# --- 4. MARK ATTENDANCE (Webcam Scan) ---
@app.post("/mark-attendance")
async def mark_attendance(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    cv2.imwrite("temp_scan.jpg", img)
    detected_names = []
    
    try:
        dfs = DeepFace.find(img_path="temp_scan.jpg", db_path="known_faces", model_name="VGG-Face", enforce_detection=False, silent=True)
        
        for df in dfs:
            if not df.empty:
                path = df.iloc[0]['identity']
                name = os.path.splitext(os.path.basename(path))[0]
                detected_names.append(name)
                
                conn = sqlite3.connect('attendance.db')
                c = conn.cursor()
                now = datetime.now()
                c.execute("SELECT * FROM attendance_logs WHERE name=? AND date=?", (name, now.strftime("%Y-%m-%d")))
                if not c.fetchone():
                    c.execute("INSERT INTO attendance_logs (name, time, date) VALUES (?, ?, ?)", 
                              (name, now.strftime("%H:%M:%S"), now.strftime("%Y-%m-%d")))
                    conn.commit()
                conn.close()

        if detected_names:
            return {"status": "success", "students": detected_names}
        else:
            return {"status": "failed", "message": "No match found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 5. REGISTER STUDENT (MISSING BEFORE!) ---
@app.post("/register-student")
async def register_student(name: str = Form(...), file: UploadFile = File(...)):
    if not os.path.exists("known_faces"): os.makedirs("known_faces")
    
    # 1. Save Photo
    file_location = f"known_faces/{name}.jpg"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    
    # 2. Add to Database (Default Password: password123)
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    try:
        # Generate a Fake ID based on count for demo
        c.execute("SELECT count(*) FROM students")
        count = c.fetchone()[0] + 1
        reg_id = f"REG-2025-{count:03d}"
        
        c.execute("INSERT INTO students (name, roll_number, password) VALUES (?, ?, ?)", (name, reg_id, "password123"))
        conn.commit()
        msg = f"Student {name} registered! ID: {reg_id}"
    except Exception as e:
        msg = "Photo saved, but DB update failed (Name might exist)."
    finally:
        conn.close()

    # 3. Clear AI Cache
    if os.path.exists("known_faces/representations_vgg_face.pkl"):
        os.remove("known_faces/representations_vgg_face.pkl")
        
    return {"status": "success", "message": msg}

# --- 6. STUDENT STATS (Now with GPA/Rank) ---
@app.get("/student/stats/{student_name}")
def get_student_stats(student_name: str):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM attendance_logs WHERE name=?", (student_name,))
    present_count = c.fetchone()[0]
    conn.close()
    
    # Use name to seed random generator so stats stay consistent for the same person
    random.seed(student_name)
    
    # Mock Data Generation
    gpa = round(random.uniform(2.5, 4.0), 2)
    credits_earned = random.randint(10, 60)
    class_rank = random.randint(1, 50)
    total_days = 60
    
    # Calculate Attendance
    attendance_rate = round((present_count / total_days) * 100, 1) if total_days > 0 else 0
    absent_days = max(0, total_days - present_count)

    return {
        "name": student_name,
        "attendance_rate": attendance_rate,
        "present_days": present_count,
        "absent_days": absent_days,
        "gpa": gpa,
        "credits": credits_earned,
        "rank": f"#{class_rank}",
        "courses": ["Neural Networks", "Ethics in AI", "Computer Vision"] # Static for now
    }

# --- 7. EXPORT CSV ---
@app.get("/export-csv")
def export_csv():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT * FROM attendance_logs")
    rows = c.fetchall()
    conn.close()
    
    csv = "ID,Name,Time,Date\n"
    for row in rows:
        csv += f"{row[0]},{row[1]},{row[2]},{row[3]}\n"
    return Response(content=csv, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendance.csv"})

# --- 8. RESET DB ---
@app.post("/reset-db")
def reset_db():
    if os.path.exists("attendance.db"):
        os.remove("attendance.db")
    init_db()
    return {"message": "Database Reset"}

# --- 9. ROSTER (For 'My Students' Tab) ---
@app.get("/get-class-roster")
def get_class_roster(class_name: str):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT name FROM students") # Just get all students for Hackathon demo
    students = [row[0] for row in c.fetchall()]
    conn.close()
    return {"class": class_name, "students": students, "count": len(students)}