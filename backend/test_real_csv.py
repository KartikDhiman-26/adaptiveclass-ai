
import json
from pathlib import Path

from app.ai_pipeline import process_assessment_csv

# Read the sample CSV
csv_path = Path("sample_assessment.csv")
csv_content = csv_path.read_bytes()

print("\nStarting AdaptiveClass AI/ML Pipeline...\n")

# Run the actual pipeline without database storage
result = process_assessment_csv(
    file_content=csv_content,
    teacher_id=1,
    db=None,
    filename="sample_assessment.csv"
)

# Display the result
print("PIPELINE STATUS:", result.get("status"))
print("\nCOMPLETE PIPELINE OUTPUT:\n")

print(json.dumps(result, indent=4, default=str))

# Check important components
print("\n--- COMPONENT CHECK ---")
print("CSV Status:", result.get("status"))
print("Class Analytics:", bool(result.get("class_analytics")))
print("Student Analytics:", len(result.get("student_analytics", [])))
print("Detected Patterns:", len(result.get("pattern_detection", [])))
print("AI Summary:", result.get("ai_insights", {}).get("class_summary"))
