# TaskManPRO

A modern task management application built with Flask and SQLite.

## Features

- Create, update, and delete tasks
- Track task progress and time spent
- Filter tasks by priority, status, and search terms
- Real-time task statistics
- Task timer functionality
- Modern, responsive UI

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Project Structure

- `app.py`: Main Flask application
- `templates/index.html`: Frontend template
- `task_manager.db`: SQLite database (created automatically)
- `requirements.txt`: Python dependencies

## Development

The application uses:
- Flask for the backend
- SQLite for the database
- Bootstrap 5 for the frontend
- Font Awesome for icons

## License

MIT License 