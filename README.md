# Medical Device Management Software (MDMS)

A comprehensive solution for managing medical devices in healthcare facilities.

## Features

- Real-time device monitoring and control
- Maintenance scheduling and tracking
- Spare parts inventory management
- Usage history tracking
- Automated backup system
- Multi-language support (Vietnamese and English)
- Role-based access control
- Comprehensive reporting system

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12.0 or higher (for production)
- SQLite (for development/testing)

## Installation

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DVT.git
cd DVT
```

2. Create and activate a virtual environment:
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

### Automated Installation

Run the installation script:
```bash
# Linux/macOS
sudo python3 install.py

# Windows (Run as Administrator)
python install.py
```

## Configuration

1. Copy the example configuration:
```bash
cp config/settings.example.json config/settings.json
```

2. Edit the configuration file:
- Database settings
- Backup locations
- Language preferences
- Security settings

## Running the Application

1. Start the application:
```bash
# If installed via pip
dvt

# Or run directly
python -m src.gui.main_window
```

2. Log in with default credentials:
- Username: admin
- Password: Admin123!

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@cdsl.com or open an issue in the GitHub repository.