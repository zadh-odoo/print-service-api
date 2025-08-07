# Print Service API

A FastAPI-based web service for printing images from base64 data. This service accepts base64-encoded images via HTTP POST requests and sends them to the system's default printer.

## Features

- FastAPI web server with CORS support
- Accepts base64-encoded images
- Cross-platform printing support (Windows/Linux)
- Can be compiled to standalone executable using PyInstaller
- Configurable port via command line argument

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- PyInstaller (for building executables)

## Installation

1. Install required packages:
```bash
pip install fastapi uvicorn pyinstaller
```

2. Run the application:
```bash
python main.py --port=5050
```

## API Usage

### Print Endpoint

**POST** `/print`

Send a base64-encoded image to be printed.

#### Request Body
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..."
}
```

#### Response
```json
{
  "message": "Printed successfully"
}
```

## Building Executable

To create a standalone executable:

```bash
pyinstaller --onefile main.py
```

The executable will be created in the `dist/` folder.

### Running the Executable

```bash
# Linux
./dist/main --port=5050

# Windows
dist\main.exe --port=5050
```

## CORS Configuration

The service is configured to accept requests from `http://localhost:8069`. To modify this, update the `allow_origins` list in the CORS middleware configuration.

## Platform Support

- **Linux**: Uses `xdg-open` to open files with the default application
- **Windows**: Uses `cmd /c start /min "" /print` to print files directly

## License

MIT License
