import os
import certifi
import json
import traceback
from google import genai
from functools import wraps
from google.genai import types
from flask import (Flask, jsonify, render_template, request, redirect, url_for, session, flash)
from pymongo import MongoClient
from werkzeug.security import (generate_password_hash, check_password_hash)
from dotenv import load_dotenv
from bson.objectid import ObjectId

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_FILE)

app = Flask(
    __name__,
    template_folder="pages",
    static_folder="assets"
)

# ==============================
# PROFILE PICTURE UPLOAD CONFIG
# ==============================

PROFILE_UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads", "profile_pictures")
app.config["PROFILE_UPLOAD_FOLDER"] = PROFILE_UPLOAD_FOLDER
ALLOWED_PROFILE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(PROFILE_UPLOAD_FOLDER, exist_ok=True)

def allowed_profile_picture(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_PROFILE_EXTENSIONS
    )

app.secret_key = os.getenv(
    "SECRET_KEY",
    "pathnivo-development-secret-key"
)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing. Please add it to your .env file.")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=15000,
    connectTimeoutMS=15000,
    socketTimeoutMS=15000,
)

db = client["pathnivo_db"]
users_collection = db["users"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Please add it to your .env file.")

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except Exception as e:
    print("MongoDB connection failed:", e)
    raise

users_collection.create_index("email", unique=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one(
        {"_id": user_id}
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))

    skills_data = user.get("skills", [])

    if not isinstance(skills_data, list):
        skills_data = []

    total_skills = len(skills_data)
    completed_skills = sum(1
        for skill in skills_data
        if (
            isinstance(skill, dict)
            and skill.get("progress", 0) >= 100
        )
    )

    skill_progress = round(
        sum(max(0,min(100,int(skill.get("progress", 0))))
            for skill in skills_data
            if isinstance(skill, dict)
        ) / total_skills
    ) if total_skills else 0

    completed_steps = user.get("completed_roadmap_steps", [])
    started_steps = user.get("started_roadmap_steps", [])

    if not isinstance(completed_steps,list):
        completed_steps = []

    if not isinstance(started_steps, list):
        started_steps = []

    projects_data = user.get("projects", [])
    if not isinstance(projects_data, list):
        projects_data = []

    total_projects = len(projects_data)
    completed_projects = sum( 1
        for project in projects_data
        if (
            isinstance(project, dict)
            and project.get("status") == "Completed"
        )
    )
    project_progress_values = []
    for project in projects_data:
        if not isinstance(project, dict):
            continue

        try:
            progress = int(project.get("progress",0))
        except (TypeError, ValueError):
            progress = 0

        progress = max(0, min(100,progress))
        project_progress_values.append(progress)
    project_progress = round(
        sum(project_progress_values)
        / len(project_progress_values)
    ) if project_progress_values else 0

    courses_data = []
    for skill in skills_data:
        if not isinstance(skill, dict):
            continue
        try:
            progress = int(skill.get("progress",0))
        except (TypeError, ValueError):
            progress = 0

        progress = max(0, min(100, progress))
        courses_data.append(
            {
                "title": skill.get("title", "Untitled Course"),
                "career": skill.get("career", "Career Skill"),
                "progress": progress,
                "status": skill.get("status", "In Progress"),
                "step_id": skill.get("step_id", "")
            }
        )

    total_courses = len(courses_data)
    completed_courses = sum(1
        for course in courses_data
        if (
            isinstance(course, dict)
            and (
                course.get("status") == "Completed"
                or course.get("progress", 0) >= 100
            )
        )
    )

    course_progress = round(
        sum(course.get( "progress", 0)
            for course in courses_data
            if isinstance(course, dict)
        ) / total_courses
    ) if total_courses else 0

    career_progress = round(
        (
            skill_progress
            + project_progress
        ) / 2
    )

    if career_progress >= 100:
        readiness_message = ("Career roadmap completed 🎉")
    elif career_progress >= 75:
        readiness_message = ("Great progress")
    elif career_progress >= 40:
        readiness_message = ("Good progress")
    elif career_progress > 0:
        readiness_message = ("Keep going")
    else:
        readiness_message = ("Start your career journey")

    incomplete_skills = [
        skill
        for skill in skills_data
        if (
            isinstance(skill, dict)
            and skill.get("progress", 0) < 100
        )
    ]

    if incomplete_skills:
        incomplete_skills.sort(key=lambda skill: skill.get("progress", 0))
        next_skill = incomplete_skills[0]
    else:
        next_skill = {
            "title": "No next skill yet",
            "progress": 0,
            "status": "Not Started"
        }

    recommended_course = {
        "title": "Start a Course",
        "description": ("Choose a course from your current learning roadmap."),
        "url": url_for("courses")
    }

    recommended_skill = {
        "title": "Build Your Skills",
        "description": ("Continue learning the next skill in your roadmap."),
        "url": url_for("skills")
    }

    recommended_project = {
        "title": "Build Your First Project",
        "description": ("Start a practical project based on your current learning."),
        "url": url_for("projects")
    }

    if incomplete_skills:
        current_skill = incomplete_skills[0]
        skill_title = current_skill.get("title", "Current Skill")
        skill_progress_value = current_skill.get("progress", 0)
        recommended_course = {
            "title": f"Learn {skill_title}",
            "description": (
                f"Continue your learning journey by improving "
                f"your {skill_title} knowledge."
            ),
            "url": url_for("courses")
        }

        recommended_skill = {
            "title": skill_title,
            "description": (
                f"Your current progress is "
                f"{skill_progress_value}%. "
                f"Keep improving this skill."
            ),
            "url": url_for("skills")
        }
        matching_project = None
        current_step_id = current_skill.get("step_id", "")
        for project in projects_data:
            if not isinstance(project, dict):
                continue
            if (
                current_step_id
                and project.get("step_id")
                == current_step_id
            ):
                matching_project = project
                break
        if matching_project:
            recommended_project = {
                "title": matching_project.get("title",
                    f"{skill_title} Practice Project"),
                "description": matching_project.get("description",
                    f"Build a practical project using {skill_title}."),
                "url": url_for("projects")
            }
        else:
            recommended_project = {
                "title": (f"{skill_title} Practice Project"),
                "description": (
                    f"Apply your {skill_title} knowledge "
                    f"by building a practical project."
                ),
                "url": url_for("projects")
            }
    else:
        incomplete_projects = [
            project
            for project in projects_data
            if (
                isinstance(project, dict)
                and project.get("progress", 0) < 100
            )
        ]
        if incomplete_projects:
            current_project = incomplete_projects[0]
            project_title = current_project.get("title", "Practice Project")
            project_progress_value = current_project.get("progress", 0)
            recommended_course = {
                "title": "Review Your Learning",
                "description": (
                    "Review your completed skills before "
                    "continuing with practical work."
                ),
                "url": url_for("courses")
            }
            recommended_skill = {
                "title": "Practice Your Skills",
                "description": (
                    "Use your completed skills in practical "
                    "projects to strengthen your knowledge."
                ),
                "url": url_for("skills")
            }
            recommended_project = {
                "title": project_title,
                "description": (
                    f"Your project is "
                    f"{project_progress_value}% complete. "
                    f"Continue building it."
                ),
                "url": url_for("projects")
            }
        else:
            recommended_course = {
                "title": "All Skills Completed 🎉",
                "description": (
                    "You have completed all your current "
                    "learning skills."
                ),
                "url": url_for("courses")
            }
            recommended_skill = {
                "title": "Keep Your Skills Strong",
                "description": (
                    "Review your completed skills and "
                    "continue practicing."
                ),
                "url": url_for("skills")
            }
            recommended_project = {
                "title": "Build More Projects",
                "description": (
                    "Create more practical projects to "
                    "strengthen your portfolio."
                ),
                "url": url_for("projects")
            }
    roadmap_display = []
    ai_roadmaps = user.get("ai_roadmaps", [])
    if not isinstance(ai_roadmaps,list):
        ai_roadmaps = []
    selected_career = str(
        user.get("selected_career", "")).strip()
    selected_roadmap = None
    if selected_career:
        for roadmap in ai_roadmaps:
            if not isinstance(roadmap, dict):
                continue
            roadmap_career = str(roadmap.get("career", "")).strip()
            if (
                roadmap_career.lower()
                == selected_career.lower()
            ):
                selected_roadmap = roadmap
                break
    if (
        selected_roadmap is None
        and ai_roadmaps
    ):
        selected_roadmap = ai_roadmaps[-1]
    roadmap_steps = []
    if selected_roadmap:
        roadmap_steps = selected_roadmap.get("roadmap", [])
    if not isinstance(roadmap_steps, list):
        roadmap_steps = []
    for step in roadmap_steps:
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("id", "")).strip()
        if not step_id:
            continue
        if step_id in completed_steps:
            status = "Completed"
        elif step_id in started_steps:
            status = "Current"
        else:
            status = "Upcoming"

        roadmap_display.append(
            {
                "id": step_id,
                "title": step.get("title","Untitled Step"),
                "status": status
            }
        )
    roadmap_display = roadmap_display[:4]
    dashboard_data = {
        "total_skills": total_skills,
        "completed_skills": completed_skills,
        "skill_progress": skill_progress,
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "course_progress": course_progress,
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "project_progress": project_progress,
        "career_progress": career_progress,
        "readiness_message": readiness_message,
        "completed_steps": len(completed_steps),
        "started_steps": len(started_steps),
        "next_skill": next_skill,
        "roadmap_display": roadmap_display,
        "recommended_course": recommended_course,
        "recommended_skill": recommended_skill,
        "recommended_project": recommended_project
    }

    return render_template("dashboard.html", user=user, dashboard=dashboard_data)

