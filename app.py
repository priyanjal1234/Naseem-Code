from flask import Flask, request, render_template, send_from_directory, jsonify
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove
import os
import uuid

app = Flask(__name__)

# Set up directories
UPLOAD_FOLDER = './static/uploads'
EDITED_FOLDER = './static/edited'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EDITED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EDITED_FOLDER'] = EDITED_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Helper function to check file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')


# Route: Upload and Process Image
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Save uploaded file
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process image based on user selection
        operation = request.form.get('operation')
        edited_filename = f"edited_{filename}"
        edited_filepath = os.path.join(app.config['EDITED_FOLDER'], edited_filename)

        try:
            if operation == 'grayscale':
                image = Image.open(filepath).convert('L')  # Convert to grayscale
                image.save(edited_filepath)
            elif operation == 'blur':
                image = Image.open(filepath).filter(ImageFilter.BLUR)  # Apply blur
                image.save(edited_filepath)
            elif operation == 'remove_bg':
                with open(filepath, 'rb') as img_file:
                    result = remove(img_file.read())  # Remove background using rembg
                with open(edited_filepath, 'wb') as out_file:
                    out_file.write(result)
            elif operation == 'enhance':
                image = Image.open(filepath)
                enhancer = ImageEnhance.Color(image)
                enhanced_image = enhancer.enhance(1.5)  # Increase color intensity
                enhanced_image.save(edited_filepath)
            else:
                return jsonify({'error': 'Invalid operation'}), 400

        except Exception as e:
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500

        # Return edited image URL
        return jsonify({
            'original_image': f"/static/uploads/{filename}",
            'edited_image': f"/static/edited/{edited_filename}"
        })

    return jsonify({'error': 'Invalid file type'}), 400


# Route: Serve Edited Image
@app.route('/edited/<filename>')
def edited_file(filename):
    return send_from_directory(app.config['EDITED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
