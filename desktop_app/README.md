# Chemical Equipment Parameter Visualizer - Desktop Application

PyQt5-based desktop client for the Chemical Equipment Parameter Visualizer system. Provides a native Windows/Linux/Mac application interface to the Django backend.

## 🎯 Features

- **JWT Authentication** - Secure login with token persistence
- **CSV Upload & Analysis** - Drag-and-drop dataset processing
- **Real-time Visualization** - Matplotlib charts matching web app design
- **Export Functionality** - Download CSV and PDF reports
- **History Management** - View and analyze last 5 datasets
- **Async Operations** - QThread workers for responsive UI
- **React Design Matching** - Identical color palette and styling

## 🏗️ Architecture

```
desktop_app/
├── main.py                 # Application entry point
├── api.py                  # REST API client (backend communication)
├── auth.py                 # JWT token management
├── ui/
│   ├── __init__.py
│   ├── login.py           # Login/Register dialog
│   └── dashboard.py       # Main dashboard window (MVC pattern)
├── charts/
│   ├── __init__.py
│   └── plots.py           # Matplotlib chart widgets
└── requirements.txt       # Python dependencies
```

### MVC Pattern Implementation

- **Model**: `api.py` handles data fetching and backend communication
- **View**: `ui/dashboard.py` UI components with QSS styling
- **Controller**: QThread workers for async operations, signal/slot connections

## 📋 Prerequisites

- Python 3.8 or higher
- Django backend running on `http://localhost:8002`
- Virtual environment (recommended)

## 🚀 Installation

### 1. Create Virtual Environment (if not exists)

```bash
# From project root (app/)
cd desktop_app

# Create venv
python -m venv .venv

# Activate
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt includes:**
- PyQt5 >= 5.15.0 (GUI framework)
- requests >= 2.31.0 (HTTP client)
- matplotlib >= 3.7.0 (Charts)
- pandas >= 2.0.0 (Data processing)

### 3. Verify Backend is Running

Ensure Django backend is operational:

```bash
# From app/django_backend/
python manage.py runserver 8002
```

Test endpoint:
```bash
curl http://localhost:8002/api/history/
```

## 🎮 Running the Application

### Method 1: Using main.py (Recommended)

```bash
cd desktop_app
python main.py
```

### Method 2: Direct Python execution

```bash
python -m desktop_app.main
```

## 🔐 First Time Usage

1. **Register Account**
   - Launch application
   - Click "Register" tab
   - Enter username and password
   - Click "Register"

2. **Login**
   - Enter credentials
   - Click "Login"
   - Token cached in `.token_cache.json` (auto-login next time)

3. **Upload Dataset**
   - Click "Select CSV File"
   - Choose a CSV file with columns: `Equipment_ID`, `Equipment_Type`, `Flowrate_m3_h`, `Pressure_bar`, `Temperature_C`
   - Click "Upload & Analyze"
   - Wait for processing

4. **View Analysis**
   - Summary cards show statistics
   - Charts display (coming soon - integration pending)
   - History section lists last 5 uploads

5. **Export Data**
   - Click "Export CSV" or "Export PDF" in header
   - Or click CSV/PDF buttons on history cards
   - Choose save location

## 🎨 Color Palette (React Matching)

```python
PRIMARY_CYAN = "#4FC3F7"      # Buttons, accents
SUCCESS_GREEN = "#66BB6A"     # Upload button
WARNING_ORANGE = "#FFA726"    # Chart colors
DANGER_RED = "#EF5350"        # Logout button
BACKGROUND_DARK = "#1E293B"   # Main background
TEXT_PRIMARY = "#E0E0E0"      # Main text
TEXT_MUTED = "#90A4AE"        # Labels, subtitles
```

## ⚙️ Configuration

### API Base URL

Default: `http://localhost:8002`

To change, edit `api.py`:

```python
class APIClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
```

### Token Storage Location

Tokens stored in: `desktop_app/.token_cache.json`

Format:
```json
{
    "username": "your_username",
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
}
```

**Security Note**: This file contains sensitive tokens. Do not commit to version control.

## 🧵 Performance Features

### QThread Workers

All network operations run in background threads:

- **HistoryLoaderThread**: Fetches upload history (non-blocking)
- **DatasetLoaderThread**: Loads dataset summaries
- **UploadThread**: Handles CSV upload with progress bar
- **ExportThread**: Downloads CSV/PDF files

