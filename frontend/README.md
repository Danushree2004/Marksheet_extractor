# Frontend for Marksheet Extraction API

A beautiful, modern web interface for the Marksheet Information Extraction API.

## 🎨 Features

- **Stunning UI**: Modern design with gradients, glassmorphism, and smooth animations
- **Drag & Drop**: Easy file upload with drag and drop support
- **Real-time Progress**: Visual progress tracking through extraction steps
- **Results Display**: Beautiful presentation of extracted data with confidence scores
- **JSON Viewer**: Collapsible JSON viewer with copy and download options
- **Responsive**: Works on desktop and mobile devices

## 🚀 How to Use

### 1. Make Sure the API is Running

The frontend needs the backend API to be running. Start it with:

```bash
cd ..
python main.py
```

The API should be running on `http://localhost:8000`

### 2. Open the Frontend

Simply open `index.html` in your browser:

- **Double-click** `index.html`, or
- **Right-click** → Open with → Your browser, or
- Use the command: `start index.html` (Windows)

### 3. Upload a Marksheet

1. **Drag and drop** a marksheet file (PDF, JPG, PNG) onto the upload area
2. Or **click** the upload area to browse for a file
3. Click **"Extract Data"**
4. Watch the progress as it processes
5. View the results with confidence scores!

## 📁 Files

- **`index.html`** - Main HTML structure
- **`styles.css`** - Premium CSS styling with animations
- **`script.js`** - JavaScript for API interaction and UI logic

## 🎯 Features Showcase

### Hero Section
- Eye-catching gradient text
- Key statistics display
- Smooth fade-in animations

### Upload Interface
- Drag and drop support
- File type validation
- File size validation (10MB max)
- Visual file preview

### Progress Tracking
- 4-step visual progress indicator
- Real-time status updates
- Smooth animations

### Results Display
- Candidate details card
- Academic details with subject-wise marks
- Confidence indicators (color-coded)
- Overall confidence badge

### JSON Viewer
- Syntax-highlighted JSON
- Copy to clipboard
- Download as file
- Collapsible view

## 🎨 Design Elements

- **Color Scheme**: Indigo/Purple gradient with dark theme
- **Typography**: Inter font family
- **Effects**: Glassmorphism, gradients, shadows
- **Animations**: Fade-in, slide-up, pulse effects
- **Icons**: Custom SVG icons

## 🔧 Technical Details

### API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`:

- **Health Check**: `GET /health`
- **Extract**: `POST /extract`

### CORS

The backend has CORS enabled to allow the frontend to make requests.

### File Validation

- **Allowed types**: PDF, JPG, JPEG, PNG
- **Max size**: 10MB
- **Client-side validation** before upload

## 🌟 User Experience

### Confidence Score Colors

- **Green (80-100%)**: High confidence
- **Yellow (50-79%)**: Medium confidence
- **Red (0-49%)**: Low confidence

### Smooth Interactions

- Hover effects on buttons and cards
- Smooth scroll to results
- Loading animations
- Success feedback

## 📱 Responsive Design

The frontend is fully responsive and works on:

- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🎓 Code Quality

- **Clean HTML**: Semantic structure
- **Modular CSS**: CSS variables for theming
- **Modern JavaScript**: ES6+ features
- **Comments**: Well-documented code

## 🚀 Future Enhancements

- [ ] Batch upload support
- [ ] History of extractions
- [ ] Dark/Light mode toggle
- [ ] Export to Excel/CSV
- [ ] Comparison view for multiple marksheets
- [ ] Advanced filtering and search

## 📄 License

Part of the Marksheet Information Extraction API project.

---

**Enjoy the beautiful UI! 🎉**