@app.route("/careers")
def careers():
    return render_template("careers.html")

@app.route("/career-details")
def career_details():
    career = request.args.get("career","python")
    careers_data = {
        "python": {
            "title": "Python Developer",
            "icon": "🐍",
            "category": "Development",
            "description": ("Build applications using Python."),
            "duration": "4–6 Months",
            "steps": 6,
            "progress": 25,
            "level": "Beginner",
            "difficulty": "Moderate",
            "focus": "Backend Development",
            "skills": [
                "Python",
                "Flask",
                "MongoDB"
            ],
            "roadmap": [
                "Learn programming basics",
                "Learn Python",
                "Learn Flask",
                "Learn MongoDB"
            ],
            "projects": [
                "Portfolio Website",
                "Blog Application"
            ]
        },

        "fullstack": {
            "title": "Full Stack Developer",
            "icon": "💻",
            "category": "Technology",
            "description": (
                "Build complete web applications using "
                "frontend, backend, databases, and APIs."
            ),
            "duration": "6–9 Months",
            "steps": 10,
            "progress": 25,
            "level": "Beginner",
            "difficulty": "Moderate",
            "focus": "Frontend + Backend",
            "skills": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Python",
                "Flask",
                "MongoDB",
                "REST APIs"
            ],
            "roadmap": [
                "Learn HTML and CSS",
                "Learn JavaScript",
                "Learn frontend development",
                "Learn React",
                "Learn Python",
                "Learn Flask",
                "Learn MongoDB",
                "Build full stack projects"
            ],
            "projects": [
                "Portfolio Website",
                "E-commerce Website",
                "Student Management System"
            ]
        },

        "data-analyst": {
            "title": "Data Analyst",
            "icon": "📊",
            "category": "Data",
            "description": (
                "Analyze data, create reports, and discover "
                "useful business insights."
            ),
            "duration": "4–6 Months",
            "steps": 7,
            "progress": 25,
            "level": "Beginner",
            "difficulty": "Moderate",
            "focus": "Data Analysis",
            "skills": [
                "Excel",
                "Python",
                "SQL",
                "Pandas",
                "NumPy",
                "Data Visualization",
                "Power BI"
            ],
            "roadmap": [
                "Learn Excel",
                "Learn basic statistics",
                "Learn SQL",
                "Learn Python",
                "Learn Pandas and NumPy",
                "Create charts and reports",
                "Build data analysis projects"
            ],
            "projects": [
                "Sales Data Analysis",
                "Student Performance Dashboard",
                "Business Report Dashboard"
            ]
        },

        "ui-ux": {
            "title": "UI/UX Designer",
            "category": "Design",
            "icon": "🎨",
            "description": (
                "Create attractive, user-friendly and "
                "professional website and app designs."
            ),
            "skills": [
                "Figma",
                "UI Design",
                "UX Research",
                "Wireframing",
                "Prototyping",
                "Typography",
                "Color Theory"
            ],
            "roadmap": [
                "Learn design principles",
                "Learn Figma",
                "Practice wireframes",
                "Create website and app prototypes",
                "Build a design portfolio",
                "Apply for UI/UX internships"
            ],
            "projects": [
                "Portfolio Website Design",
                "Food Delivery App UI",
                "Student Dashboard UI"
            ]
        },

        "cybersecurity": {
            "title": "Cybersecurity Analyst",
            "icon": "🛡️",
            "category": "Cybersecurity",
            "description": (
                "Protect systems, networks, and data from "
                "cyber threats and security attacks."
            ),
            "duration": "6–9 Months",
            "steps": 9,
            "progress": 25,
            "level": "Beginner",
            "difficulty": "Moderate",
            "focus": "Security",
            "skills": [
                "Networking",
                "Linux",
                "Python Basics",
                "Cybersecurity Fundamentals",
                "Ethical Hacking",
                "Security Tools",
                "Threat Analysis"
            ],
            "roadmap": [
                "Learn computer networking",
                "Learn Linux basics",
                "Learn cybersecurity fundamentals",
                "Learn ethical hacking basics",
                "Practice security tools",
                "Learn vulnerability analysis",
                "Study security monitoring",
                "Build cybersecurity projects"
            ],
            "projects": [
                "Network Scanner",
                "Password Strength Checker",
                "Basic Security Audit Report"
            ]
        },

        "mobile-app": {
            "title": "Mobile App Developer",
            "category": "Development",
            "icon": "📱",
            "description": (
                "Build Android and iOS mobile applications "
                "using modern development tools."
            ),
            "skills": [
                "Programming Basics",
                "Flutter",
                "Dart",
                "Firebase",
                "API Integration",
                "UI Design",
                "App Debugging"
            ],
            "roadmap": [
                "Learn programming basics",
                "Learn Dart",
                "Learn Flutter",
                "Build simple mobile apps",
                "Learn Firebase",
                "Connect APIs",
                "Publish a mobile app"
            ],
            "projects": [
                "To-Do Mobile App",
                "Notes App",
                "Student Attendance App"
            ]
        }
    }
    selected_career = careers_data.get(career, careers_data["python"])
    return render_template("career-details.html",career=selected_career)

@app.route("/login.html", methods=["GET", "POST"])
def old_login_url():
    if request.method == "POST":
        return redirect(url_for("login"),code=307)
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        print("LOGIN EMAIL:", email)
        print("PASSWORD RECEIVED:", bool(password))
        user = db.users.find_one(
            {"email": email}
        )
        print("USER FOUND:", user is not None)
        if not user:
            flash("Email is not registered.", "error")
            return redirect(url_for("login"))
        stored_password = user.get("password")
        print("PASSWORD FIELD FOUND:",stored_password is not None)
        if not stored_password:
            flash("This account has no password saved.","error")
            return redirect(url_for("login"))
        try:
            password_correct = check_password_hash(stored_password,password)
        except Exception as error:
            print("PASSWORD HASH ERROR:",error)
            flash("Password format is invalid. Please register again.","error")
            return redirect(url_for("login"))
        print("PASSWORD CORRECT:",password_correct)
        if not password_correct:
            flash("Incorrect password.","error")
            return redirect(url_for("login"))
        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        print("SESSION CREATED:",dict(session))
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        confirm_password = request.form.get("confirm_password","")
        terms = request.form.get("terms")
        if (
            not name
            or not email
            or not password
            or not confirm_password
        ):
            return render_template("register.html", error="Please fill all fields.")
        if (
            "@" not in email
            or "." not in email
        ):
            return render_template("register.html",error="Please enter a valid email address.")
        if len(password) < 8:
            return render_template("register.html",error="Password must be at least 8 characters.")
        if password != confirm_password:
            return render_template("register.html",error="Passwords do not match.")
        if not terms:
            return render_template("register.html",error="Please accept the Terms of Service.")
        existing_user = users_collection.find_one(
            {"email": email}
        )
        if existing_user:
            return render_template("register.html",error="This email is already registered.")
        hashed_password = generate_password_hash(password)
        user_data = {
            "name": name,
            "email": email,
            "password": hashed_password
        }
        users_collection.insert_one(user_data)
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

