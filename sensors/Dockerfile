FROM python:3.9-slim

WORKDIR /app

# Copy the requirements (if you had a requirements.txt, otherwise manual install)
# Install older paho-mqtt to be safe, or latest if you updated code
RUN pip install paho-mqtt==1.6.1

# COPY BOTH FILES: The script AND the config
COPY data_generator.py .
COPY config.ini .

CMD ["python", "-u", "data_generator.py"]