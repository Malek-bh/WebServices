FROM python:3.11

# Expose the application port
EXPOSE 5000

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY . .

# Install FastAPI and other dependencies
RUN pip install -r requirements.txt

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]


