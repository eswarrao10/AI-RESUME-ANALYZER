# ================= SKILL DATABASE WITH LEARNING LINKS =================
SKILL_DATABASE = {
    "python": "https://www.youtube.com/results?search_query=python+full+course",
    "django": "https://www.youtube.com/results?search_query=django+tutorial",
    "sql": "https://www.youtube.com/results?search_query=sql+full+course",
    "machine learning": "https://www.youtube.com/results?search_query=machine+learning+course",
    "html": "https://www.youtube.com/results?search_query=html+full+course",
    "css": "https://www.youtube.com/results?search_query=css+full+course",
    "javascript": "https://www.youtube.com/results?search_query=javascript+course",
    "react": "https://www.youtube.com/results?search_query=react+js+course",
    "node js": "https://www.youtube.com/results?search_query=node+js+course",
    "express js": "https://www.youtube.com/results?search_query=express+js+tutorial",
    "angular": "https://www.youtube.com/results?search_query=angular+course",
    "java": "https://www.youtube.com/results?search_query=java+full+course",
    "c": "https://www.youtube.com/results?search_query=c+programming+course",
    "c++": "https://www.youtube.com/results?search_query=c%2B%2B+course",
    "mongodb": "https://www.youtube.com/results?search_query=mongodb+course",
    "data science": "https://www.youtube.com/results?search_query=data+science+course",
    "data analysis": "https://www.youtube.com/results?search_query=data+analysis+course",
    "excel": "https://www.youtube.com/results?search_query=excel+course",
    "power bi": "https://www.youtube.com/results?search_query=power+bi+course",
    "aws": "https://www.youtube.com/results?search_query=aws+course",
    "docker": "https://www.youtube.com/results?search_query=docker+course",
    "git": "https://www.youtube.com/results?search_query=git+and+github+tutorial",
    "github": "https://www.youtube.com/results?search_query=github+tutorial",
    "dsa": "https://www.youtube.com/results?search_query=data+structures+and+algorithms+course"
}


# ================= SKILL EXTRACTION =================
def extract_skills(text):
    text = text.lower()
    found = []

    for skill in SKILL_DATABASE.keys():
        if skill in text:
            found.append(skill)

    return list(set(found))
