# PDF to Image Conversion API

This FastAPI application provides services to upload PDF files, convert them to high-quality images, and upload the resulting images to AWS S3 storage.

## Features

- Upload PDF files individually or in batches
- Convert PDFs to images (300 DPI JPG format)
- Background task processing for large batches
- Status tracking for both conversion and S3 upload processes
- Automatic cleanup of local files after processing
- AWS S3 integration for cloud storage

## Requirements

- Python 3.8+
- FastAPI
- pdf2image
- Poppler utilities
- boto3 (AWS SDK)
- Additional dependencies listed in `requirements.txt`

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Poppler utilities (required for PDF to image conversion):
   - **Windows**: Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
     - Extract to a directory (e.g., `C:\poppler`)
     - Add the bin directory to system PATH or update `POPPLER_PATH` in the code
   - **Linux**: `apt-get install poppler-utils`
   - **macOS**: `brew install poppler`

3. Create `.env` file with the following variables:
   ```
   AWS_ACCESS_KEY=your_aws_access_key
   AWS_SECRET_KEY=your_aws_secret_key
   S3_BUCKET_NAME=your_s3_bucket_name
   Upload_folder_path=./uploads
   Images_folder_path=./images
   ```

4. Create the necessary directories:
   ```bash
   mkdir uploads
   mkdir images
   ```

## Running the API

### Development

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Production (IIS on Windows)

1. Set up a virtual environment and install dependencies
2. Install the required Windows features for IIS and Python hosting
3. Configure the application in IIS using the provided `web.config`
4. Ensure Poppler is installed and accessible in the PATH

## API Endpoints

### Health Checks

- **GET /health**: Simple health check endpoint
- **GET /test-connection**: Detailed server and environment information

### File Operations

- **POST /upload-files/**: Upload PDF files to the server
  - Accepts multiple files
  - Returns filenames of uploaded files

- **POST /convert-pdfs/**: Convert uploaded PDFs to images
  - Parameter: `folder_path` (optional subfolder)
  - Returns task ID for status tracking

### Status Tracking

- **GET /conversion-status/{task_id}**: Check PDF to image conversion status
  - Returns progress information and status

- **GET /s3-upload-status/{task_id}**: Check S3 upload status
  - Returns upload progress information and status

## Workflow

1. Upload PDF files using the `/upload-files/` endpoint
2. Start the conversion process with `/convert-pdfs/`
3. Monitor conversion status using the task ID
4. Once complete, images are uploaded to S3
5. Local files are automatically cleaned up

## Folder Structure

- `uploads/`: Temporary storage for uploaded PDF files
- `images/`: Temporary storage for converted images before S3 upload

## Troubleshooting

- Ensure Poppler is correctly installed and accessible in PATH
- Check logs for specific error messages
- Verify AWS credentials are correct
- Ensure IIS has appropriate permissions to access directories and execute commands