@app.route("/roadmap")
@login_required
def roadmap():
    user = db.users.find_one(
        {"_id": ObjectId(session["user_id"])}
    )
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("roadmap.html",user=user)
def create_fallback_roadmap(career):
    career_lower = career.lower().strip()
    if any(
        word in career_lower
        for word in [
            "video editor",
            "video editing",
            "video editing basics"
        ]
    ):
        return [
            {
                "category": "Video Editing",
                "title": "Video Editing Basics",
                "description": (
                    "Learn the fundamentals of video editing, "
                    "timeline editing, cuts, transitions and storytelling."
                ),
                "what_to_learn": [
                    "Video editing interface",
                    "Timeline and sequence",
                    "Cutting and trimming",
                    "Transitions",
                    "Basic storytelling"
                ],
                "resources": [
                    {
                        "title": "YouTube Video Editing Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=video+editing+basics+tutorial"
                        )
                    },
                    {
                        "title": "DaVinci Resolve Training",
                        "url": (
                            "https://www.blackmagicdesign.com/"
                            "products/davinciresolve/training"
                        )
                    },
                    {
                        "title": "Adobe Premiere Pro Tutorials",
                        "url": (
                            "https://helpx.adobe.com/"
                            "premiere-pro/tutorials.html"
                        )
                    }
                ]
            },

            {
                "category": "Video Editing",
                "title": "Cuts and Transitions",
                "description": (
                    "Learn professional cutting techniques, "
                    "transitions and smooth scene changes."
                ),
                "what_to_learn": [
                    "Basic cuts",
                    "Jump cuts",
                    "Match cuts",
                    "Transitions",
                    "Pacing"
                ],
                "resources": [
                    {
                        "title": "YouTube Cuts and Transitions Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=video+editing+cuts+transitions+tutorial"
                        )
                    },
                    {
                        "title": "Adobe Premiere Pro Tutorials",
                        "url": (
                            "https://helpx.adobe.com/"
                            "premiere-pro/tutorials.html"
                        )
                    }
                ]
            },

            {
                "category": "Video Editing",
                "title": "Audio Editing",
                "description": (
                    "Learn how to use music, sound effects, "
                    "dialogue and audio levels effectively."
                ),
                "what_to_learn": [
                    "Dialogue editing",
                    "Background music",
                    "Sound effects",
                    "Audio levels",
                    "Audio mixing"
                ],
                "resources": [
                    {
                        "title": "YouTube Audio Editing Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=video+editing+audio+mixing+tutorial"
                        )
                    },

                    {
                        "title": "Adobe Premiere Pro Audio Tutorials",
                        "url": (
                            "https://helpx.adobe.com/"
                            "premiere-pro/tutorials.html"
                        )
                    }
                ]
            },

            {
                "category": "Video Editing",
                "title": "Color Correction and Color Grading",
                "description": (
                    "Learn basic color correction and cinematic "
                    "color grading techniques."
                ),
                "what_to_learn": [
                    "Exposure",
                    "White balance",
                    "Contrast",
                    "Color correction",
                    "Color grading"
                ],
                "resources": [
                    {
                        "title": "DaVinci Resolve Official Training",
                        "url": (
                            "https://www.blackmagicdesign.com/"
                            "products/davinciresolve/training"
                        )
                    },

                    {
                        "title": "YouTube Color Grading Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=color+grading+video+editing+tutorial"
                        )
                    }
                ]
            },

            {
                "category": "Video Editing",
                "title": "Motion Graphics Basics",
                "description": (
                    "Learn basic motion graphics, text animation "
                    "and visual effects."
                ),
                "what_to_learn": [
                    "Text animation",
                    "Keyframes",
                    "Basic motion",
                    "Titles",
                    "Simple visual effects"
                ],
                "resources": [
                    {
                        "title": "YouTube Motion Graphics Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=motion+graphics+basics+tutorial"
                        )
                    },

                    {
                        "title": "Adobe After Effects Tutorials",
                        "url": (
                            "https://helpx.adobe.com/"
                            "after-effects/tutorials.html"
                        )
                    }
                ]
            }
        ]

    if "python" in career_lower:
        return [
            {
                "category": "Programming",
                "title": "Python Basics",
                "description": (
                    "Learn Python syntax, variables, data types "
                    "and basic programming concepts."
                ),
                "what_to_learn": [
                    "Variables",
                    "Data types",
                    "Operators",
                    "Conditions",
                    "Loops"
                ],
                "resources": [
                    {
                        "title": "W3Schools Python Tutorial",
                        "url": (
                            "https://www.w3schools.com/python/"
                        )
                    },

                    {
                        "title": "Python Official Tutorial",
                        "url": (
                            "https://docs.python.org/3/tutorial/"
                        )
                    },

                    {
                        "title": "freeCodeCamp Python",
                        "url": (
                            "https://www.freecodecamp.org/"
                            "learn/scientific-computing-with-python/"
                        )
                    }
                ]
            },

            {
                "category": "Programming",
                "title": "Python Functions and Modules",
                "description": (
                    "Learn functions, modules and reusable Python code."
                ),
                "what_to_learn": [
                    "Functions",
                    "Parameters",
                    "Return values",
                    "Modules",
                    "Packages"
                ],
                "resources": [
                    {
                        "title": "W3Schools Python Functions",
                        "url": (
                            "https://www.w3schools.com/"
                            "python/python_functions.asp"
                        )
                    },

                    {
                        "title": "Python Documentation",
                        "url": (
                            "https://docs.python.org/3/tutorial/"
                        )
                    }
                ]
            },

            {
                "category": "Backend Development",
                "title": "Flask",
                "description": (
                    "Learn how to build web applications and "
                    "APIs using Flask."
                ),
                "what_to_learn": [
                    "Flask application",
                    "Routes",
                    "Templates",
                    "Forms",
                    "APIs"
                ],
                "resources": [
                    {
                        "title": "Flask Documentation",
                        "url": (
                            "https://flask.palletsprojects.com/"
                        )
                    },

                    {
                        "title": "YouTube Flask Tutorials",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=flask+python+tutorial"
                        )
                    }
                ]
            },

            {
                "category": "Database",
                "title": "MongoDB",
                "description": (
                    "Learn database concepts and how to work "
                    "with MongoDB."
                ),
                "what_to_learn": [
                    "Collections",
                    "Documents",
                    "CRUD",
                    "Queries",
                    "MongoDB with Python"
                ],
                "resources": [
                    {
                        "title": "MongoDB University",
                        "url": (
                            "https://learn.mongodb.com/"
                        )
                    },

                    {
                        "title": "MongoDB Python Documentation",
                        "url": (
                            "https://www.mongodb.com/"
                            "docs/languages/python/"
                        )
                    }
                ]
            }
        ]
    if any(
        word in career_lower
        for word in [
            "web developer",
            "frontend",
            "front end",
            "full stack",
            "fullstack"
        ]
    ):
        return [
            {
                "category": "Frontend",
                "title": "HTML Basics",
                "description": (
                    "Learn how websites are structured using HTML."
                ),
                "what_to_learn": [
                    "HTML structure",
                    "Headings",
                    "Paragraphs",
                    "Links",
                    "Forms"
                ],
                "resources": [
                    {
                        "title": "W3Schools HTML",
                        "url": (
                            "https://www.w3schools.com/html/"
                        )
                    },

                    {
                        "title": "MDN HTML",
                        "url": (
                            "https://developer.mozilla.org/"
                            "en-US/docs/Web/HTML"
                        )
                    }
                ]
            },

            {
                "category": "Frontend",
                "title": "CSS Basics",
                "description": (
                    "Learn how to style and design websites."
                ),
                "what_to_learn": [
                    "Selectors",
                    "Colors",
                    "Box model",
                    "Flexbox",
                    "Grid"
                ],
                "resources": [
                    {
                        "title": "W3Schools CSS",
                        "url": (
                            "https://www.w3schools.com/css/"
                        )
                    },

                    {
                        "title": "MDN CSS",
                        "url": (
                            "https://developer.mozilla.org/"
                            "en-US/docs/Web/CSS"
                        )
                    }
                ]
            },

            {
                "category": "Frontend",
                "title": "JavaScript",
                "description": (
                    "Learn JavaScript to add interaction and "
                    "dynamic behavior to websites."
                ),
                "what_to_learn": [
                    "Variables",
                    "Functions",
                    "Arrays",
                    "Objects",
                    "DOM"
                ],
                "resources": [
                    {
                        "title": "W3Schools JavaScript",
                        "url": (
                            "https://www.w3schools.com/js/"
                        )
                    },

                    {
                        "title": "MDN JavaScript",
                        "url": (
                            "https://developer.mozilla.org/"
                            "en-US/docs/Web/JavaScript"
                        )
                    },

                    {
                        "title": "freeCodeCamp JavaScript",
                        "url": (
                            "https://www.freecodecamp.org/"
                            "learn/javascript-algorithms-and-data-structures-v8/"
                        )
                    }
                ]
            }
        ]

    if any(
        word in career_lower
        for word in [
            "cybersecurity",
            "cyber security",
            "security analyst"
        ]
    ):
        return [
            {
                "category": "Cybersecurity",
                "title": "Networking Fundamentals",
                "description": (
                    "Learn networking concepts required for cybersecurity."
                ),
                "what_to_learn": [
                    "IP addresses",
                    "TCP/IP",
                    "DNS",
                    "HTTP/HTTPS",
                    "Ports"
                ],
                "resources": [
                    {
                        "title": "Cisco Networking Basics",
                        "url": (
                            "https://www.cisco.com/c/en/us/"
                            "training-events/training-certifications/"
                            "training.html"
                        )
                    },

                    {
                        "title": "YouTube Networking Basics",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=networking+basics+for+cybersecurity"
                        )
                    }
                ]
            },

            {
                "category": "Cybersecurity",
                "title": "Linux Basics",
                "description": (
                    "Learn Linux commands and basic system administration."
                ),
                "what_to_learn": [
                    "Linux terminal",
                    "Files and directories",
                    "Permissions",
                    "Processes",
                    "Basic commands"
                ],
                "resources": [
                    {
                        "title": "Linux Journey",
                        "url": (
                            "https://linuxjourney.com/"
                        )
                    },

                    {
                        "title": "Linux Documentation",
                        "url": (
                            "https://www.kernel.org/doc/html/latest/"
                        )
                    }
                ]
            },

            {
                "category": "Cybersecurity",
                "title": "Cybersecurity Fundamentals",
                "description": (
                    "Understand common threats, vulnerabilities "
                    "and security concepts."
                ),
                "what_to_learn": [
                    "Threats",
                    "Vulnerabilities",
                    "Authentication",
                    "Encryption",
                    "Security principles"
                ],
                "resources": [
                    {
                        "title": "Cisco Cybersecurity",
                        "url": (
                            "https://www.cisco.com/c/en/us/"
                            "products/security/what-is-cybersecurity.html"
                        )
                    },

                    {
                        "title": "YouTube Cybersecurity Fundamentals",
                        "url": (
                            "https://www.youtube.com/results?"
                            "search_query=cybersecurity+fundamentals+tutorial"
                        )
                    }
                ]
            }
        ]

    career_query = career.replace(" ", "+")
    return [
        {
            "category": "Career Fundamentals",
            "title": f"{career} Basics",
            "description": (
                f"Learn the fundamentals of {career} and "
                "understand the tools, concepts and skills "
                "required for this career."
            ),
            "what_to_learn": [
                f"Introduction to {career}",
                "Core concepts",
                "Important tools",
                "Practical exercises",
                "Beginner projects"
            ],
            "resources": [
                {
                    "title": (
                        f"YouTube {career} Tutorials"
                    ),
                    "url": (
                        "https://www.youtube.com/results?"
                        f"search_query={career_query}+tutorial"
                    )
                }
            ]
        },

        {
            "category": "Practice",
            "title": f"{career} Practice",
            "description": (
                f"Practice the important concepts of {career} "
                "by building small practical projects."
            ),
            "what_to_learn": [
                "Hands-on practice",
                "Small exercises",
                "Portfolio projects",
                "Problem solving"
            ],
            "resources": [
                {
                    "title": (
                        f"YouTube {career} Projects"
                    ),
                    "url": (
                        "https://www.youtube.com/results?"
                        f"search_query={career_query}+projects"
                    )
                }
            ]
        }
    ]

