#!/usr/bin/env python3

import os
import sys
import glob
import csv

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def rate_images_in_directory(image_dir, output_csv='image_ratings.csv'):
    """
    Displays all images in 'image_dir'. For each image, waits for the user to
    press 'y' or 'n' (case-insensitive) and stores the rating.
    Ratings are saved to 'output_csv' at the end.
    """
    # Gather image files from the directory (you can add more extensions if needed)
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif")
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(image_dir, ext)))
    
    # Sort for consistent viewing order
    image_paths.sort()

    if not image_paths:
        print(f"No images found in directory: {image_dir}")
        return

    # Dictionary to store { filename: 'Y'/'N' }
    ratings = {}

    print(f"Found {len(image_paths)} images in '{image_dir}'.")
    print("Press 'y' or 'n' to rate each image. Press 'q' to quit early.\n")

    for img_path in image_paths:
        # Read image
        img = mpimg.imread(img_path)

        # Display image
        fig, ax = plt.subplots()
        ax.imshow(img)
        ax.set_title(os.path.basename(img_path))
        ax.axis('off')  # Hide axes
        plt.tight_layout()

        # Key press event handler
        user_key = []

        def on_key(event):
            # Store the key pressed, then close the figure
            user_key.append(event.key.lower())
            plt.close()

        cid = fig.canvas.mpl_connect('key_press_event', on_key)
        plt.show()  # Blocks until the figure is closed

        if not user_key:
            # If user somehow closed window without pressing a key
            print("No rating provided, skipping this image...")
            continue

        key_pressed = user_key[0]
        if key_pressed == 'q':
            # Quit early
            print("\nQuitting early...")
            break
        elif key_pressed == 'y':
            ratings[img_path] = 'Y'
        elif key_pressed == 'n':
            ratings[img_path] = 'N'
        else:
            # If invalid key pressed, skip rating
            print(f"Invalid key '{key_pressed}' - skipping this image...")
            continue

    # Save ratings to CSV
    if ratings:
        # If you already have ratings in a CSV and want to append,
        # you might load them first or choose a different writing mode.
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["filename", "rating"])
            for filename, rating in ratings.items():
                writer.writerow([filename, rating])

        print(f"\nRatings saved to {output_csv}")
    else:
        print("\nNo ratings to save.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python rate_images.py <image_directory> [output_csv]")
        sys.exit(1)

    image_dir = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else 'image_ratings.csv'
    rate_images_in_directory(image_dir, output_csv)

if __name__ == "__main__":
    main()
