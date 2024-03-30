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

## Global variables ##################################################

workspace_path = os.path.join(os.getcwd(), 'workspace')
input_path = os.path.join(workspace_path, 'input')
output_s1_split_path = os.path.join(workspace_path, 'output_s1_split_path')
output_final_path = os.path.join(workspace_path, 'output_final_path')
log_path = os.path.join(workspace_path, 'logs', 'app.log')
db_path = os.path.join(workspace_path, 'db')
db_file = os.path.join(db_path, 'documents_splitter.db')
bucket_name = 'shalix-automation-dev.appspot.com'

# PENDING | MERGED | READY | FAILED | UPLOADED | UPLOAD_FAILED

## Firebase Config
cred_path = os.path.join(os.getcwd(), 'resources', 'dev_firebase.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'storageBucket': bucket_name
})

db = firestore.client()

## Plumbing Code ##################################################

def init_logger():
    logger.add(log_path, rotation='5 MB', retention='10 days', compression='zip')

def check_workspace():
    abort_if_not_exists(input_path)
    create_if_not_exists(output_s1_split_path)
    create_if_not_exists(output_final_path)

def abort_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
       logger.error(f"❌ [ABORTING PROCESS] Folder [{folder_path}] REQUIRED. CREATE THIS FOLDER AND ADD INVOICES.")
       sys.exit()

def create_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.debug(f"Folder [{folder_path}] created.")

def create_pdf_file(pdf_file, file_path):
    with open(file_path, 'wb') as new_pdf:
        pdf_file.write(new_pdf)

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as f:
        pdf_reader = PdfReader(f)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def copy_file(source, target):
    with open(source, 'rb') as file:
        content = file.read()

    with open(target, 'wb') as new_file:
        new_file.write(content)

def is_invoice(pdf_text):
    return not "RECUERDE PARA PEDIDOS POR INTERNET" in pdf_text

def remove_directory(path):
    try:
        shutil.rmtree(path)
        logger.info(f"== Path {path} removed.")
    except OSError as e:
        logger.error(f"== ❌ Error: {e}")

## Database Config ##################################################

create_if_not_exists(db_path)
db_connection = sqlite3.connect(db_file)
db_cursor = db_connection.cursor()

