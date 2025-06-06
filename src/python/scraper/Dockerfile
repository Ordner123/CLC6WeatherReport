# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your code
COPY Scraper.py MetarTaf.py scraper/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run Scraper.py when the container starts
CMD ["python", "Scraper.py"]