def create_project_for_skill(skill_title, career):
    career_lower = career.lower()
    skill_lower = skill_title.lower()
    if (
        "video" in career_lower
        or "editing" in career_lower
    ):
        if (
            "basic" in skill_lower
            or "editing" in skill_lower
        ):
            return {
                "title": (
                    "Short Video Editing Project"
                ),
                "description": (
                    "Create a 30–60 second edited video "
                    "using cuts, transitions, music, text "
                    "and basic storytelling."
                ),
                "category": "Video Editing",
                "skills": [
                    "Video Editing",
                    "Cutting",
                    "Transitions",
                    "Audio",
                    "Storytelling"
                ]
            }
        if "audio" in skill_lower:
            return {
                "title": (
                    "Video Audio Editing Project"
                ),
                "description": (
                    "Create a short video with clean dialogue, "
                    "background music and suitable sound effects."
                ),
                "category": "Video Editing",
                "skills": [
                    "Audio Editing",
                    "Music",
                    "Sound Effects",
                    "Audio Mixing"
                ]
            }
        if "color" in skill_lower:
            return {
                "title": (
                    "Color Grading Practice Project"
                ),
                "description": (
                    "Take raw video footage and create a "
                    "professionally corrected and graded final video."
                ),
                "category": "Video Editing",
                "skills": [
                    "Color Correction",
                    "Color Grading",
                    "Exposure",
                    "Contrast"
                ]
            }
        if "motion" in skill_lower:
            return {
                "title": (
                    "Motion Graphics Project"
                ),
                "description": (
                    "Create a short video containing animated "
                    "text, titles, keyframes and basic motion graphics."
                ),
                "category": "Video Editing",
                "skills": [
                    "Motion Graphics",
                    "Keyframes",
                    "Text Animation",
                    "Visual Effects"
                ]
            }
    if "python" in career_lower:
        if "flask" in skill_lower:
            return {
                "title": (
                    "Flask Student Management System"
                ),
                "description": (
                    "Build a Flask web application where users "
                    "can add, update, view and delete student records."
                ),
                "category": "Backend",
                "skills": [
                    "Python",
                    "Flask",
                    "MongoDB",
                    "CRUD"
                ]
            }

        if (
            "mongo" in skill_lower
            or "database" in skill_lower
        ):
            return {
                "title": (
                    "Python MongoDB CRUD Application"
                ),
                "description": (
                    "Build a Python application that stores "
                    "and manages data using MongoDB CRUD operations."
                ),
                "category": "Backend",
                "skills": [
                    "Python",
                    "MongoDB",
                    "CRUD",
                    "Database"
                ]
            }
        return {
            "title": (
                "Python Practice Application"
            ),
            "description": (
                "Build a practical Python application to "
                "demonstrate programming fundamentals, functions "
                "and problem solving."
            ),
            "category": "Programming",
            "skills": [
                "Python",
                "Programming",
                "Logic",
                "Problem Solving"
            ]
        }
    if (
        "web" in career_lower
        or "frontend" in career_lower
        or "full stack" in career_lower
        or "fullstack" in career_lower
    ):
        if (
            "html" in skill_lower
            or "css" in skill_lower
        ):
            return {
                "title": (
                    "Responsive Portfolio Website"
                ),
                "description": (
                    "Build a responsive personal portfolio "
                    "website using HTML and CSS."
                ),
                "category": "Frontend",
                "skills": [
                    "HTML",
                    "CSS",
                    "Responsive Design"
                ]
            }
        if "javascript" in skill_lower:
            return {
                "title": (
                    "JavaScript To-Do Application"
                ),
                "description": (
                    "Build an interactive To-Do application "
                    "using JavaScript and browser storage."
                ),
                "category": "Frontend",
                "skills": [
                    "JavaScript",
                    "DOM",
                    "Events",
                    "Local Storage"
                ]
            }
        return {
            "title": (
                "Full Stack Web Application"
            ),
            "description": (
                "Build a complete web application with "
                "frontend, backend, database and user interaction."
            ),
            "category": "Full Stack",
            "skills": [
                "HTML",
                "CSS",
                "JavaScript",
                "Backend",
                "Database"
            ]
        }
    if (
        "cyber" in career_lower
        or "security" in career_lower
    ):
        if "network" in skill_lower:
            return {
                "title": (
                    "Network Security Analysis Project"
                ),
                "description": (
                    "Create a beginner-friendly network analysis "
                    "project to understand network traffic and "
                    "common security concepts."
                ),
                "category": "Cybersecurity",
                "skills": [
                    "Networking",
                    "Security",
                    "Threat Analysis"
                ]
            }
        return {
            "title": (
                "Cybersecurity Security Audit"
            ),
            "description": (
                "Create a basic security audit report "
                "identifying common security risks and "
                "recommended protections."
            ),
            "category": "Cybersecurity",
            "skills": [
                "Cybersecurity",
                "Security",
                "Risk Analysis"
            ]
        }
    return {
        "title": (
            f"{skill_title} Practice Project"
        ),
        "description": (
            f"Build a practical project to apply what "
            f"you learned about {skill_title}."
        ),
        "category": "Practice",
        "skills": [
            skill_title
        ]
    }

