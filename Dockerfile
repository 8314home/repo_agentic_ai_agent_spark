# 1. Use an official stable slim Python image as base
FROM python:3.11-slim

# 2. Prevent Python from writing .pyc files and buffer streams for real-time logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Install OpenJDK 17 (mandatory for PySpark) and basic system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Set up critical System Environment paths for Java and Spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 5. Set the default working directory inside the container space
WORKDIR /app

# 6. Copy the dependencies file first to leverage Docker cache layers
COPY requirements.txt .

# 7. Install your pinned Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copy the entire workspace code assets into the container space
COPY . .

# 9. Ensure execution paths match relative workspace directories
ENV PYTHONPATH=/app

# 10. Default entry point command to execute your orchestration loop script
CMD ["python", "main.py"]
