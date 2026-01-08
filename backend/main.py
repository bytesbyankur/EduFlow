import cv2
import numpy as np
import os
import sqlite3
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from deepface import DeepFace
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. CONFIGURATION & DATA ---
CLASS_ROSTERS = {
    "Advanced Neural Networks": ["Taylor Swift", "Rashmika Mandana", "Elon Musk"],
    "Ethics in AI": ["Barack Obama", "Taylor Swift", "Sraddha Kapoor"],
    "Computer Vision 101": ["Rashmika Mandana", "Elon Musk", "Taylor Swift"]
}

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    # Attendance Table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  class_name TEXT,
                  time TEXT, 
                  date TEXT)''')

    # Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  roll_number TEXT UNIQUE,
                  password TEXT)''')
    
    # Seed Data (If empty)
    c.execute("SELECT count(*) FROM students")
    if c.fetchone()[0] == 0:
        print("Seeding Database...")
        students = [
            ("Barack Obama", "REG-2025-001", "password123"),
            ("Rashmika Mandana", "REG-2025-002", "password123"),
            ("Elon Musk", "REG-2025-003", "password123"),
            ("Taylor Swift", "REG-2025-004", "password123"),
            ("Sraddha Kapoor", "REG-2025-005", "password123"),
        ]
        c.executemany("INSERT INTO students (name, roll_number, password) VALUES (?, ?, ?)", students)
        conn.commit()

    conn.close()

init_db()

# --- 3. LOGIN SYSTEM ---
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