@app.route("/api/roadmap/generate", methods=["POST"])
@login_required
def generate_ai_roadmap():
    try:
        data = request.get_json(silent=True) or {}
        career = data.get("career", "").strip()
        if not career:
            return jsonify(
                {
                    "success": False,
                    "message": ("Please enter a career name.")
                }
            ), 400
        if len(career) > 100:
            return jsonify(
                {
                    "success": False,
                    "message": ("Career name is too long.")
                }
            ), 400
        user_id = ObjectId(session["user_id"])
        user = db.users.find_one(
            {"_id": user_id}
        )
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404

        prompt = f"""
Create a practical beginner-friendly career roadmap for:
Career: {career}

The roadmap must be useful for a student who wants to learn
this career from beginner level to job/project-ready level.

For every roadmap step provide:
1. category
2. title
3. description
4. what_to_learn
5. resources

RESOURCE RULES:
- Resources MUST be free to access.
- Do NOT recommend paid-only courses.
- Do NOT recommend Udemy paid courses.
- Do NOT recommend Coursera paid courses.
- Do NOT invent URLs.
- Do NOT create fake URLs.
- Do NOT use "#" as a URL.
- Every resource URL must be a real HTTPS URL.
- Prefer resources that are actually available for free.

Try to provide 2 to 4 useful resources for every topic.

Resource priority:
1. YouTube free video tutorials
2. W3Schools free tutorials and exercises when relevant
3. MDN Web Docs when relevant
4. freeCodeCamp when relevant
5. CodeDex when relevant for programming/coding
6. Official documentation when it is free
7. Other reliable completely-free educational websites
8. Completely free coding/practice websites

RESOURCE SELECTION RULE:
- For programming and web-development topics, prefer:
YouTube + W3Schools + MDN/freeCodeCamp + CodeDex/practice.
- For HTML, CSS, JavaScript, Python, SQL and similar topics,
prefer W3Schools whenever a relevant tutorial exists.
- For coding practice, prefer free practice resources such as
W3Schools Exercises, CodeDex, freeCodeCamp and other
completely free practice platforms when relevant.
- For non-programming skills such as Video Editing, UI/UX,
Graphic Design, Cybersecurity, Data Analysis, etc., use
YouTube and other completely free educational/tutorial
websites that are actually relevant to that skill.
- Do not force W3Schools or CodeDex for skills where they
are not relevant.
- Prefer at least ONE YouTube tutorial for each topic when
a suitable free tutorial exists.
- Prefer 2 to 4 resources per roadmap step.
- Every resource must have a direct working HTTPS URL.
- Never return "#" as a URL.
- Never return an empty URL.
- Never invent a URL.
- Never return a paid-only resource.
- Never return a fake or guessed URL.

For programming topics:
- Prefer W3Schools tutorials and exercises.
- Prefer CodeDex where relevant.
- Prefer freeCodeCamp.
- Include at least one free video tutorial when possible.

For web development:
- Prefer W3Schools.
- Prefer MDN Web Docs.
- Prefer freeCodeCamp.
- Include YouTube tutorials.

For non-programming careers:
- Find completely free educational websites, tutorials,
documentation, practice resources, and YouTube tutorials
relevant to that skill.
- Do not force W3Schools or CodeDex when they are not relevant.

IMPORTANT:
- Search the web when necessary to find current real resources.
- Only return URLs that you have good reason to believe are real.
- The URL must directly lead to the learning resource.
- Do not return search-result pages when a direct tutorial/resource
URL is available.
- Prefer stable tutorial pages over temporary links.
- Do not include paid resources.

Return only valid JSON matching the requested schema.
"""
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "career": {"type": "STRING"},
                        "steps": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "category": {"type": "STRING"},
                                    "title": {"type": "STRING"},
                                    "description": {"type": "STRING"},
                                    "what_to_learn": {"type": "ARRAY",
                                        "items": {"type": "STRING"}},
                                    "resources": {"type": "ARRAY",
                                        "items": {"type": "OBJECT",
                                            "properties": {
                                                "title": {"type": "STRING"},
                                                "url": {"type": "STRING"}
                                            },
                                            "required": ["title","url"]
                                        }
                                    }
                                },
                                "required": [
                                    "category",
                                    "title",
                                    "description",
                                    "what_to_learn",
                                    "resources"
                                ]
                            }
                        }
                    },

                    "required": [
                        "career",
                        "steps"
                    ]
                }
            )
        )

        ai_text = (response.text or "").strip()
        print("================================")
        print("GEMINI ROADMAP RESPONSE")
        print(ai_text)
        print("================================")
        if not ai_text:
            return jsonify(
                {
                    "success": False,
                    "message": ("Gemini returned an empty response.")
                }
            ), 500
        roadmap_data = json.loads(ai_text)
        steps = roadmap_data.get("steps",[])
        if not steps:
            return jsonify(
                {
                    "success": False,
                    "message": ("Gemini returned an empty roadmap.")
                }
            ), 500
        final_steps = []
        career_id = "".join(
            character.lower()
            if character.isalnum()
            else "-"
            for character in career
        ).strip("-")
        for index, step in enumerate(steps,start=1):
            what_to_learn = step.get("what_to_learn",[])
            resources = step.get("resources",[])
            if not isinstance(what_to_learn, list):
                what_to_learn = []
            if not isinstance(resources, list):
                resources = []
            clean_resources = []
            for resource in resources:
                if not isinstance(resource, dict):
                    continue
                title = str(resource.get("title","Learning Resource")).strip()
                url = str(resource.get("url","")).strip()
                if not url.lower().startswith("https://"):
                    continue
                if (url == "#" or not url):
                    continue
                clean_resources.append(
                    {
                        "title": (title or "Learning Resource"),
                        "url": url
                    }
                )
            final_steps.append(
                {
                    "id": (f"ai-{career_id}"
                        f"-step-{index}"
                    ),
                    "category": step.get("category", "General"),
                    "title": step.get("title", f"Step {index}"),
                    "description": step.get("description", "Learn and practice this career skill."),
                    "what_to_learn": what_to_learn,
                    "resources": clean_resources
                }
            )
        roadmap_record = {
            "career": career,
            "roadmap": final_steps,
            "source": "gemini"
        }
        db.users.update_one(
            {"_id": user_id},
            {"$pull": {"ai_roadmaps": {"career": career}}}
        )

        db.users.update_one(
            {"_id": user_id},
            {"$push": {"ai_roadmaps": roadmap_record},
                "$set": {"selected_career": career}
            }
        )
        print("AI ROADMAP SAVED:", career)
        return jsonify(
            {
                "success": True,
                "cached": False,
                "career": career,
                "roadmap": final_steps
            }
        ), 200
    except json.JSONDecodeError as error:
        print("JSON PARSE ERROR:",repr(error))
        return jsonify(
            {
                "success": False,
                "message": ("Gemini returned invalid JSON.")
            }
        ), 500
    except Exception as error:
        print("================================")
        print("AI ROADMAP ERROR")
        print("================================")
        print("ERROR TYPE:", type(error).__name__)
        print("ERROR:", str(error))
        traceback.print_exc()
        print("================================")
        error_text = str(error).upper()
        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "QUOTA" in error_text
        ):

            print("Gemini quota unavailable.")
            print("Using local fallback roadmap for:", career)
            fallback_steps = create_fallback_roadmap(career)
            career_id = "".join(
                character.lower()
                if character.isalnum()
                else "-"
                for character in career
            ).strip("-")
            final_steps = []
            for index, step in enumerate(fallback_steps,start=1):
                final_steps.append(
                    {
                        "id": (f"ai-{career_id}" f"-step-{index}"),
                        "category": step.get("category", "General"),
                        "title": step.get("title", f"Step {index}"),
                        "description": step.get("description", "Learn and practice this career skill."),
                        "what_to_learn": step.get("what_to_learn", []),
                        "resources": step.get("resources", [])
                    }
                )

            roadmap_record = {
                "career": career,
                "roadmap": final_steps,
                "source": "local_fallback"
            }

            db.users.update_one(
                {"_id": user_id},
                {"$pull": {"ai_roadmaps": {"career": career}}}
            )

            db.users.update_one(
                {"_id": user_id},
                {"$push": {"ai_roadmaps": roadmap_record},
                    "$set": {"selected_career": career}}
            )
            print("LOCAL FALLBACK ROADMAP SAVED:", career)
            return jsonify(
                {
                    "success": True,
                    "cached": False,
                    "fallback": True,
                    "career": career,
                    "roadmap": final_steps,
                    "message": (
                        "Gemini quota is unavailable. "
                        "A local roadmap has been generated."
                    )
                }
            ), 200
        return jsonify(
            {
                "success": False,
                "message": (f"Gemini error: {str(error)}")
            }
        ), 500

