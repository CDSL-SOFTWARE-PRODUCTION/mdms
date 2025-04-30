# Medical Device Management Software (MDMS)
## Project Documentation

### Phase 1: Foundation and Setup (Week 1-2)

#### 1. Technology Stack Selection ✓
- **GUI Framework**: PyQt6
  - Chosen for robust features and cross-platform support
  - Touch screen compatibility
  - Modern widget support
- **Database**: 
  - Primary: PostgreSQL (Production)
  - Development: SQLite (Testing/Development)
  - ORM: SQLAlchemy

#### 2. Project Structure Setup ✓
```
DVT/
├── config/           # Configuration files
├── docs/            # Documentation
├── scripts/         # Utility scripts
├── src/             # Source code
│   ├── business_logic/      # Business layer
│   ├── database/           # Data access layer
│   ├── device_communication/ # Device interface layer
│   ├── gui/               # Presentation layer
├── tasks/           # Project tasks
└── tests/           # Test suites
```

#### 3. Database Schema Design ✓
#### 4. Core Architecture Interfaces ✓

##### 4.1 Database Layer
- **BaseDevice Interface**
  - Core device communication protocol
  - Connection management (Serial, USB, Ethernet)
  - Status monitoring
  - Parameter get/set operations
  - Error handling

##### 4.2 Device Communication Layer
- **Base Device Protocol**
  - Abstract communication methods
  - Connection state management
  - Data validation
  - Error handling
  - Real-time monitoring capabilities

##### 4.3 Business Logic Layer
- **Device Service**
  - Device registration and management
  - Status monitoring
  - Usage tracking
  - Maintenance scheduling
  - Alert management

##### 4.4 GUI Layer
- **Base Window Interface**
  - Common window properties
  - Navigation controls
  - Status display
  - Error message handling
  - Theme management

### Phase 2: Core Module Implementation (Week 3-6)

Database Layer Implementation:
Implement database connection logic.
Implement Data Access Objects (DAOs) or Repository patterns for each table, providing CRUD (Create, Read, Update, Delete) operations. Use an ORM like SQLAlchemy if desired.
User Management Module:
Business Logic: Implement user registration, login (with password hashing), session management, basic role checking, and activity logging logic.
GUI: Create login screen, and potentially a basic user management screen (for admins).
Basic Device Management Module:
Business Logic: Implement logic for adding, viewing, updating device details, assigning groups, and changing status.
GUI: Create screens/widgets for listing devices (table view), viewing/editing device details (form view), searching/filtering devices.

Abstract Device Communication Layer:
Implement the BaseDeviceCommunicator interface.
Develop initial, generic handlers for connection types (Serial, USB, TCP/IP) - these might just log actions initially without real hardware interaction.
Phase 3: Feature Expansion (Week 7-12)

Device Control & Monitoring Module:
Business Logic: Design logic to handle sending commands and receiving/parsing real-time data. Implement alert condition checking.
Device Communication: Implement specific communication logic for one sample device type (e.g., a simulated temperature sensor via Serial/USB).
GUI: Develop dashboard elements to display real-time data, controls (buttons, sliders) to send commands, and an alert display area.

Usage History Module:
Business Logic: Implement logic to start/stop usage tracking and calculate durations.
Database: Ensure usage_history table is populated correctly.
GUI: Create a screen to view usage history, filterable by device and date range.
Maintenance Module:
Business Logic: Implement logic for scheduling, recording maintenance, tracking spare parts, generating reminders (based on next_maintenance_due or warranty expiry).
Database: Ensure maintenance tables are populated.
GUI: Create screens for managing maintenance schedules, logging activities, viewing inventory, and displaying upcoming maintenance/warranty alerts.
Reporting Module:
Business Logic: Develop functions to query data and aggregate statistics for required reports (status, usage, cost, incidents).
GUI: Create a reporting section allowing users to select report types, date ranges, and view/export the results (e.g., to CSV or PDF).

Phase 4: Device-Specific Modules & Integration (Week 13-16)

Implement Specialized Device Modules:
For each device type in Điều 6 (Đèn mổ, Máy soi, etc.):
Create specific subclasses inheriting from BaseDeviceCommunicator.
Implement the unique communication protocols and command sets.
Add specific logic to the Business Logic layer if needed.
Adapt or add specialized widgets/controls to the GUI for unique functions (e.g., light intensity control, image display area).
Integrate All Modules: Ensure seamless data flow and interaction between GUI, Business Logic, Device Communication, and Database layers.
Phase 5: Testing & Non-Functional Requirements (Week 17-20)

Unit & Integration Testing: Write and run tests for individual functions (unit tests) and interactions between components (integration tests).
System Testing: Perform end-to-end testing based on user scenarios covering all functional requirements.

Performance Testing: Measure response times under simulated load, optimize database queries and GUI rendering (< 2s goal).
Security Implementation & Testing: Implement data encryption (e.g., for sensitive fields), finalize role-based access controls, conduct basic security checks.
Reliability: Implement robust error handling, logging, and test backup/restore procedures.
Cross-Platform Testing: Test thoroughly on Windows, Linux, and macOS target environments.
Usability Testing: Gather feedback on GUI clarity, ease of use, language correctness, and touch screen interaction. Refine GUI based on feedback.
Phase 6: Documentation & Deployment (Week 21-22)

Documentation:
Write User Manual (installation, usage guide, troubleshooting).
Write Technical Documentation (architecture overview, setup instructions, API details, database schema).

Packaging: Create installers/packages suitable for deployment on Windows, Linux, and macOS (using tools like PyInstaller, cx_Freeze, etc.).
Final Review & Release Candidate: Conduct final testing and prepare for release.