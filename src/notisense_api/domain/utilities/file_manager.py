import imghdr
import os

import base64
import io
import uuid

import boto3
from decouple import config
from fastapi import APIRouter, HTTPException

# Initialize Boto3 S3 Client
s3_client = boto3.client(
    "s3",
    region_name=config("AWS__REGION"),
    aws_access_key_id=config("AWS__ACCESS_KEY"),
    aws_secret_access_key=config("AWS__SECRET_KEY"),
)
AWS_BUCKET_NAME = config("AWS__BUCKET_NAME")
AWS_REGION = config("AWS__REGION")

def save_file(filename: str, content: bytes, upload_dir: str = "uploads") -> str:
    os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as file:
        file.write(content)
    return file_path


async def upload_to_s3(image_base64: str):
    try:
        # Decode Base64 string
        base64_data = clean_base64(image_base64)
        image_data = base64.b64decode(base64_data)
        image_stream = io.BytesIO(image_data)

        # Detect file format
        file_format = imghdr.what(None, h=image_data)

        if file_format not in ["jpeg", "png", "gif", "bmp", "webp"]:
            raise HTTPException(status_code=400, detail="Unsupported image format")

        # Ensure correct file extension
        file_extension = "jpg" if file_format == "jpeg" else file_format
        file_name = f"{uuid.uuid4()}.{file_extension}"

        # Upload to S3
        s3_client.upload_fileobj(
            image_stream,
            AWS_BUCKET_NAME,
            file_name,
            ExtraArgs={"ContentType": f"image/{file_extension}"},
        )

        # Generate S3 URL
        s3_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

        return s3_url

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")


def clean_base64(data: str) -> str:
    """Splits the string by ',' and returns the Base64 part if a prefix exists."""
    parts = data.split(",", 1)  # Split only at the first comma
    return parts[1] if len(parts) > 1 else parts[0]  # Return Base64 part if prefix exists
