import fitz
from flask import Flask, request, jsonify, send_file, render_template
import os, uuid
# import boto
import atexit

app = Flask(__name__)
# app.config.from_object('config')

MY_DOMIAN = "https://uploadandsearch.onrender.com/"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home_page():
    return "Hello world"

## If user is done his work, to free space from modified PDFs
# List to store paths of modified PDFs
modified_pdfs_to_delete = []

@atexit.register
def delete_modified_pdfs_on_exit():
    for pdf_path in modified_pdfs_to_delete:
        os.remove(pdf_path)
    print("Modified PDFs deleted on program exit.")

@app.route('/searchText', methods=['GET', 'POST'])
def search_text():
    if request.method == 'POST':
        if 'search_text' not in request.form:
            return jsonify({'error': 'Invalid input data'}), 400
        search_text = request.form['search_text']
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
                        modified_pdfs_to_delete.append(pdf_path)
                        new_pdf_path = f"{MY_DOMIAN}uploads/{modified_pdf_path}"
                        modified_pdfs.append(new_pdf_path)

        # return jsonify({'modified_pdfs': modified_pdfs}), 200
        return f'search_results: {", ".join(modified_pdfs)}'
    return render_template('search.html')

@app.route('/uploadPdf', methods=['GET', 'POST'])
def upload_pdf():
    if request.method == 'POST':
        if 'pdfs' not in request.files:
            return jsonify({'error': 'Invalid input data'}), 400

        pdf_files = request.files.getlist('pdfs')    
        pdf_urls = []

        for pdf_file in pdf_files:
            if pdf_file.filename == '':
                continue

            filename = f"{str(uuid.uuid4())}.pdf"
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # s3.upload_file(pdf_path, 'upload-and-search', f'uploads/{filename}')
            pdf_file.save(pdf_path)
            pdf_path = f"{MY_DOMIAN}uploads/{filename}"
            pdf_urls.append(pdf_path)

        # return jsonify({'pdf_urls': pdf_urls}), 200
        return f'Files uploaded successfully. Uploaded files: {", ".join(pdf_urls)}'
    return render_template('upload.html')

@app.route('/uploads/<path:filename>', methods=['GET'])
def get_pdf(filename):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(pdf_path) and pdf_path.endswith('.pdf'):
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    else:
        return 'PDF not found', 404

if __name__ == '__main__':
    app.run(debug=True)