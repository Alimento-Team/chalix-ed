"""
Configuration settings for Facial Expression Recording feature.

Add these settings to your LMS configuration file (e.g., production.py or lms.env.json)
"""

# ===========================
# MinIO/S3 Storage Configuration for Facial Expression Videos
# ===========================

# Storage backend class (use S3Boto3Storage for MinIO compatibility)
FACIAL_EXPRESSION_STORAGE_CLASS = 'storages.backends.s3boto3.S3Boto3Storage'

# MinIO bucket name for storing facial expression videos
FACIAL_EXPRESSION_STORAGE_BUCKET = 'facial-expressions'

# Root directory within the bucket
FACIAL_EXPRESSION_STORAGE_ROOT = 'facial_expressions/'

# MinIO access credentials
FACIAL_EXPRESSION_STORAGE_ACCESS_KEY = 'your-minio-access-key-here'
FACIAL_EXPRESSION_STORAGE_SECRET_KEY = 'your-minio-secret-key-here'

# MinIO endpoint URL (without trailing slash)
# For local development: 'http://localhost:9000'
# For production: 'https://minio.yourdomain.com'
FACIAL_EXPRESSION_STORAGE_ENDPOINT = 'http://minio:9000'

# Optional: Region name (can be empty for MinIO)
FACIAL_EXPRESSION_STORAGE_REGION = 'us-east-1'

# Optional: Custom domain for serving files (if using CDN)
# FACIAL_EXPRESSION_STORAGE_CUSTOM_DOMAIN = 'cdn.yourdomain.com'

# Optional: Maximum file size per chunk (in bytes, default: 100MB)
FACIAL_EXPRESSION_MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# Optional: Enable/disable facial expression recording globally
ENABLE_FACIAL_EXPRESSION_RECORDING = True

# Optional: Courses where facial expression recording is enabled
# If empty, enabled for all courses
FACIAL_EXPRESSION_ENABLED_COURSES = [
    # 'course-v1:Org+Course+Run',
]

# Optional: Automatic cleanup after X days (0 = never cleanup)
FACIAL_EXPRESSION_RETENTION_DAYS = 90

# ===========================
# Example lms.env.json format
# ===========================
"""
{
  "FACIAL_EXPRESSION_STORAGE_CLASS": "storages.backends.s3boto3.S3Boto3Storage",
  "FACIAL_EXPRESSION_STORAGE_BUCKET": "facial-expressions",
  "FACIAL_EXPRESSION_STORAGE_ROOT": "facial_expressions/",
  "FACIAL_EXPRESSION_STORAGE_ACCESS_KEY": "minioadmin",
  "FACIAL_EXPRESSION_STORAGE_SECRET_KEY": "minioadmin",
  "FACIAL_EXPRESSION_STORAGE_ENDPOINT": "http://minio:9000",
  "FACIAL_EXPRESSION_STORAGE_REGION": "us-east-1",
  "ENABLE_FACIAL_EXPRESSION_RECORDING": true,
  "FACIAL_EXPRESSION_RETENTION_DAYS": 90
}
"""

# ===========================
# MinIO Server Configuration
# ===========================
"""
If you're setting up MinIO from scratch:

1. Install MinIO:
   docker run -p 9000:9000 -p 9001:9001 \
     --name minio \
     -e "MINIO_ROOT_USER=minioadmin" \
     -e "MINIO_ROOT_PASSWORD=minioadmin" \
     -v /data:/data \
     minio/minio server /data --console-address ":9001"

2. Create bucket:
   - Access MinIO console at http://localhost:9001
   - Login with credentials
   - Create new bucket named "facial-expressions"
   - Set appropriate access policies

3. Create access keys:
   - Go to Access Keys in MinIO console
   - Create new access key
   - Use the generated key and secret in your configuration
"""

# ===========================
# Django Settings
# ===========================
"""
Make sure to add the app to INSTALLED_APPS:

INSTALLED_APPS = [
    # ... other apps
    'lms.djangoapps.facial_expression',
    'lms.djangoapps.learning_analytics',
    # ... other apps
]
"""

# ===========================
# CORS Settings (if MFE is on different domain)
# ===========================
"""
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:2000',  # frontend-app-learning dev server
    'https://learning.yourdomain.com',  # production MFE
]
"""
