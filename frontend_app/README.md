# PDF to Image Conversion Frontend

This React application provides a user-friendly interface for uploading PDF files, converting them to images, and storing them in AWS S3.

## Features

- Clean, modern user interface
- Folder/file selection for batch PDF uploads
- Real-time conversion progress tracking
- Integration with backend API for PDF processing
- Responsive design for desktop and mobile devices

## Requirements

- Node.js 16+
- npm or yarn
- Backend API service running (see API folder)

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create a production build:
   ```bash
   npm run build
   ```

## Development

Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## Configuration

The application is configured to connect to the backend API. The API endpoint is defined in `src/api.js`. 

For local development, it points to `http://localhost:8000`. For production, it uses relative paths that are proxied through IIS to the backend service.


## Application Structure

- `src/App.js`: Main application component
- `src/api.js`: API configuration and connection settings
- `src/App.css`: Styling for the application
- `public/`: Static assets and HTML template

## Integration with Backend

The frontend communicates with the backend API through the following endpoints:

- `GET /health`: Check if the backend is online
- `POST /upload-files/`: Upload PDF files
- `POST /convert-pdfs/`: Trigger PDF to image conversion
- `GET /conversion-status/{task_id}`: Track conversion progress

## Troubleshooting

- If API calls fail, check that the backend service is running
- Verify that the API endpoint in `src/api.js` is correctly configured
- For CORS issues, ensure the backend allows requests from the frontend domain
- Check browser developer console for JavaScript errors

## Browser Compatibility

The application is compatible with:
- Chrome 60+
- Firefox 60+
- Edge 79+
- Safari 12+