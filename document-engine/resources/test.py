import sqlite3
import os

workspace_path = os.path.join(os.getcwd(), 'workspace')
db_path = os.path.join(workspace_path, 'db')
db_file = os.path.join(db_path, 'documents_splitter.db')

def create_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

create_if_not_exists(db_path)
db_connection = sqlite3.connect(db_file)
db_cursor = db_connection.cursor()

db_cursor.execute('''
                  SELECT id, doc_number, client_id, cif, emited_at, page, total, path
                  FROM documents
                  WHERE status='PENDING' AND doc_type='INVOICE'
                  ORDER BY doc_number, total desc
                  ''')

resultset = db_cursor.fetchall()
documents_map = {}

for row in resultset:
    doc_number = row[1]
    if not doc_number in documents_map:
        documents_map[doc_number] = []
    documents_map[doc_number].append(row)

print(documents_map)

db_cursor.close()
db_connection.close()
