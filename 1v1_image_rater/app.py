import os
import glob
import csv
import argparse
from flask import Flask, request, render_template, jsonify, send_from_directory

app = Flask(__name__)

# Globals for simplicity (only one user expected)
image_folder = None
pairs = []      # List of dicts: {"prompt": <N>, "img0": <filename>, "img1": <filename>}
votes = []      # List of dicts: {"prompt": <N>, "vote": 0 or 1}
current_index = 0

def load_pairs():
    """Scans the image folder for valid pairs and sorts them by prompt number."""
    global pairs, image_folder
    # Look for files matching prompt_*_0.png
    file_pattern = os.path.join(image_folder, "*_1.png")
    print(file_pattern)
    file0_list = sorted(glob.glob(file_pattern))
    for file0 in file0_list:
        base0 = os.path.basename(file0)
        # Expecting names like "prompt_1.png"
        if base0.endswith("_1.png"):
            #prompt_number = base1[len("prompt_"):-len("_1.png")]
            prompt = base0[:-len("_1.png")]
            # Construct the corresponding file for the other image
            base1 = f"{prompt}_2.png"
            file1 = os.path.join(image_folder, base1)
            if os.path.exists(file1):
                pairs.append({
                    "prompt": prompt,
                    "img0": base0,  # We’ll serve these files via our custom route.
                    "img1": base1
                })
    # Sort pairs by the integer value of the prompt number
    # pairs.sort(key=lambda x: int(x["prompt"]))
    # Sort pairs by alphabetical order of the prompt
    pairs.sort(key=lambda x: x["prompt"])

def write_csv():
    """Writes the recorded votes to a CSV file."""
    with open("votes.csv", "w", newline="") as csvfile:
        fieldnames = ["prompt", "vote"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for vote_entry in votes:
            writer.writerow(vote_entry)

@app.route('/')
def index():
    """Main page. Shows the current image pair or a finished message if done."""
    global current_index, pairs
    if current_index < len(pairs):
        pair = pairs[current_index]
        return render_template("index.html",
                               pair=pair,
                               current_index=current_index,
                               total=len(pairs))
    else:
        return render_template("finished.html")

@app.route('/vote', methods=['POST'])
def vote():
    """
    Expects a JSON POST with the vote:
      { "vote": 0 }  (if left)  or  { "vote": 1 }  (if right)
    Records the vote and advances to the next pair.
    """
    global current_index, pairs, votes
    data = request.get_json()
    vote_value = data.get("vote")
    if current_index < len(pairs):
        current_pair = pairs[current_index]
        votes.append({
            "prompt": current_pair["prompt"],
            "vote": vote_value
        })
        current_index += 1
        # If this was the last pair, write the CSV file
        if current_index == len(pairs):
            write_csv()
            return jsonify({"finished": True})
        return jsonify({"finished": False})
    # In case there is no pair left
    return jsonify({"finished": True})

@app.route('/images/<filename>')
def serve_image(filename):
    """Serves image files from the image folder."""
    return send_from_directory(image_folder, filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Preference Evaluation App: Evaluate image pairs by pressing 'a' (left) or ';' (right)."
    )
    parser.add_argument("image_folder", help="Path to folder containing images")
    args = parser.parse_args()
    image_folder = args.image_folder
    if not os.path.exists(image_folder):
        print(f"Error: Folder '{image_folder}' does not exist!")
        exit(1)
    load_pairs()
    if len(pairs) == 0:
        print("Error: No valid image pairs found in the folder!")
        exit(1)
    # Start the Flask server (accessible on all interfaces at port 5000)
    app.run(host="0.0.0.0", port=5002, debug=True)
