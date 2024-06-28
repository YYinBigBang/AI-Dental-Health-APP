# Use the official Python image from Docker Hub as the base image
FROM python:3.10.12-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the dependencies file to the current directory
COPY requirements.txt .

# Install any dependencies listed in the requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables to ensure Python runs in a non-interactive mode
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Run Django's collectstatic command as part of the build process
RUN python manage.py collectstatic --no-input

# Expose port 8000 to the outside world
EXPOSE 8000

# Start the Gunicorn server, specifying the number of workers and the WSGI application
CMD ["gunicorn", "--workers=3", "--bind", "0.0.0.0:8000", "AI_Dental_Health_APP.wsgi:application"]
