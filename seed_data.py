import sqlite3
import datetime

conn = sqlite3.connect('internloom.db')
cursor = conn.cursor()

# Insert the data
query = """
INSERT INTO job_listings 
(title, description, required_skills, preferred_skills, stipend, location, target_batch, deadline, max_applicants, current_applicants, status) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
data = (
    'Backend Intern', 
    'FastAPI work', 
    '["Python", "FastAPI"]', 
    '["Docker"]', 
    '30000 INR', 
    'Remote', 
    2026, 
    '2026-12-31 23:59:59', 
    50, 
    0, 
    'active'
)

cursor.execute(query, data)
conn.commit()
conn.close()
print("Data successfully inserted!")