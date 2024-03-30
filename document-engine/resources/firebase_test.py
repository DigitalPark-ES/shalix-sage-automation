import os
import shutil
import sys
import re
import sqlite3
import time
from PyPDF2 import PdfReader, PdfWriter
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore, storage


bucket_name = 'shalix-automation-dev.appspot.com'

# PENDING | MERGED | READY | FAILED | UPLOADED | UPLOAD_FAILED

## Firebase Config
cred_path = os.path.join(os.getcwd(), 'resources', 'fb.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': bucket_name
})


db = firestore.client()
doc_ref = db.collection('dococo')

doc_ref.add({
    "name": "Erikson"
})

print("OK")