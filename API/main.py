from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Annotated
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import logging
from dotenv import load_dotenv
import pathlib
from pdf2image import convert_from_path 
import glob
import uuid
import boto3
from datetime import datetime
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = os.getenv("Upload_folder_path", "./uploads")
IMAGES_DIR = os.getenv("Images_folder_path", "./images")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

conversion_status = {}
s3_upload_status = {}

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )

def get_date_prefix():
    now = datetime.now()
    month_name = now.strftime("%b") 
    date_format = now.strftime("%y%m%d") 
    
    return f"{now.year}/{month_name}/{date_format}"

@app.post("/upload-files/")
async def create_upload_files(files: list[UploadFile]):
    try:
        logger.info(f"Received upload request with {len(files)} files")
        file_paths = []
        for file in files:
            filename = file.filename.replace("\\", "/")
            file_path = os.path.join(UPLOAD_DIR, filename)
            directory = os.path.dirname(file_path)
            logger.info(f"Creating directory if needed: {directory}")
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Saving file: {filename}")
            try:
                with open(file_path, "wb") as buffer:
                    contents = await file.read()
                    buffer.write(contents)
                file_paths.append(file_path)
                logger.info(f"Successfully saved: {filename}")
            except Exception as e:
                logger.error(f"Error saving file {filename}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save file {filename}: {str(e)}")
        
        return {"filenames": [file.filename for file in files]}
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/convert-pdfs/")
async def convert_pdfs(background_tasks: BackgroundTasks, folder_path: str = ""):
    try:
        source_dir = os.path.join(UPLOAD_DIR, folder_path)
        if not os.path.exists(source_dir):
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
        
        pdf_files = []
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    rel_path = os.path.relpath(root, UPLOAD_DIR)
                    pdf_files.append(os.path.join(rel_path, file))
        
        if not pdf_files:
            return {"message": "No PDF files found to convert"}
        
        task_id = str(uuid.uuid4())
        conversion_status[task_id] = {
            "total": len(pdf_files),
            "converted": 0,
            "failed": 0,
            "status": "processing"
        }
        
        background_tasks.add_task(
            convert_pdf_files_to_images, 
            pdf_files, 
            task_id
        )
        
        return {"task_id": task_id, "total_files": len(pdf_files)}
        
    except Exception as e:
        logger.error(f"Error setting up conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversion-status/{task_id}")
async def get_conversion_status(task_id: str):
    if task_id not in conversion_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return conversion_status[task_id]

@app.get("/s3-upload-status/{task_id}")
async def get_s3_upload_status(task_id: str):
    if task_id not in s3_upload_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return s3_upload_status[task_id]

def convert_pdf_files_to_images(pdf_files, task_id):
    for pdf_file in pdf_files:
        try:
            pdf_path = os.path.join(UPLOAD_DIR, pdf_file)
            pdf_name = os.path.basename(pdf_file).rsplit('.', 1)[0]
            file_guid = str(uuid.uuid4())
            
            output_dir = os.path.join(IMAGES_DIR, file_guid, pdf_name)
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Converting PDF to: {output_dir}")
            
            try:
                pages = convert_from_path(pdf_path, 300)
                
                for i, page in enumerate(pages):
                    image_path = os.path.join(output_dir, f"page_{i+1}.jpg")
                    logger.info(f"Saving image to: {image_path}")
                    page.save(image_path, "JPEG")
                
                conversion_status[task_id]["converted"] += 1
                logger.info(f"Successfully converted: {pdf_file} to {output_dir}")
                
            except Exception as e:
                logger.error(f"Error during PDF conversion: {str(e)}")
                conversion_status[task_id]["failed"] += 1
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")
            conversion_status[task_id]["failed"] += 1
    
    conversion_status[task_id]["status"] = "completed"
    logger.info(f"Conversion task {task_id} completed")
    
    upload_to_s3_and_cleanup(task_id)

def upload_to_s3_and_cleanup(task_id):
    try:
        s3_upload_status[task_id] = {
            "total": 0,
            "uploaded": 0,
            "failed": 0,
            "status": "processing"
        }
        
        s3_client = get_s3_client()
        date_prefix = get_date_prefix()
        
        total_files = 0
        s3_upload_tasks = []
        
        logger.info(f"Checking files in {IMAGES_DIR}")
        
        for root, _, files in os.walk(IMAGES_DIR):
            for file in files:
                if file.lower().endswith('.jpg'):
                    total_files += 1
                    local_path = os.path.join(root, file)                
                    rel_path = os.path.relpath(root, IMAGES_DIR)
                    rel_path = rel_path.replace('\\', '/')
                    parts = rel_path.split('/')
                    
                    logger.info(f"File: {local_path}, Parts: {parts}")
                    
                    guid = parts[0] if len(parts) > 0 else "unknown"
                    filename = parts[1] if len(parts) > 1 else "unknown"
                    
                    s3_key = f"test/{date_prefix}/{guid}/{filename}/{file}"
                    logger.info(f"Will upload to S3 as: {s3_key}")
                    
                    s3_upload_tasks.append((local_path, s3_key))
        
        logger.info(f"Found {total_files} files to upload")
        s3_upload_status[task_id]["total"] = total_files
        
        if total_files == 0:
            logger.warning("No files found to upload!")
            s3_upload_status[task_id]["status"] = "completed"
            cleanup_local_directories()
            return
        
        for local_path, s3_key in s3_upload_tasks:
            try:
                logger.info(f"Uploading {local_path} to S3 bucket {S3_BUCKET_NAME}, key: {s3_key}")
                s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_key)
                s3_upload_status[task_id]["uploaded"] += 1
                logger.info(f"Successfully uploaded to S3: {s3_key}")
            except Exception as e:
                logger.error(f"Error uploading {local_path} to S3: {str(e)}")
                s3_upload_status[task_id]["failed"] += 1
        
        s3_upload_status[task_id]["status"] = "completed"
        logger.info(f"S3 upload task {task_id} completed")
        
        cleanup_local_directories()
        
    except Exception as e:
        logger.error(f"Error in S3 upload process: {str(e)}")
        if task_id in s3_upload_status:
            s3_upload_status[task_id]["status"] = "failed"

def cleanup_local_directories():
    try:
        logger.info("Cleaning up uploads directory")
        for item in os.listdir(UPLOAD_DIR):
            item_path = os.path.join(UPLOAD_DIR, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        logger.info("Cleaning up images directory")
        for item in os.listdir(IMAGES_DIR):
            item_path = os.path.join(IMAGES_DIR, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                
        logger.info("Successfully cleaned up local directories")
    except Exception as e:
        logger.error(f"Error cleaning up local directories: {str(e)}")