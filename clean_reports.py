from app import app, db, Report
import json
import ast

# Ensure database operations run in the Flask application context
with app.app_context():
    reports = Report.query.all()
    for report in reports:
        try:
            # Convert diagnosis to valid JSON format
            diagnosis = ast.literal_eval(report.diagnosis)  # Convert to dict
            report.diagnosis = json.dumps(diagnosis)  # Convert to JSON string
        except Exception as e:
            print(f"Error processing report ID {report.id}: {e}")
            db.session.delete(report)  # Optionally delete invalid reports
    db.session.commit()

print("Database cleaning completed.")