@app.route("/api/roadmap")
@login_required
def get_roadmap_data():
    user = db.users.find_one(
        {"_id": ObjectId(session["user_id"])}
    )
    if not user:
        return jsonify(
            {"completed_steps": [], "started_steps": []}
        )
    completed_steps = user.get("completed_roadmap_steps", [])
    started_steps = user.get("started_roadmap_steps", [])
    if not isinstance(completed_steps, list):
        completed_steps = []
    if not isinstance(started_steps, list):
        started_steps = []
    return jsonify(
        {
            "completed_steps": completed_steps,
            "started_steps": started_steps
        }
    )
    
@app.route("/api/roadmap/start", methods=["POST"])
@login_required
def start_roadmap_step():
    try:
        user_id = ObjectId(session["user_id"])
        user = db.users.find_one(
            {"_id": user_id}
        )
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404
        data = request.get_json(silent=True) or {}
        step_id = str(data.get("step_id", "")).strip()
        print("================================")
        print("ROADMAP START REQUEST")
        print("STEP ID:", step_id)
        print("================================")
        if not step_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Step ID is missing."
                }
            ), 400
        roadmap_step = None
        career_name = "Career"
        ai_roadmaps = user.get("ai_roadmaps", [])
        if not isinstance(ai_roadmaps, list):
            ai_roadmaps = []
        for roadmap in ai_roadmaps:
            if not isinstance(roadmap, dict):
                continue
            current_career = str(
                roadmap.get("career", "Career")).strip()
            roadmap_steps = roadmap.get("roadmap", [])
            if not isinstance(roadmap_steps, list):
                continue
            for step in roadmap_steps:
                if not isinstance(step, dict):
                    continue
                current_step_id = str(step.get( "id", "")).strip()
                if current_step_id == step_id:
                    roadmap_step = step
                    career_name = (current_career or "Career")
                    break
            if roadmap_step:
                break
        if roadmap_step:
            skill_title = str(
                roadmap_step.get("title", "Untitled Skill")).strip()
        else:
            print("ROADMAP STEP NOT FOUND IN DATABASE:", step_id)
            skill_title = (step_id
                .replace("-", " ")
                .replace("_", " ")
                .strip()
                .title()
            )
        if not skill_title:
            skill_title = "Untitled Skill"
        started_steps = user.get("started_roadmap_steps", [])
        if not isinstance(started_steps, list):
            started_steps = []
        if step_id not in started_steps:
            started_steps.append(step_id)
        skill_record = {
            "step_id": step_id,
            "title": skill_title,
            "career": career_name,
            "progress": 50,
            "status": "In Progress"
        }
        try:
            project_template = create_project_for_skill(skill_title, career_name)
        except Exception as project_error:
            print("PROJECT TEMPLATE ERROR:", repr(project_error))
            project_template = {
                "title": (f"{skill_title} Practice Project"),
                "description": (
                    f"Build a practical project "
                    f"using {skill_title}."),
                "category": "Practice",
                "skills": [skill_title]
            }
        project_record = {
            "id": (f"{step_id}-project"),
            "title": project_template.get("title",
                f"{skill_title} Practice Project"),
            "description": project_template.get("description",
                f"Build a practical project using {skill_title}."),
            "category": project_template.get("category", "Practice"),
            "skills": project_template.get("skills",[skill_title]),
            "progress": 0,
            "status": "Not Started",
            "step_id": step_id,
            "career": career_name
        }
        existing_skills = user.get("skills", [])
        if not isinstance(existing_skills, list):
            existing_skills = []
        clean_skills = []
        for skill in existing_skills:
            if not isinstance(skill, dict):
                continue
            if (str(skill.get("step_id", ""))== step_id):
                continue
            clean_skills.append(skill)
        clean_skills.append(skill_record)
        existing_projects = user.get("projects", [])
        if not isinstance(existing_projects, list):
            existing_projects = []
        clean_projects = []
        for project in existing_projects:
            if not isinstance(project, dict):
                continue
            if (str(project.get("step_id", ""))== step_id):
                continue
            clean_projects.append(project)
        clean_projects.append(project_record)

        db.users.update_one(
            {"_id": user_id},
            {"$set": {"started_roadmap_steps": (started_steps),
                    "skills": clean_skills,
                    "projects": clean_projects
                }
            }
        )

        print("================================")
        print("ROADMAP STEP STARTED SUCCESSFULLY")
        print("STEP:", skill_title)
        print("CAREER:", career_name)
        print("PROJECT:", project_record["title"])
        print("================================")
        return jsonify(
            {
                "success": True,
                "step_id": step_id,
                "started": True,
                "skill": skill_record,
                "project": project_record,
                "started_steps": started_steps
            }
        ), 200
    except Exception as error:
        print("================================")
        print("START ROADMAP ERROR")
        print("================================")
        print("ERROR TYPE:", type(error).__name__)
        print("ERROR:", str(error))
        traceback.print_exc()
        print("================================")
        return jsonify(
            {
                "success": False,
                "message": ("Unable to start this topic."),
                "error": str(error)
            }
        ), 500

