import fitz
from flask import Flask, request, jsonify
import os, uuid
# import atexit

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home_page():
    return "Hello world"

## If user is done his work, to free space from modified PDFs
# List to store paths of modified PDFs
# modified_pdfs_to_delete = []

# @atexit.register
# def delete_modified_pdfs_on_exit():
#     for pdf_path in modified_pdfs_to_delete:
#         os.remove(pdf_path)
#     print("Modified PDFs deleted on program exit.")

@app.route('/searchText', methods=['POST'])
def search_text():
    if 'text' not in request.form:
        return jsonify({'error': 'Invalid input data'}), 400
    search_text = request.form['text']
    modified_pdfs = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Search and highlight text
            pdf_document = fitz.open(pdf_path)
            modified_pdf_path = f"modified_{filename}"
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], modified_pdf_path)

            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text_instances = page.search_for(search_text)

                if text_instances:
                    for inst in text_instances:
                        rect = fitz.Rect(inst)
                        page.add_highlight_annot(rect)

                    pdf_document.save(pdf_path)
                    # modified_pdfs_to_delete.append(pdf_path)
                    modified_pdfs.append(pdf_path)

    return jsonify({'modified_pdfs': modified_pdfs}), 200

@app.route('/uploadPdf', methods=['POST'])
def upload_pdf():
    if 'pdfs' not in request.files:
        return jsonify({'error': 'Invalid input data'}), 400

    pdf_files = request.files.getlist('pdfs')    
    pdf_urls = []

    for pdf_file in pdf_files:
        if pdf_file.filename == '':
            continue

        filename = f"{str(uuid.uuid4())}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(pdf_path)
        pdf_urls.append(pdf_path)

    return jsonify({'pdf_urls': pdf_urls}), 200


if __name__ == '__main__':
    app.run()
