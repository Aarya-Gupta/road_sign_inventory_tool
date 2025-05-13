# app/routes.py
import os
import uuid # To generate unique filenames
from flask import (
    Blueprint, # <<< Import Blueprint
    render_template, request, redirect, url_for,
    flash, send_from_directory, current_app # Keep current_app for use *inside* functions
)
from werkzeug.utils import secure_filename
# Adjust the import path for video_processor relative to routes.py
from .processing.video_processor import process_video
# Adjust the import path for config relative to routes.py
from config import allowed_file

# --- Create a Blueprint ---
# The first argument 'main' is the name of the blueprint.
# The second argument __name__ helps Flask locate the blueprint's resources (like templates).
bp = Blueprint('main', __name__)

# --- Define routes using the blueprint ---
@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part in the request', 'danger')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file', 'warning')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Secure the filename and create a unique name to avoid conflicts
            original_filename = secure_filename(file.filename)
            unique_id = uuid.uuid4().hex[:8] # Add 8 hex chars for uniqueness
            _, ext = os.path.splitext(original_filename)
            # Ensure extension starts with a dot if it exists
            if ext and not ext.startswith('.'):
                ext = '.' + ext
            elif not ext: # Handle cases with no extension if necessary, maybe default?
                # Decide how to handle files without extensions if allowed_file permits them
                pass 
            unique_filename = f"{unique_id}_{os.path.splitext(original_filename)[0]}{ext}" # Reconstruct filename safely

            # Use current_app.config inside the function where context exists
            upload_path = current_app.config['UPLOAD_FOLDER'] / unique_filename
            output_filename = f"processed_{unique_filename}"
            output_path = current_app.config['OUTPUT_FOLDER'] / output_filename

            try:
                # Save the uploaded file
                file.save(upload_path)
                flash(f'File "{original_filename}" uploaded successfully. Starting processing...', 'info')

                # --- Trigger the background processing ---
                process_video(str(upload_path), str(output_path), str(current_app.config['MODEL_PATH']))

                flash(f'Video processing complete for "{original_filename}".', 'success')

                # Clean up the original uploaded file after processing
                try:
                    os.remove(upload_path)
                except OSError as e:
                     current_app.logger.error(f"Error deleting uploaded file {upload_path}: {e}")


                # Use url_for with the blueprint name: 'main.download_file'
                return render_template('results.html', output_filename=output_filename)

            except Exception as e:
                # Use current_app.logger inside the function
                current_app.logger.error(f"Error processing file {original_filename}: {e}", exc_info=True)
                flash(f'An error occurred during processing: {str(e)}', 'danger')
                # Clean up potentially partially saved files
                if os.path.exists(upload_path): # Check existence before removing
                    try:
                        os.remove(upload_path)
                    except OSError as e_del_up:
                         current_app.logger.error(f"Error deleting upload file on error {upload_path}: {e_del_up}")
                if os.path.exists(output_path): # Check existence before removing
                     try:
                        os.remove(output_path)
                     except OSError as e_del_out:
                         current_app.logger.error(f"Error deleting output file on error {output_path}: {e_del_out}")
                return redirect(request.url) # Redirect back to upload page on error

        else:
            # Check if file exists before flashing error
            if file and file.filename:
                 flash(f'Invalid file type for "{secure_filename(file.filename)}". Allowed types are: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}', 'warning')
            else:
                 # If file object exists but has no filename, it was likely an empty selection
                 flash('No file selected or file type not allowed.', 'warning')
            return redirect(request.url)

    # For GET request, just show the upload form
    return render_template('index.html')


# --- Define download route using the blueprint ---
@bp.route('/download/<filename>')
def download_file(filename):
    # Make sure filename is secure and points only within the output directory
    safe_filename = secure_filename(filename)
    if not safe_filename == filename:
        flash('Invalid filename.', 'danger')
        # Use url_for with the blueprint name: 'main.index'
        return redirect(url_for('main.index'))

    output_dir = current_app.config['OUTPUT_FOLDER']

    # Check if file actually exists to prevent errors
    file_path = os.path.join(output_dir, safe_filename)
    if not os.path.exists(file_path):
        flash(f'File not found: {safe_filename}', 'danger')
        return redirect(url_for('main.index'))

    try:
        return send_from_directory(output_dir, safe_filename, as_attachment=True)
    except FileNotFoundError:
         flash(f'Error: Processed file not found ({safe_filename}).', 'danger')
         return redirect(url_for('main.index'))