Benefits:
- UI remains responsive during API calls
- Progress indicators for long operations
- Error handling per operation
- Automatic thread cleanup on window close

### Usage Example

```python
# Dashboard internally handles threading
def load_history(self):
    thread = HistoryLoaderThread(self.api_client)
    thread.finished.connect(self.on_history_loaded)
    thread.error.connect(self.on_error)
    thread.start()
```

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Ensure you're in the virtual environment:
```bash
# Check active environment
which python  # Linux/Mac
where python  # Windows

# Should show .venv path
```

### Issue: "Connection refused" when logging in

**Solution**: Start Django backend:
```bash
cd django_backend
python manage.py runserver 8002
```

### Issue: Login dialog closes immediately

**Solution**: Check API URL in `api.py`. Ensure backend is accessible.

### Issue: Charts not displaying

**Solution**: This is expected in current version. Chart integration with dashboard coming soon. For now, summary cards and history work fully.

### Issue: "Invalid token" error

**Solution**: Delete `.token_cache.json` and login again:
```bash
rm .token_cache.json  # Linux/Mac
del .token_cache.json  # Windows
```

## 🔄 Development Workflow

### Adding New Features

1. **API Endpoints**: Update `api.py` with new methods
2. **UI Components**: Add widgets to `ui/dashboard.py`
3. **Async Operations**: Create QThread workers
4. **Styling**: Update QSS stylesheet in `apply_styling()`

### Example: Adding a new API call

```python
# 1. Add to api.py
def get_dataset_details(self, dataset_id):
    response = requests.get(
        f"{self.base_url}/api/dataset/{dataset_id}/",
        headers=self._get_headers()
    )
    return self._handle_response(response)

# 2. Create worker thread (dashboard.py)
class DatasetDetailThread(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, api_client, dataset_id):
        super().__init__()
        self.api_client = api_client
        self.dataset_id = dataset_id
    
    def run(self):
        result = self.api_client.get_dataset_details(self.dataset_id)
        self.finished.emit(result.get("data", {}))

# 3. Use in dashboard
def load_details(self, dataset_id):
    thread = DatasetDetailThread(self.api_client, dataset_id)
    thread.finished.connect(self.on_details_loaded)
    thread.start()
```

## 📊 Comparison: Web vs Desktop

| Feature | React Web App | PyQt5 Desktop App |
|---------|---------------|-------------------|
| **Framework** | React.js + Chart.js | PyQt5 + Matplotlib |
| **HTTP Client** | Axios | Requests |
| **State Management** | useState hooks | Instance variables |
| **Authentication** | localStorage | .token_cache.json |
| **Charts** | Chart.js (Canvas) | Matplotlib (FigureCanvas) |
| **Styling** | CSS + Tailwind | QSS (Qt Style Sheets) |
| **Backend** | Same Django API | Same Django API |
| **Color Palette** | Identical | Identical |

**Key Advantage**: Both frontends share the same backend, ensuring consistency and avoiding data duplication.

## 🚀 Future Enhancements

- [ ] **Chart Integration**: Embed Matplotlib charts in dashboard
- [ ] **Auto-refresh**: Periodic history updates
- [ ] **Desktop PDF Preview**: Built-in PDF viewer
- [ ] **Dark Mode Toggle**: Switch between themes
- [ ] **Dataset Search**: Filter history by name/date
- [ ] **Drag & Drop Upload**: Direct file drop support
- [ ] **System Tray Icon**: Minimize to tray
- [ ] **Notifications**: Desktop alerts for completed operations

## 📝 License

Part of the Chemical Equipment Parameter Visualizer project.

## 🤝 Contributing

1. Follow MVC pattern for new features
2. Use QThread for any network/long operations
3. Match React color palette in QSS styling
4. Add docstrings to all classes/methods
5. Test on both Windows and Linux

## 📞 Support

For issues:
1. Check backend is running: `curl http://localhost:8002/api/history/`
2. Verify dependencies: `pip list`
3. Check logs in terminal
4. Delete `.token_cache.json` and re-login

---

**Architecture Note**: This desktop app follows industry-standard practices:
- **Separation of Concerns**: API, Auth, UI, Charts in separate modules
- **Async Operations**: QThread workers prevent UI blocking
- **Token Persistence**: Auto-login for better UX
- **Error Handling**: Try-except with user-friendly messages
- **Styling**: QSS matching web app for brand consistency

Built with ❤️ using PyQt5 and Python 3
