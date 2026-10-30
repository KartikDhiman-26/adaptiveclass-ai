
from app.performance_analyzer import analyze_records

dummy_records = [
    {
        "rollno": "101",
        "name": "Aarav",
        "subject": "Mathematics",
        "class": "CSE-A",
        "marks": "18",
        "max_marks": "20",
        "topic": "Algebra",
        "assessment": "Quiz 1",
        "date": "2026-10-20"
    },
    {
        "rollno": "101",
        "name": "Aarav",
        "subject": "Mathematics",
        "class": "CSE-A",
        "marks": "8",
        "max_marks": "20",
        "topic": "Calculus",
        "assessment": "Quiz 2",
        "date": "2026-10-25"
    },
    {
        "rollno": "102",
        "name": "Diya",
        "subject": "Mathematics",
        "class": "CSE-A",
        "marks": "17",
        "max_marks": "20",
        "topic": "Algebra",
        "assessment": "Quiz 1",
        "date": "2026-10-20"
    },
    {
        "rollno": "102",
        "name": "Diya",
        "subject": "Mathematics",
        "class": "CSE-A",
        "marks": "16",
        "max_marks": "20",
        "topic": "Calculus",
        "assessment": "Quiz 2",
        "date": "2026-10-25"
    }
]

result = analyze_records(dummy_records)

from pprint import pprint
pprint(result)
