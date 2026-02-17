from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse

import random
import time
import re
import PyPDF2
import spacy
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import io
import base64

from .models import Resume, UserSecurity, ActivityLog
from .utils import generate_report

nlp = spacy.load("en_core_web_sm")

OTP_STORAGE = {}

# ================= PASSWORD CHECK =================
def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


# ================= SKILL DATABASE =================
SKILL_DATABASE = {
    "python": "https://www.youtube.com/results?search_query=python+course",
    "django": "https://www.youtube.com/results?search_query=django+tutorial",
    "sql": "https://www.youtube.com/results?search_query=sql+course",
    "machine learning": "https://www.youtube.com/results?search_query=machine+learning+course",
    "html": "https://www.youtube.com/results?search_query=html+course",
    "css": "https://www.youtube.com/results?search_query=css+course",
    "javascript": "https://www.youtube.com/results?search_query=javascript+course",
    "react": "https://www.youtube.com/results?search_query=react+course",
    "aws": "https://www.youtube.com/results?search_query=aws+course",
    "docker": "https://www.youtube.com/results?search_query=docker+course",
}


# ================= EXPANDED ROLE MAP =================
ROLE_MAP = {
    "python": "Backend Developer",
    "django": "Backend Developer",
    "flask": "Backend Developer",
    "node js": "Backend Developer",
    "express js": "Backend Developer",
    "java": "Backend Developer",

    "html": "Frontend Developer",
    "css": "Frontend Developer",
    "javascript": "Frontend Developer",
    "react": "Frontend Developer",
    "angular": "Frontend Developer",

    "mongodb": "Full Stack Developer",
    "sql": "Full Stack Developer",
    "git": "Full Stack Developer",
    "github": "Full Stack Developer",

    "machine learning": "ML Engineer",
    "data science": "Data Scientist",
    "data analysis": "Data Analyst",

    "excel": "Data Analyst",
    "power bi": "Data Analyst",

    "aws": "Cloud Engineer",
    "docker": "DevOps Engineer",

    "c": "Software Engineer",
    "c++": "Software Engineer",
    "dsa": "Software Engineer",

    "nlp": "AI Engineer",
    "deep learning": "AI Engineer",

    "flutter": "Mobile Developer",
    "android": "Mobile Developer",

    "cyber security": "Security Analyst"
}


def extract_skills(text):
    text = text.lower()
    return [skill for skill in SKILL_DATABASE if skill in text]


# ================= LOGIN =================
def login_view(request):

    if request.method == "POST":

        username_input = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=username_input)
            username_input = user_obj.username
        except:
            pass

        user = authenticate(request, username=username_input, password=password)

        if user:
            login(request, user)
            ActivityLog.objects.create(user=user, action="User Login")
            return redirect("home")

        messages.error(request, "Invalid credentials")

    return render(request, "users/login.html")


# ================= REGISTER =================
def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not is_strong_password(password):
            messages.error(request, "Weak password")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        UserSecurity.objects.create(user=user, email_verified=True)

        messages.success(request, "Registration successful")
        return redirect("login")

    return render(request, "users/register.html")


# ================= FORGOT PASSWORD =================
def forgot_password(request):

    if request.method == "POST":

        identifier = request.POST.get("username")

        # 🔥 Allow username OR email
        try:
            if User.objects.filter(email=identifier).exists():
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)

        except User.DoesNotExist:
            messages.error(request, "Invalid username or email")
            return redirect("forgot_password")

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP + expiry
        OTP_STORAGE[user.username] = {
            "otp": otp,
            "expiry": time.time()+ 300  # 5 min
        }

        send_mail(
            "Password Reset OTP",
            f"Your OTP is {otp}. It expires in 5 minutes.",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False
        )

        request.session["reset_user"] = user.username
        messages.success(request, "OTP sent to your email")

        return redirect("reset_password")

    return render(request, "users/forgot_password.html")