# --- 4. MARK ATTENDANCE (Class Specific) ---
@app.post("/mark-attendance")
async def mark_attendance(class_name: str = Form(...), file: UploadFile = File(...)):
    # Read Image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite("temp_scan.jpg", img)
    
    detected_names = []
    
    try:
        # 1. Get students only for this specific class
        valid_students = CLASS_ROSTERS.get(class_name, [])
        if not valid_students:
            return {"status": "failed", "message": "No students enrolled in this class"}

        # 2. Scan Face
        dfs = DeepFace.find(img_path="temp_scan.jpg", db_path="known_faces", model_name="VGG-Face", enforce_detection=False, silent=True)
        
        for df in dfs:
            if not df.empty:
                path = df.iloc[0]['identity']
                name = os.path.splitext(os.path.basename(path))[0]
                
                # 3. Check: Is this person in this class?
                if name in valid_students:
                    detected_names.append(name)
                    
                    conn = sqlite3.connect('attendance.db')
                    c = conn.cursor()
                    now = datetime.now()
                    
                    # Check if already marked for THIS CLASS today
                    c.execute("SELECT * FROM attendance_logs WHERE name=? AND class_name=? AND date=?", (name, class_name, now.strftime("%Y-%m-%d")))
                    if not c.fetchone():
                        c.execute("INSERT INTO attendance_logs (name, class_name, time, date) VALUES (?, ?, ?, ?)", 
                                  (name, class_name, now.strftime("%H:%M:%S"), now.strftime("%Y-%m-%d")))
                        conn.commit()
                    conn.close()

        if detected_names:
            return {"status": "success", "students": detected_names}
        else:
            return {"status": "failed", "message": "Student not found in this class roster"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 5. REGISTER STUDENT (UPDATED: Class Specific) ---
@app.post("/register-student")
async def register_student(name: str = Form(...), class_name: str = Form(...), file: UploadFile = File(...)):
    if not os.path.exists("known_faces"): os.makedirs("known_faces")
    
    # 1. Save Photo
    file_location = f"known_faces/{name}.jpg"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    
    # 2. Add to DB
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    msg = "" 

    try:
        c.execute("SELECT count(*) FROM students")
        count = c.fetchone()[0] + 1
        reg_id = f"REG-2025-{count:03d}"
        
        c.execute("INSERT INTO students (name, roll_number, password) VALUES (?, ?, ?)", (name, reg_id, "password123"))
        conn.commit()
        
        msg = f"Student {name} registered! ID: {reg_id}"
        
        # 3. Add ONLY to the Selected Class
        if class_name in CLASS_ROSTERS:
            # Check to avoid duplicates
            if name not in CLASS_ROSTERS[class_name]:
                CLASS_ROSTERS[class_name].append(name)
                msg += f" (Added to {class_name})"
        else:
            msg += " (Warning: Class not found in roster)"
            
    except Exception as e:
        msg = f"Error: {str(e)}" 
    finally:
        conn.close()

    # 4. Clear Cache
    if os.path.exists("known_faces/representations_vgg_face.pkl"):
        os.remove("known_faces/representations_vgg_face.pkl")
        
    return {"status": "success", "message": msg}

# --- 6. STUDENT STATS ---
@app.get("/student/stats/{student_name}")
def get_student_stats(student_name: str):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    # 1. Total Present Count (Global)
    c.execute("SELECT COUNT(*) FROM attendance_logs WHERE name=?", (student_name,))
    total_present = c.fetchone()[0]
    
    # 2. Daily Activity for Graph
    daily_activity = []
    today = datetime.now()
    
    for i in range(6, -1, -1): 
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM attendance_logs WHERE name=? AND date=?", (student_name, target_date))
        count = c.fetchone()[0]
        daily_activity.append(count)
        
    # 3. Enrolled Courses Logic
    enrolled_courses = []
    for course_name, students in CLASS_ROSTERS.items():
        if student_name in students:
            c.execute("SELECT COUNT(*) FROM attendance_logs WHERE name=? AND class_name=?", (student_name, course_name))
            class_present = c.fetchone()[0]
            
            sessions_so_far = 10 
            class_rate = round((class_present / sessions_so_far) * 100, 1)
            
            status = "On Track"
            if class_rate < 75: status = "At Risk"
            if class_rate < 50: status = "Critical"
            
            enrolled_courses.append({
                "name": course_name, 
                "present": class_present, 
                "rate": class_rate, 
                "status": status
            })

    conn.close()
    
    # 4. Mock Academic Stats
    random.seed(student_name)
    gpa = round(random.uniform(2.5, 4.0), 2)
    credits_earned = random.randint(10, 25)
    class_rank = random.randint(1, 50)
    
    overall_rate = round(sum(c['rate'] for c in enrolled_courses) / len(enrolled_courses), 1) if enrolled_courses else 0.0

    return {
        "name": student_name,
        "attendance_rate": overall_rate,
        "present_days": total_present,
        "total_days": 30, 
        "gpa": gpa,
        "credits": credits_earned,
        "rank": f"#{class_rank}",
        "courses": enrolled_courses,
        "graph_data": daily_activity
    }

# --- 7. DASHBOARD DATA ---
@app.get("/get-dashboard-data")
def get_dashboard_data():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    # Join to get real IDs
    c.execute("""
        SELECT s.roll_number, a.name, a.time, a.class_name 
        FROM attendance_logs a 
        LEFT JOIN students s ON a.name = s.name 
        ORDER BY a.id DESC LIMIT 10
    """)
    recent_logs = c.fetchall()
    
    # Stats logic
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(DISTINCT name) FROM attendance_logs WHERE date=?", (today,))
    present_today = c.fetchone()[0]
    conn.close()
    
    return {
        "stats": {"total_students": total_students, "present_today": present_today},
        "recent_logs": recent_logs
    }

# --- 8. GET CLASS ROSTER ---
@app.get("/get-class-roster")
def get_class_roster(class_name: str):
    students = CLASS_ROSTERS.get(class_name, [])
    return {"class": class_name, "students": students, "count": len(students)}

# --- 9. RESET DB ---
@app.post("/reset-db")
def reset_db():
    if os.path.exists("attendance.db"):
        os.remove("attendance.db")
    init_db()
    return {"message": "Database Reset"}

# --- 10. EXPORT CSV ---
@app.get("/export-csv")
def export_csv():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute("SELECT * FROM attendance_logs")
    rows = c.fetchall()
    conn.close()
    csv = "ID,Name,Class,Time,Date\n"
    for row in rows:
        csv += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n"
    return Response(content=csv, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendance.csv"})

# --- 11. GET STUDENT FULL HISTORY ---
@app.get("/student/history/{student_name}")
def get_student_history(student_name: str):
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT date, time, class_name 
        FROM attendance_logs 
        WHERE name=? 
        ORDER BY date DESC, time DESC
    """, (student_name,))
    
    logs = c.fetchall()
    conn.close()
    
    history = []
    for log in logs:
        history.append({
            "date": log[0],
            "time": log[1],
            "class": log[2]
        })
        
    return {"history": history}