@app.route("/api/roadmap/complete", methods=["POST"])
@login_required
def complete_roadmap_step():
    try:
        user_id = ObjectId( session["user_id"])
        data = request.get_json(silent=True) or {}
        step_id = str(data.get("step_id", "")).strip()
        if not step_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Step ID is missing."
                }
            ), 400
        user = db.users.find_one({"_id": user_id})
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404
        completed_steps = user.get("completed_roadmap_steps", [])
        if not isinstance(completed_steps, list):
            completed_steps = []
        if step_id not in completed_steps:
            completed_steps.append(step_id)
        skills = user.get("skills", [])
        if not isinstance(skills, list):
            skills = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            if (str(skill.get("step_id", ""))== step_id):
                skill["progress"] = 100
                skill["status"] = "Completed"
        projects = user.get("projects", [])
        if not isinstance(projects, list):
            projects = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            if (str(project.get("step_id", ""))== step_id):
                project["progress"] = 100
                project["status"] = "Completed"
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"completed_roadmap_steps": (completed_steps),
                    "skills": skills,
                    "projects": projects
                }
            }
        )
        print( "ROADMAP STEP COMPLETED:", step_id)
        return jsonify(
            {
                "success": True,
                "completed": True,
                "step_id": step_id,
                "completed_steps": completed_steps,
                "progress": 100,
                "status": "Completed"
            }
        ), 200
    except Exception as error:
        print("COMPLETE ROADMAP ERROR:", repr(error))
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "message": ("Unable to complete this topic."),
                "error": str(error)
            }
        ), 500

@app.route("/api/projects/start", methods=["POST"])
@login_required
def start_project():
    try:
        data = request.get_json(silent=True) or {}
        project_id = str(data.get("project_id", "")).strip()
        if not project_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Project ID is missing."
                }
            ), 400
        user_id = ObjectId(session["user_id"])
        user = db.users.find_one({"_id": user_id})
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404
        projects = user.get("projects", [])
        if not isinstance(projects, list):
            projects = []
        project_found = False
        new_progress = 10
        for project in projects:
            if not isinstance(project, dict):
                continue
            if project.get("id") == project_id:
                old_progress = project.get("progress", 0)
                try:
                    old_progress = int(old_progress)
                except (TypeError, ValueError):
                    old_progress = 0
                new_progress = max(old_progress, 10)
                project["progress"] = new_progress
                project["status"] = "In Progress"
                project_found = True
                break
        if not project_found:
            return jsonify(
                {
                    "success": False,
                    "message": "Project not found."
                }
            ), 404
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"projects": projects}}
        )
        return jsonify(
            {
                "success": True,
                "project_id": project_id,
                "progress": new_progress,
                "status": "In Progress"
            }
        ), 200
    except Exception as error:
        print("START PROJECT ERROR:", repr(error))
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "message": ("Unable to start project."),
                "error": str(error)
            }
        ), 500

@app.route("/api/projects/complete", methods=["POST"])
@login_required
def complete_project():
    try:
        data = request.get_json(silent=True) or {}
        project_id = str(data.get("project_id", "")).strip()
        if not project_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Project ID is missing."
                }
            ), 400
        user_id = ObjectId(session["user_id"])
        user = db.users.find_one({"_id": user_id})
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404
        projects = user.get("projects", [])
        if not isinstance(projects, list):
            projects = []
        project_found = False
        for project in projects:
            if not isinstance(project, dict):
                continue
            if project.get("id") == project_id:
                project["progress"] = 100
                project["status"] = "Completed"
                project_found = True
                break
        if not project_found:
            return jsonify(
                {
                    "success": False,
                    "message": "Project not found."
                }
            ), 404
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"projects": projects}}
        )
        return jsonify(
            {
                "success": True,
                "project_id": project_id,
                "progress": 100,
                "status": "Completed"
            }
        ), 200
    except Exception as error:
        print("COMPLETE PROJECT ERROR:", repr(error))
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "message": ("Unable to complete project."),
                "error": str(error)
            }
        ), 500

@app.route("/api/roadmap/uncomplete", methods=["POST"])
@login_required
def uncomplete_roadmap_step():
    try:
        user_id = ObjectId(session["user_id"])
        data = request.get_json(silent=True) or {}
        step_id = str(data.get("step_id", "")).strip()
        if not step_id:
            return jsonify(
                {
                    "success": False,
                    "message": "Step ID is missing."
                }
            ), 400
        user = db.users.find_one({"_id": user_id})
        if not user:
            return jsonify(
                {
                    "success": False,
                    "message": "User not found."
                }
            ), 404
        completed_steps = user.get("completed_roadmap_steps", [])
        if not isinstance(completed_steps, list):
            completed_steps = []
        if step_id in completed_steps:
            completed_steps.remove(step_id)
        skills = user.get("skills", [])
        if not isinstance(skills, list):
            skills = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            if (str(skill.get("step_id", ""))== step_id):
                skill["progress"] = 50
                skill["status"] = "In Progress"
        projects = user.get("projects", [])
        if not isinstance(projects, list):
            projects = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            if (str(project.get("step_id", ""))== step_id):
                try:
                    old_progress = int(project.get("progress", 0))
                except (TypeError, ValueError):
                    old_progress = 0
                project["progress"] = max(old_progress, 0)
                project["status"] = "In Progress"
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"completed_roadmap_steps": (completed_steps),
                    "skills": skills,
                    "projects": projects
                }
            }
        )
        return jsonify(
            {
                "success": True,
                "completed": False,
                "completed_steps": completed_steps
            }
        ), 200
    except Exception as error:
        print("UNCOMPLETE ROADMAP ERROR:", repr(error))
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "message": ("Unable to reset this topic."),
                "error": str(error)
            }
        ), 500

@app.route("/skills")
@login_required
def skills():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": user_id})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    skills_data = user.get("skills", [])
    if not isinstance(skills_data, list):
        skills_data = []
    cleaned_skills = []
    for skill in skills_data:
        if not isinstance(skill, dict):
            continue
        progress = skill.get("progress", 0)
        try:
            progress = int(progress)
        except (TypeError, ValueError):
            progress = 0
        progress = max(0,min(100,progress))
        cleaned_skills.append(
            {
                "step_id": skill.get("step_id", ""),
                "title": skill.get("title", "Unknown Skill"),
                "career": skill.get("career", "Career Skill"),
                "progress": progress,
                "status": skill.get("status", "In Progress")
            }
        )
    total_skills = len(cleaned_skills)
    strong_skills = sum(
        1
        for skill in cleaned_skills
        if skill["progress"] >= 80
    )
    average_level = round(
        sum(
            skill["progress"]
            for skill in cleaned_skills
        )
        / total_skills
    ) if total_skills else 0
    incomplete_skills = [
        skill
        for skill in cleaned_skills
        if skill["progress"] < 100
    ]
    if incomplete_skills:
        incomplete_skills.sort(key=lambda skill: skill["progress"])
        next_focus = (incomplete_skills[0]["title"])
    else:
        next_focus = (
            "Start learning"
            if not cleaned_skills
            else "All skills completed 🎉"
        )
    return render_template("skills.html",
        user=user,
        skills_data=cleaned_skills,
        total_skills=total_skills,
        strong_skills=strong_skills,
        average_level=average_level,
        next_focus=next_focus
    )

@app.route("/courses")
@login_required
def courses():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": user_id})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    skills_data = user.get("skills", [])
    if not isinstance(skills_data, list):
        skills_data = []
    courses_data = []
    for skill in skills_data:
        if not isinstance(skill, dict):
            continue
        progress = skill.get("progress", 0)
        try:
            progress = int(progress)
        except (TypeError, ValueError):
            progress = 0
        progress = max(0,min(100,progress))
        courses_data.append(
            {
                "title": skill.get("title", "Untitled Course"),
                "career": skill.get("career", "Career Skill"),
                "progress": progress,
                "status": skill.get("status", "In Progress"),
                "step_id": skill.get("step_id", "")
            }
        )
    total_courses = len(courses_data)
    completed_courses = sum( 1
        for course in courses_data
        if course.get("progress",0) >= 100
    )
    course_progress = round(
        sum(
            course.get("progress",0)
            for course in courses_data
        )
        / total_courses
    ) if total_courses else 0
    return render_template("courses.html",
        user=user,
        courses_data=courses_data,
        total_courses=total_courses,
        completed_courses=completed_courses,
        course_progress=course_progress
    )

