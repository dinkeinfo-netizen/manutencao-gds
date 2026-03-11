# GDS Maintenance System - RQ MAN – 073 01

A comprehensive Flask-based web application for managing maintenance orders (OS), equipment, and technical staff. This system streamlines the maintenance workflow from request to completion, including digital signatures and automated notifications.

## 🚀 Features

- **Maintenance Order Management**: Create, track, and complete maintenance orders.
- **Workflow Automation**: Automated status transitions (Open -> In Progress -> Completed).
- **Digital Signatures**: Technical and supervisor digital signatures for verification.
- **Bulk Import/Export**: Import equipment and locations via Excel; export maintenance history and KPIs.
- **Analytics Dashboard**: Real-time KPIs for mechanics, equipment downtime, and maintenance types.
- **User Roles**: Specialized access for Admin, Mechanics, and Standard Users.
- **Email Notifications**: Automated alerts for new and finalized maintenance activities.

## 🛠 Technology Stack

- **Backend**: Python / Flask
- **Database**: MySQL 8.0
- **Frontend**: HTML5, Vanilla CSS, Bootstrap 5, Chart.js
- **Containerization**: Docker & Docker Compose
- **Data Processing**: Pandas / Openpyxl (Excel Integration)

## 📦 Setup & Installation

### Prerequisites
- Docker and Docker Compose installed.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/dinkeinfo-netizen/manutencao-gds.git
   cd manutencao-gds
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory (refer to `.env.example` if available) with the following variables:
   - `SECRET_KEY`: A secure random string for Flask sessions.
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: For email integration.

3. **Spin up the containers**:
   ```bash
   docker-compose up -d --build
   ```

4. **Access the Application**:
   The system will be available at `http://localhost:5001`.

## 🗄 Database Structure

The system uses SQLAlchemy for ORM. Main models include:
- **Mecanico**: Staff management.
- **Equipamento**: Machine and asset inventory.
- **Localizacao**: Physical site management.
- **OrdemServico**: Centralized maintenance logs, including logs for materials, photos, and signatures.
- **User**: Authentication and authorization.

## 📄 Documentation

Developed and maintained by **DINKE**. Reference: **RQ MAN – 073 01**.
