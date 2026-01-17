# 1. Use a lightweight Python image
FROM python:3.10-slim

# 2. Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set work directory
WORKDIR /app

# 4. Install system dependencies (needed for some python libs)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

# 5. Copy the entire mono-repo into the container
COPY . /app

# 6. Install your RDBMS library first (The Mono-repo link)
# This allows the app to 'import simpledb' from anywhere
RUN pip install --no-cache-dir ./simple_rdbms

# 7. Install Finance Tracker dependencies
RUN pip install --no-cache-dir -r finance_tracker/requirements.txt

# 8. Create the directory for your RDBMS data files
RUN mkdir -p /app/db_data

# 9. Set the environment variable for your DB location
ENV DB_PATH=/app/db_data

# 10. Start the application
# --workers 1 is MANDATORY for your internal Thread Lock to work
CMD ["uvicorn", "finance_tracker.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]