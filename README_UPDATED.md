# CCPM Task Management Tool

A personal task management tool based on Critical Chain Project Management (CCPM) principles.

## Overview

This application helps manage tasks, track progress, and handle buffers according to CCPM methodology. It provides project management, task tracking, time management, and CCPM-specific buffer management features.

## Features

- Task management (create, edit, delete)
- Time tracking
- CCPM management (critical chain visualization, buffer consumption)
- Buffer management system
- Task estimation system
- Task dependency management
- Multi-tasking prevention
- Progress tracking
- Notification API system

## Implementation

The project is implemented using:

- **Backend**: Python with SQLAlchemy for database management
- **Frontend**: Taipy for the web interface
- **Database**: SQLite for data storage

## Project Structure

```
ccmp_test_2/
├── README.md
├── requirements.txt
├── src/
│   ├── app.py                  # Main application entry point
│   ├── models/                 # Database models
│   │   ├── base.py             # Base database configuration
│   │   ├── task.py             # Task model
│   │   ├── project.py          # Project model
│   │   ├── feeding_buffer.py   # Feeding buffer model
│   │   ├── time_entry.py       # Time entry model
│   │   ├── notification.py     # Notification model
│   │   └── ...
│   ├── controllers/            # Business logic
│   │   ├── task_controller.py  # Task operations
│   │   ├── project_controller.py # Project operations
│   │   └── ...
│   ├── views/                  # UI views
│   │   ├── dashboard.py        # Dashboard view
│   │   ├── tasks.py            # Tasks view
│   │   └── ...
│   ├── utils/                  # Utility functions
│   │   ├── buffer_calculator.py # Buffer calculations
│   │   ├── critical_chain.py   # Critical chain algorithms
│   │   └── ...
│   ├── database/               # Database initialization
│   │   └── init_db.py          # Database setup
│   └── api/                    # API endpoints
│       └── api_routes.py       # API routes
└── simple.py                   # Simple demonstration app
```

## CCPM Concepts Implemented

1. **50% Probability Estimates**: Tasks are estimated with 50% probability of completion (without safety margins).

2. **Project Buffer**: A buffer at the end of the project to protect the overall timeline.

3. **Buffer Consumption Tracking**: Monitoring how much of the buffer is being consumed.

4. **Buffer Status Visualization**: Green (0-33%), Yellow (34-66%), Red (67-100%) status indicators.

5. **Critical Chain Identification**: Identifying the sequence of dependent tasks that determines the project duration.

6. **Feeding Buffers**: Buffers where non-critical paths merge with the critical chain.

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python simple.py
   ```

## Demo Application

The `simple.py` file provides a simple demonstration of CCPM concepts:

- Task management with start and complete actions
- Buffer consumption calculation
- Buffer status visualization
- Project status tracking

## Future Enhancements

- Enhanced critical chain visualization
- Multiple project support
- Resource leveling
- Advanced reporting
- Mobile application

## License

[MIT License](LICENSE)