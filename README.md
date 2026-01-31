# Smart City IoT Monitoring System

## Project Overview

This project implements a Smart City monitoring platform based on Internet of Things (IoT) technologies.  
The system simulates an urban sensor network that monitors environmental and traffic-related parameters such as temperature, humidity, air quality, noise levels, and traffic density across multiple city districts.

The architecture follows a fully containerized microservices approach and integrates real-time data generation, message-based communication, time-series data storage, automated data analysis, alerting mechanisms, and centralized visualization to support data-driven urban management.

---

## System Architecture

The system is composed of the following components:

- **Python Simulator** – Generates synthetic IoT sensor data
- **MQTT (Mosquitto)** – Message broker for real-time communication
- **Telegraf** – Data ingestion and preprocessing agent
- **InfluxDB** – Time-series database for data storage
- **Node-RED** – Data processing and alerting logic
- **Grafana** – Web-based monitoring dashboard
- **Telegram Bot** – Automated alert notification service

All components are deployed as Docker containers and orchestrated using Docker Compose.

---

## Requirements

- Docker  
- Docker Compose  

---

## Setup and Execution

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-root>

### 2. Create the .env file

After cloning the repository, create a .env file in the project root directory with the following content:

```bash
TELEGRAM_TOKEN=8458510312:AAFgcKYmvDqk6gj8xI55lpcynFmudzdvYTA
TELEGRAM_CHATID=-5200673556
INFLUX_TOKEN=my-super-secret-auth-token
MQTT_USER=iot_user
MQTT_PASSWORD=iot_password
DOCKER_INFLUXDB_INIT_PASSWORD=admin12345
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token


### 3. Start thhe system

From the root directory of the project, run:

```bash
docker compose up --build

Docker Compose will build and start all services required for the Smart City monitoring system.