# ================= RESET PASSWORD =================
def reset_password(request):

    username = request.session.get("reset_user")

    if not username:
        return redirect("login")

    if request.method == "POST":

        otp_entered = request.POST.get("otp")
        new_password = request.POST.get("new_password")

        otp_data = OTP_STORAGE.get(username)

        # OTP not generated
        if not otp_data:
            messages.error(request, "OTP not generated")
            return redirect("forgot_password")

        # OTP expired
        if time.time() > otp_data["expiry"]:
            OTP_STORAGE.pop(username, None)
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        # Wrong OTP
        if otp_data["otp"] != otp_entered:
            messages.error(request, "Invalid OTP")
            return redirect("reset_password")

        # Password strength check
        if not is_strong_password(new_password):
            messages.error(request, "Password too weak")
            return redirect("reset_password")

        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()

        OTP_STORAGE.pop(username, None)
        request.session.pop("reset_user", None)

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "users/reset_password.html")


# ================= HOME =================
@login_required
def home(request):

    latest_resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    activities = ActivityLog.objects.filter(user=request.user).order_by("-timestamp")[:5]

    return render(request, "users/home.html", {
        "latest_resume": latest_resume,
        "activities": activities
    })


# ================= UPLOAD RESUME =================
@login_required
def upload_resume(request):

    if request.method == "POST":

        uploaded_file = request.FILES.get("resume")

        if not uploaded_file:
            messages.error(request, "Upload resume first")
            return redirect("upload")

        job_description = request.POST.get("job_description", "")

        # -------- Extract Resume Text --------
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        resume_text = ""

        for page in pdf_reader.pages:
            if page.extract_text():
                resume_text += page.extract_text()

        # -------- Extract Skills --------
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(job_description)

        matched = list(set(resume_skills) & set(jd_skills))
        missing = list(set(jd_skills) - set(resume_skills))

        # -------- CORRECT SCORING --------
        total_jd = len(jd_skills)

        coverage = int((len(matched) / total_jd) * 100) if total_jd else 0
        gap = 100 - coverage
        score = coverage

        # -------- Role Prediction --------
        roles = list(set(ROLE_MAP[s] for s in matched if s in ROLE_MAP))

        # -------- Suggestions --------
        suggestions = [f"Improve skill: {s}" for s in missing]

        # -------- Save Resume --------
        resume_obj = Resume.objects.create(
            user=request.user,
            file=uploaded_file,
            score=score,
            matched_skills=matched,
            missing_skills=missing,
            coverage=coverage,
            gap=gap,
            recommended_roles=roles,
            suggestions=suggestions
        )

        ActivityLog.objects.create(user=request.user, action="Uploaded Resume")

        # -------- PIE CHART FIX --------
        matched_count = len(matched)
        missing_count = len(missing)

        # Prevent pie crash if both zero
        if matched_count == 0 and missing_count == 0:
            matched_count = 1
            missing_count = 0

        plt.figure(figsize=(5,5))
        plt.pie(
            [matched_count, missing_count],
            labels=['Matched Skills', 'Missing Skills'],
            autopct='%1.0f%%',
            startangle=90,
            colors=['#22c55e', '#ef4444'],
            wedgeprops={'edgecolor':'white'}
        )

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        chart = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return render(request, "users/dashboard.html", {
            "resume": resume_obj,
            "chart": chart,
            "matched": matched,
            "missing": missing,
            "score": score
        })

    return render(request, "users/upload.html")



# ================= HISTORY =================
@login_required
def history(request):

    resumes = Resume.objects.filter(user=request.user).order_by("-uploaded_at")

    paginator = Paginator(resumes, 8)
    page = request.GET.get("page")
    resumes = paginator.get_page(page)

    return render(request, "users/history.html", {"resumes": resumes})


# ================= DELETE =================
@login_required
def delete_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)
    resume.delete()
    return redirect("history")


# ================= BULK DELETE =================
@login_required
def bulk_delete(request):

    if request.method == "POST":
        ids = request.POST.getlist("resume_ids")
        Resume.objects.filter(id__in=ids, user=request.user).delete()

    return redirect("history")


# ================= COMPARE =================
@login_required
def compare_resumes(request):

    ids = request.GET.getlist("compare")
    resumes = Resume.objects.filter(id__in=ids, user=request.user)

    return render(request, "users/compare.html", {"resumes": resumes})


# ================= DOWNLOAD REPORT =================
@login_required
def download_report(request, resume_id):

    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    ActivityLog.objects.create(user=request.user, action="Downloaded Report")

    return generate_report(
        resume.score,
        resume.matched_skills,
        resume.missing_skills,
        resume.suggestions,
        request.user.username,
        resume.recommended_roles,
        resume.coverage,
        resume.gap
    )


# ================= LOGOUT =================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
