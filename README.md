# PDF to Image Conversion Solution

A complete solution for converting PDF files to high-quality images and storing them in AWS S3, featuring a React frontend and FastAPI backend deployed on Windows IIS.

## Project Structure

This project consists of two main components:

1. **Frontend Application** (`/frontend_app/`)
   - React-based user interface
   - Provides file upload and conversion monitoring
   - Deployed at: `your-url`

2. **Backend API** (`/API/`)
   - FastAPI-based service for PDF processing
   - Handles PDF to image conversion using Poppler
   - Manages AWS S3 uploads
   - Deployed at: `your-url`

## Key Features

- Upload multiple PDF files through a user-friendly interface
- Convert PDFs to high-quality (300 DPI) images
- Background processing for large batches
- Real-time conversion and upload status tracking
- Secure storage in AWS S3
- Automatic cleanup of local files after processing

## Deployment Architecture

- **Web Server**: Windows IIS 
- **Frontend**: Static files served by IIS with URL rewriting
- **Backend**: Python FastAPI running under IIS with FastCGI
- **Storage**: AWS S3 for long-term image storage

## Requirements

### Frontend
- Node.js 16+
- npm or yarn

### Backend
- Python 3.8+
- FastAPI
- Poppler utilities
- AWS credentials for S3 access

## Setup Instructions

Detailed setup instructions are available in the README files within each component directory:

- [Frontend Setup](/frontend_app/README.md)
- [Backend Setup](/API/README.md)

## Troubleshooting

Common issues and their solutions:

- **PDF Conversion Fails**: Ensure Poppler is installed and in PATH
- **API Connection Issues**: Check the API endpoint configuration in frontend
- **S3 Upload Fails**: Verify AWS credentials are correct

See component-specific READMEs for more detailed troubleshooting information. 