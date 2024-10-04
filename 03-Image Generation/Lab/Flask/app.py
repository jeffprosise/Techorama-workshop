import os, base64
from flask import Flask, render_template, request
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(24)

# TODO: Instantiate the CLIP model

# TODO: Define candidate labels

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Display the image that was uploaded
        image = request.files["file"]
        uri = "data:;base64," + base64.b64encode(image.read()).decode("utf-8")
        image.seek(0)

        # Identify the species
        species = identify_species(Image.open(image))

    else:
        # Display a placeholder image
        uri = "/static/placeholder.png"
        species = "&nbsp;"

    return render_template("index.html", image_uri=uri, label=species)

# Function that uses zero-shot image classification to classify a bird image
def identify_species(image):
    return 'Unknown Species'