@app.route("/projects")
@login_required
def projects():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one(
        {"_id": user_id})

    if not user:
        session.clear()
        return redirect(url_for("login"))
    projects_data = user.get("projects",[])
    if not isinstance(projects_data,list):
        projects_data = []
    cleaned_projects = []
    for project in projects_data:
        if not isinstance(project,dict):
            continue
        progress = project.get("progress",0)
        try:
            progress = int(progress)
        except (TypeError,ValueError):
            progress = 0
        progress = max(0,min(100,progress))

        cleaned_projects.append(
            {
                "id": project.get("id",""),
                "title": project.get("title","Untitled Project"),
                "description": project.get("description","Build this project to practice your skills."),
                "category": project.get("category","Practice"),
                "skills": project.get("skills",[]),
                "progress": progress,
                "status": project.get("status","Not Started"),
                "step_id": project.get("step_id",""),
                "career": project.get("career","")
            }
        )

    total_projects = len(cleaned_projects)
    completed_projects = sum( 1
        for project in cleaned_projects
        if project["progress"] >= 100
    )

    project_progress = round(
        sum(
            project["progress"]
            for project in cleaned_projects
        )
        / total_projects
    ) if total_projects else 0

    return render_template("projects.html",
        user=user,
        projects_data=cleaned_projects,
        total_projects=total_projects,
        completed_projects=completed_projects,
        project_progress=project_progress
    )

@app.route("/progress")
@login_required
def progress():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": user_id})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    skills_data = user.get("skills", [])
    if not isinstance(skills_data, list):
        skills_data = []
    valid_skills = [
        skill for skill in skills_data
        if isinstance(skill, dict)
    ]
    total_skills = len(valid_skills)
    skill_progress_values = []
    for skill in valid_skills:
        try:
            progress_value = int(skill.get("progress", 0) or 0)
        except (TypeError, ValueError):
            progress_value = 0
        progress_value = max(0, min(100, progress_value))
        skill_progress_values.append(progress_value)
    skill_progress = round(
        sum(skill_progress_values) / total_skills
    ) if total_skills else 0
    course_progress = skill_progress
    projects_data = user.get("projects", [])
    if not isinstance(projects_data, list):
        projects_data = []
    valid_projects = [
        project for project in projects_data
        if isinstance(project, dict)
    ]
    total_projects = len(valid_projects)
    project_progress_values = []
    for project in valid_projects:
        try:
            progress_value = int(project.get("progress", 0) or 0)
        except (TypeError, ValueError):
            progress_value = 0
        progress_value = max(0, min(100, progress_value))
        project_progress_values.append(progress_value)
    project_progress = round(
        sum(project_progress_values) / total_projects
    ) if total_projects else 0
    completed_steps = user.get("completed_roadmap_steps", [])
    if not isinstance(completed_steps, list):
        completed_steps = []
    ai_roadmaps = user.get("ai_roadmaps", [])
    if not isinstance(ai_roadmaps, list):
        ai_roadmaps = []
    selected_career = str(user.get("selected_career", "")).strip()
    selected_roadmap = None
    if selected_career:
        for roadmap in ai_roadmaps:
            if not isinstance(roadmap, dict):
                continue
            roadmap_career = str(roadmap.get("career", "")).strip()
            if roadmap_career.lower() == selected_career.lower():
                selected_roadmap = roadmap
                break
    if selected_roadmap is None and ai_roadmaps:
        selected_roadmap = ai_roadmaps[-1]
    roadmap_steps = []
    if selected_roadmap:
        roadmap_steps = selected_roadmap.get("roadmap", [])
    if not isinstance(roadmap_steps, list):
        roadmap_steps = []
    valid_roadmap_steps = [
        step
        for step in roadmap_steps
        if isinstance(step, dict)
        and str(step.get("id", "")).strip()
    ]
    total_roadmap_steps = len(valid_roadmap_steps)
    completed_roadmap_steps = sum(
        1
        for step in valid_roadmap_steps
        if str(step.get("id", "")).strip() in completed_steps
    )
    roadmap_progress = round(
        (completed_roadmap_steps / total_roadmap_steps) * 100
    ) if total_roadmap_steps else 0
    overall_progress = round(
        (
            roadmap_progress
            + skill_progress
            + project_progress
        ) / 3
    )
    return render_template("progress.html",
    user=user,
    progress={
        "roadmap_progress": roadmap_progress,
        "skill_progress": skill_progress,
        "course_progress": course_progress,
        "project_progress": project_progress,
        "overall_progress": overall_progress,
        "completed_roadmap_steps": completed_roadmap_steps,
        "total_roadmap_steps": total_roadmap_steps,
        "total_skills": total_skills,
        "total_projects": total_projects
    }
)

@app.route("/profile")
@login_required
def profile():
    user = db.users.find_one(
        {"_id": ObjectId(session["user_id"])}
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("profile.html",user=user)

@app.route("/profile/update",methods=["POST"])
@login_required
def update_profile():
    user_id = ObjectId(session["user_id"])
    name = request.form.get("name","").strip()
    phone = request.form.get("phone","").strip()
    education = request.form.get("education","").strip()
    study_year = request.form.get("study_year","").strip()
    career_goal = request.form.get("career_goal","").strip()
    skill_level = request.form.get("skill_level","").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("profile"))
    db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "name": name,
                "phone": phone,
                "education": education,
                "study_year": study_year,
                "career_goal": career_goal,
                "skill_level": skill_level
            }
        }
    )

    flash("Profile updated successfully.","success")
    return redirect(url_for("profile"))

@app.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_profile_picture():
    if "profile_picture" not in request.files:
        flash("Please select a profile picture.", "error")
        return redirect(url_for("profile"))

    file = request.files["profile_picture"]
    if file.filename == "":
        flash("Please select a profile picture.", "error")
        return redirect(url_for("profile"))
    if not allowed_profile_picture(file.filename):
        flash(
            "Only JPG, JPEG, PNG and WEBP images are allowed.",
            "error"
        )
        return redirect(url_for("profile"))
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": user_id})

    if not user:
        session.clear()
        return redirect(url_for("login"))
    old_picture = user.get("profile_picture")
    extension = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{user_id}.{extension}"
    filepath = os.path.join(
        app.config["PROFILE_UPLOAD_FOLDER"],
        filename
    )
    file.save(filepath)
    if old_picture and old_picture != filename:
        old_filepath = os.path.join(
            app.config["PROFILE_UPLOAD_FOLDER"],
            old_picture
        )

        if os.path.exists(old_filepath):
            os.remove(old_filepath)

    db.users.update_one(
        {"_id": user_id},
        {"$set": {"profile_picture": filename}}
    )

    flash(
        "Profile picture updated successfully.",
        "success"
    )

    return redirect(url_for("profile"))

@app.route("/profile/remove-picture", methods=["POST"])
@login_required
def remove_profile_picture():
    user_id = ObjectId(session["user_id"])
    user = db.users.find_one({"_id": user_id})
    if not user:
        session.clear()
        return redirect(url_for("login"))
    old_picture = user.get("profile_picture")
    if old_picture:
        old_filepath = os.path.join(
            app.config["PROFILE_UPLOAD_FOLDER"],
            old_picture
        )
        if os.path.exists(old_filepath):
            os.remove(old_filepath)
        db.users.update_one(
            {"_id": user_id},
            {"$unset": {"profile_picture": ""}}
        )

    flash(
        "Profile picture removed.",
        "success"
    )
    return redirect(url_for("profile"))

@app.route("/settings")
@login_required
def settings():
    user = db.users.find_one(
        {"_id": ObjectId(session["user_id"])}
    )

    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("settings.html",user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)