def configure_database():
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_type TEXT,
            status TEXT,
            doc_number TEXT,
            client_id TEXT,       
            cif TEXT,
            emited_at DATE,
            page INTEGER,
            total REAL,
            path TEXT
            )
    ''')
    logger.info("Database ready!")

def insert_document(doc_type, status, doc_number, client_id, cif, emited_at, page, total, path):
    db_cursor.execute(
        """INSERT INTO documents (doc_type, status, doc_number, client_id, cif, emited_at, page, total, path) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
            (doc_type, status, doc_number, client_id, cif, emited_at, page, total, path))

def insert_new_invoice(doc_number, client_id, cif, emited_at, page, total, path, success=True):
    insert_document(
        'INVOICE', 
        'PENDING' if success else 'FAILED',
        doc_number, client_id, cif, emited_at, page, total, path)

def insert_merged_invoice(doc_type, doc_number, client_id, cif, emited_at, total, path, success=True):
    insert_document(
        doc_type, 
        'READY' if success else 'FAILED',
        doc_number, client_id, cif, emited_at, 1, total, path)

def insert_albaran(doc_number, cif, emited_at, page, total, path):
    insert_document('ALBARAN', 'PENDING', doc_number, 'client_id', cif, emited_at, page, total, path)

def update_merged_invoices(doc_number, client_id, doc_type):
    update_document(doc_number, client_id, 'MERGED', doc_type)

def update_ready_invoice(doc_number, client_id, doc_type):
    update_document(doc_number, client_id, 'READY', doc_type)

def update_document(doc_number, client_id, status, doc_type):
    db_cursor.execute('''
                   UPDATE documents SET status = ?
                      WHERE doc_number = ? AND client_id = ? AND status = 'PENDING' AND doc_type = ?
                    ''', (status, doc_number, client_id, doc_type))
    
def find_documents_rows(status='PENDING'):
    db_cursor.execute('''
                  SELECT id, doc_number, client_id, cif, emited_at, page, total, path, doc_type
                  FROM documents
                  WHERE status = ?
                  ORDER BY doc_number, total desc
                  ''', (status,))

    return db_cursor.fetchall()

def find_documents(status='PENDING'):
    resultset = find_documents_rows(status)
    documents_map = {}

    for row in resultset:
        doc_number = row[1]
        if not doc_number in documents_map:
            documents_map[doc_number] = []
        documents_map[doc_number].append(row)
    
    return documents_map

def update_document_by_id(id, status):
    db_cursor.execute('''
                   UPDATE documents SET status = ?
                      WHERE id = ?
                    ''', (status, id,))

## Business Logic ##################################################

def split_document_pages(all_documents_path):
    """
    This function takes a pdf files with more than one page containing invoices information
    It divides the pages in idependient pdfs files and are store in stored in a folder.
    """
    all_invoices_pdf = PdfReader(open(all_documents_path, 'rb'))
    all_invoices_pdf_pages = len(all_invoices_pdf.pages)

    logger.info(f"== Split Process Started for [{all_documents_path}]: ===")
    logger.info(f"== - Pages: {all_invoices_pdf_pages}")

    def create_single_invoice_pdf(page):
        single_invoice_pdf = PdfWriter()
        single_invoice_pdf.add_page(all_invoices_pdf.pages[page])

        single_invoice_file_name = os.path.join(output_s1_split_path, f"invoice-{page + 1}.pdf")
        create_pdf_file(single_invoice_pdf, single_invoice_file_name)

        logger.info(f"== - PDF File created [{single_invoice_file_name}.pdf] ✅")

    for page in range(all_invoices_pdf_pages):
        create_single_invoice_pdf(page)

    logger.info(f"== Split Process Finished for [{all_documents_path}]")

def map_documents(splitted_documents_source_path):
    """
    This function read all documents(pdfs) that were spllited previously.
    It parse the document to find the Customer CIF number and save a new PDF file with the CIF name.
    """
    logger.info(f"== CIF Mapping Process Started in folder [{splitted_documents_source_path}]: ===")
    
    cif_cache = {}

    def get_new_pdf_sequence(cif):
        new_pdf_sequence = 1 
        if cif in cif_cache:
            new_pdf_sequence = cif_cache[cif] + 1
        cif_cache[cif] = new_pdf_sequence
        return cif_cache[cif]

    def map_invoice(index, pdf_text):
        cif = re.search(r'CIF/DNI: \S+\s+\S+\s+(\S+)', pdf_text).group(1)
        invoice_number = re.search(r'(\d+)\s*GRACIAS POR SU PEDIDO', pdf_text).group(1)
        invoice_date = re.search(r'CIF/DNI:\s*(\d{2}-\d{2}-\d{4})', pdf_text).group(1)
        client_id = re.search(r'CIF/DNI: \d{2}-\d{2}-\d{4}\n([A-Z0-9]+)', pdf_text).group(1)
        total_result = re.search(r'(\d{1,3}(?:,\d{2})?)(?=\s*FORMA DE PAGO TOTAL FACTURA)', pdf_text)

        if cif and invoice_number and invoice_date and client_id:
            page = get_new_pdf_sequence(invoice_number)
            total = total_result.group(1) if total_result else 0
            new_pdf_file_name = f"INVOICE_{invoice_number}_{cif}_{invoice_date}_{page}.pdf"
            new_pdf_file_path = os.path.join(output_final_path, new_pdf_file_name)
            copy_file(invoice_pdf_path, new_pdf_file_path)
            insert_new_invoice(invoice_number, client_id, cif, invoice_date, page, total, new_pdf_file_path)
            logger.info(f"== - {index} Invoce PDF File Mapped for CIF [{cif}] [{new_pdf_file_path}] ✅")
        else:
            insert_new_invoice(invoice_number, client_id, cif, invoice_date, page, 0, new_pdf_file_path, False)
            logger.error(f"== - {index} Invoice PDF Mapping failed for [{invoice_pdf_path}] ❌")

    def map_albaran(index, pdf_text):
        albaran_number = re.search(r'PVV\n(\d+)', pdf_text).group(1)
        albaran_date = re.search(r'(\d{2}/\d{2}/\d{4})', pdf_text).group(1).strip().replace("/", "-")
        total_result = re.search(r'BULTOS\s+(\d+,\d+)\s+VOLUMEN', pdf_text)
        cif = re.search(r'(\w+) CONSULTAS LLAME TELEFONO', pdf_text).group(1)

        if albaran_number and albaran_date and cif:
            page = get_new_pdf_sequence(albaran_number)
            total = total_result.group(1) if total_result else 0
            new_pdf_file_name = f"ALBARAN_{albaran_number}_{cif}_{albaran_date}_{page}.pdf"
            new_pdf_file_path = os.path.join(output_final_path, new_pdf_file_name)
            copy_file(invoice_pdf_path, new_pdf_file_path)
            insert_albaran(albaran_number, cif, albaran_date, page, total, new_pdf_file_path)
            logger.info(f"== - {index} Albaran PDF File Mapped for CIF [{cif}] [{new_pdf_file_path}] ✅")
        else:
            insert_albaran(albaran_number, cif, albaran_date, page, 0, new_pdf_file_path, False)
            logger.error(f"== - {index} Albaran PDF Mapping failed for [{invoice_pdf_path}] ❌")

    for index, invoice_file_name in enumerate(os.listdir(splitted_documents_source_path)):
        try:
            invoice_pdf_path = os.path.join(splitted_documents_source_path, invoice_file_name)
            logger.debug(f"*** Processing Albaran [{invoice_pdf_path}]")
            pdf_text = extract_text_from_pdf(invoice_pdf_path).upper()
            if is_invoice(pdf_text):
                map_invoice(index + 1, pdf_text)
            else:
                map_albaran(index + 1, pdf_text)
        except Exception as e:
            logger.error(f"== ❌❌❌ Error {invoice_file_name}: [{e}]")
    
    db_connection.commit()
    logger.info(f"== CIF Mapping Process Finished in folder [{splitted_documents_source_path}]")

def merge_documents():
    def merge_docs(doc_number, documents, doc_type):
        merge_pdf = PdfWriter()
        total = 0
        # id, doc_number, client_id, cif, emited_at, page, total, path
        for document_row in documents:
            path = document_row[7]
            id = document_row[0]
            client_id = document_row[2]
            cif = document_row[3]
            emited_at = document_row[4]
            raw_total = float(str(document_row[6]).replace(',', '.'))
            total = raw_total if raw_total > 0 else total
            with open(path, 'rb') as pdf_file:
                opened_file = PdfReader(pdf_file)
                merge_pdf.add_page(opened_file.pages[0])

        merged_file_name = f"{doc_type}_{doc_number}_{cif}_{emited_at}_all.pdf"
        merged_file_path = os.path.join(output_final_path, merged_file_name)
        create_pdf_file(merge_pdf, merged_file_path)
        insert_merged_invoice(doc_type, doc_number, client_id, cif, emited_at, total, merged_file_path)
        update_merged_invoices(doc_number, client_id, doc_type)
        logger.info(f"=== - 📚✅ Merged: {merged_file_path}")

    invoices_map = find_documents()
    for invoice_number, invoices in invoices_map.items():
        if len(invoices) > 1: # MERGE
            invoice_row = invoices[0]
            doc_type = invoice_row[8]
            logger.info(f"=== Merge: {invoice_number}, Invoices: {len(invoices)}")
            merge_docs(invoice_number, invoices, doc_type)
        else:
            invoice_row = invoices[0]
            client_id = invoice_row[2]
            doc_type = invoice_row[8]
            update_ready_invoice(invoice_number, client_id, doc_type)
            logger.info(f"=== Ready: {invoice_number}")

    db_connection.commit()

def upload_documents():
    logger.info("== Upload Process to Firebase 🚀")

    bucket = storage.bucket(bucket_name)
    doc_ref = db.collection('documents')

    for document_row in find_documents_rows('READY'):
        id = document_row[0]
        doc_number = document_row[1]
        client_id = document_row[2]
        cif = document_row[3]
        emited_at = document_row[4]
        total = document_row[6]
        path = document_row[7]
        doc_type = document_row[8]
        upload_file_name=os.path.basename(path)

        logger.info(f"=== Uploading {doc_number} [{upload_file_name}] path {path}")

        try:
            blob = bucket.blob(f"documents/{cif}/{doc_type}/{upload_file_name}")
            blob.upload_from_filename(path)

            blob.make_public()

            pdf_url = blob.public_url

            doc_ref.add({
                'doc_number': doc_number,
                'client_id': client_id,
                'cif': cif,
                'emited_at': emited_at,
                'total': total,
                'doc_type': doc_type,
                'pdf_url': pdf_url,
            })

            update_document_by_id(id, 'UPLOADED')
            logger.info(f"=== Upload {doc_number} uploaded: {'pdf_url'} ✅")
        except Exception as e:
            update_document_by_id(id, 'UPLOAD_FAILED')
            logger.error(f"== ❌❌❌ Error {doc_number} id: {id}: [{e}]")

        db_connection.commit()

## ##################################################
    
def main():
    init_logger()
    logger.info("= Job Started ==========================================================")

    check_workspace()
    configure_database()
    
    split_document_pages(os.path.join(input_path, 'single.pdf'))
    map_documents(output_s1_split_path)
    merge_documents()
    remove_directory(output_s1_split_path)

    time.sleep(2)

    upload_documents()


    # TODO In another function, Do the Cleanup, remove Db records, remove folders.
    ## Remove only documents that were uploaded.

    db_connection.close()
    logger.info("= Job Finihsed =========================================================")

main()

## TODO: Procesar todo lo que esta en la carpeta por separado
## TODO: Eliminar archivo al procesarse completamente SI DIFERENTE DE FAILED


## /
## Documents
    ## CIF
          ## ALBARAN
          ## FACTURAS