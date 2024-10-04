import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Paths to media directories
IMAGE_DIR = 'static/slides'
AUDIO_DIR = 'static/audio'

# Ensure that the audio directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

# Get a sorted list of images from the slides directory
images = sorted(
    [file for file in os.listdir(IMAGE_DIR) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Function to fetch the slide count
@app.route('/get_slide_count')
def get_slide_count():
    return jsonify({ 'count': f'{len(images)}'})

# Function to fetch a slide
@app.route('/get_slide/<int:index>')
def get_slide(index):
    if index >= 0 and index < len(images):
        image_name = images[index]
        image_url = f'{IMAGE_DIR}/{image_name}'

        return jsonify({
            'image_url': image_url,
            'audio_url': ''
        })

    return jsonify({
        'image_url': '',
        'audio_url': ''
    })
