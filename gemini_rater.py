import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import csv
import glob
from typing import List, Dict, Tuple
import pickle  # Import the pickle module


class ImageReviewer:
    def __init__(self, root):
        self.root = root
        root.title("Image Review and Rating")

        # Initialize data structures (empty initially)
        self.image_batches: Dict[str, List[str]] = {}
        self.current_batch_index: int = 0
        self.current_subfolder_index: int = 0
        self.config_data: Dict[str, Dict] = {}
        self.ratings: List[Dict] = []
        self.rating_mapping = {"NA": 0, "not at all": 1, "somewhat": 2, "strongly": 3}
        self.reverse_rating_mapping = {0: "NA", 1: "not at all", 2: "somewhat", 3: "strongly"}
        self.selected_buttons: Dict[str, tk.Button] = {}
        self.project_filepath: str | None = None  # Store the project file path
        self.sort_column: str | None = None
        self.sort_reverse: bool = False

        self.create_widgets()
        self.setup_spreadsheet()


    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New Project", command=self.new_project)  # Add New Project
        filemenu.add_command(label="Open Project...", command=self.open_project)
        filemenu.add_command(label="Save Project", command=self.save_project)
        filemenu.add_command(label="Save Project As...", command=self.save_project_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)


        self.batch_button = ttk.Button(left_frame, text="Select Batch Folder", command=self.load_batches)
        self.batch_button.pack(pady=5)

        self.spreadsheet = ttk.Treeview(left_frame, columns=(
            "Batch Index", "Image Index", "Temperature", "Top P", "Top K", "Max Tokens",
            "Whole Object", "Match Desc", "Match Style", "Reasoning", "Average Score"
        ), show="headings")
        self.spreadsheet.pack(fill=tk.BOTH, expand=True)
        self.setup_spreadsheet_columns()
        self.spreadsheet.bind("<Double-1>", self.on_spreadsheet_double_click)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        image_frame = ttk.Frame(right_frame)
        image_frame.pack(pady=10)

        self.generated_image_label = ttk.Label(image_frame)
        self.generated_image_label.pack(side=tk.LEFT, padx=5)
        self.reference_image_label = ttk.Label(image_frame)
        self.reference_image_label.pack(side=tk.LEFT, padx=5)

        index_frame = ttk.Frame(right_frame)
        index_frame.pack(pady=5)

        self.batch_index_label = ttk.Label(index_frame, text="Batch Index: N/A")
        self.batch_index_label.pack(side=tk.LEFT, padx=5)

        self.image_index_label = ttk.Label(index_frame, text="Image Index: N/A")
        self.image_index_label.pack(side=tk.LEFT, padx=5)

        self.config_text = tk.Text(right_frame, height=12, width=100, wrap=tk.WORD)
        self.config_text.pack(pady=5)
        self.config_text.insert(tk.END, "Config will be displayed here.")
        self.config_text.config(state=tk.DISABLED)

        nav_button_frame = ttk.Frame(right_frame)
        nav_button_frame.pack(pady=5)
        self.prev_image_button = ttk.Button(nav_button_frame, text="Previous Image", command=self.prev_subfolder)
        self.prev_image_button.pack(side=tk.LEFT, padx=5)
        self.next_image_button = ttk.Button(nav_button_frame, text="Next Image", command=self.next_subfolder)
        self.next_image_button.pack(side=tk.LEFT, padx=5)
        self.prev_batch_button = ttk.Button(nav_button_frame, text="Previous Batch", command=self.prev_batch)
        self.prev_batch_button.pack(side=tk.LEFT, padx=5)
        self.next_batch_button = ttk.Button(nav_button_frame, text="Next Batch", command=self.next_batch)
        self.next_batch_button.pack(side=tk.LEFT, padx=5)

        self.rating_button_frames = {}
        rating_criteria = ["Whole Object", "Match Desc", "Match Style", "Reasoning"]
        for criterion in rating_criteria:
            criterion_frame = ttk.Frame(right_frame)
            criterion_frame.pack(pady=2)

            label = ttk.Label(criterion_frame, text=criterion + ":")
            label.pack(side=tk.LEFT, padx=5)

            button_frame = ttk.Frame(criterion_frame)
            button_frame.pack(side=tk.LEFT)
            self.rating_button_frames[criterion] = button_frame
            self.selected_buttons[criterion] = None

            self.create_rating_buttons(criterion)

        self.save_button = ttk.Button(right_frame, text="Save Rating", command=self.save_rating)
        self.save_button.pack(pady=5)
        #self.save_button.config(state=tk.DISABLED)

        self.summary_button = ttk.Button(right_frame, text="Show Summary", command=self.show_summary)
        self.summary_button.pack(pady=5)

        self.save_csv_button = ttk.Button(right_frame, text="Save to CSV", command=self.save_to_csv)
        self.save_csv_button.pack(pady=5)

    def create_rating_buttons(self, criterion):
        for widget in self.rating_button_frames[criterion].winfo_children():
            widget.destroy()

        for rating_text in ["NA", "not at all", "somewhat", "strongly"]:
            button = ttk.Button(self.rating_button_frames[criterion], text=rating_text,
                                command=lambda c=criterion, rt=rating_text: self.set_rating(c, rt))
            button.pack(side=tk.LEFT, padx=2)



    def setup_spreadsheet_columns(self):
        self.spreadsheet.heading("Batch Index", text="Batch Index")
        self.spreadsheet.column("Batch Index", width=70)
        self.spreadsheet.heading("Image Index", text="Image Index")
        self.spreadsheet.column("Image Index", width=70)
        self.spreadsheet.heading("Temperature", text="Temperature")
        self.spreadsheet.column("Temperature", width=70)
        self.spreadsheet.heading("Top P", text="Top P")
        self.spreadsheet.column("Top P", width=50)
        self.spreadsheet.heading("Top K", text="Top K")
        self.spreadsheet.column("Top K", width=50)
        self.spreadsheet.heading("Max Tokens", text="Max Tokens")
        self.spreadsheet.column("Max Tokens", width=80)
        self.spreadsheet.heading("Whole Object", text="Whole Object")
        self.spreadsheet.column("Whole Object", width=100)
        self.spreadsheet.heading("Match Desc", text="Match Desc")
        self.spreadsheet.column("Match Desc", width=100)
        self.spreadsheet.heading("Match Style", text="Match Style")
        self.spreadsheet.column("Match Style", width=100)
        self.spreadsheet.heading("Reasoning", text="Reasoning")
        self.spreadsheet.column("Reasoning", width=80)
        self.spreadsheet.heading("Average Score", text="Average Score")
        self.spreadsheet.column("Average Score", width=80)

    

    def on_spreadsheet_double_click(self, event):
        """Handles double-click events on the spreadsheet."""
        region = self.spreadsheet.identify("region", event.x, event.y)
        if region == "heading":
            column = self.spreadsheet.identify_column(event.x)
            column_name = self.spreadsheet.heading(column, "text")
            self.sort_spreadsheet(column_name)
        else:
            item = self.spreadsheet.selection()[0]  # Get selected item ID
            values = self.spreadsheet.item(item, 'values')  # Get values of the item
            try:
                # Extract batch and image indices from the selected row
                clicked_batch_index = int(values[0])
                clicked_image_index = int(values[1])
                # Check if the indices are valid for the current data
                batch_paths = list(self.image_batches.keys())
                if clicked_batch_index < len(batch_paths):
                    current_batch_path = batch_paths[clicked_batch_index]
                    if clicked_image_index < len(self.image_batches[current_batch_path]):
                        # Update current indices and display the image
                        self.current_batch_index = clicked_batch_index
                        self.current_subfolder_index = clicked_image_index
                        self.display_current_images()
                    else:
                        messagebox.showerror("Error", "Invalid image index.")
                else:
                    messagebox.showerror("Error", "Invalid batch index.")
            except ValueError:
                messagebox.showerror("Error", "Invalid data in the selected row.")
            except IndexError:
                messagebox.showerror("Error", "Please select a valid row")


        
    def sort_spreadsheet(self, column):
        """Sorts the spreadsheet data by the given column."""
        if self.sort_column == column:
            # Toggle reverse if same column is clicked again
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False  # Default to ascending
        
        # Get data from spreadsheet (list of tuples)
        data = [(self.spreadsheet.set(child, column), child) for child in self.spreadsheet.get_children('')]
        
        # Sort data (handle different data types)
        try:
            # Try numeric sort first
            data.sort(key=lambda x: float(x[0]), reverse=self.sort_reverse)
        except ValueError:
            # Fallback to string sort if numeric fails
             data.sort(key=lambda x: x[0], reverse=self.sort_reverse)
        
        # Rearrange items in the Treeview
        for index, (val, child) in enumerate(data):
            self.spreadsheet.move(child, '', index)  # Move item to new index



    def setup_spreadsheet(self):
        for item in self.spreadsheet.get_children():
            self.spreadsheet.delete(item)

        for rating_entry in self.ratings:
            batch_idx = rating_entry['Batch Index']
            image_idx = rating_entry['Image Index']
            config = self.config_data.get(list(self.image_batches.keys())[batch_idx], {})

            # Calculate average score (same logic as in show_summary)
            whole_object_score = self.rating_mapping.get(rating_entry.get("Whole Object", "NA"), 0)
            match_desc_score = self.rating_mapping.get(rating_entry.get("Match Desc", "NA"), 0)
            match_style_score = self.rating_mapping.get(rating_entry.get("Match Style", "NA"), 0)
            reasoning_score = self.rating_mapping.get(rating_entry.get("Reasoning", "NA"), 0)
            average_score = (whole_object_score + match_desc_score + match_style_score + reasoning_score) / 4

            values = (
                batch_idx,
                image_idx,
                config.get('Temperature', 'N/A'),
                config.get('Top P', 'N/A'),
                config.get('Top K', 'N/A'),
                config.get('Max Output Tokens', 'N/A'),
                rating_entry.get("Whole Object", "NA"),
                rating_entry.get("Match Desc", "NA"),
                rating_entry.get("Match Style", "NA"),
                rating_entry.get("Reasoning", "NA"),
                f"{average_score:.2f}",
            )
            self.spreadsheet.insert("", "end", values=values)
        
        if self.sort_column:
            self.sort_spreadsheet(self.sort_column)



    def load_batches(self):
        batch_folder_path = filedialog.askdirectory(title="Select Batch Folder")
        if not batch_folder_path:
            return

        # Do NOT reset data structures here; keep existing data for project saving/loading.
        # self.image_batches = {}  <--  NO!
        # self.config_data = {}
        # self.ratings = []

        batch_folders = [f.path for f in os.scandir(batch_folder_path) if f.is_dir()]

        for i, batch_path in enumerate(batch_folders):
            subfolders = sorted([f.path for f in os.scandir(batch_path) if f.is_dir()])
            if subfolders:
                self.image_batches[batch_path] = subfolders # Add to existing batches.

            config_path = os.path.join(batch_path, "config.txt")
            if os.path.exists(config_path):
                self.config_data[batch_path] = self.load_config(config_path)
            else:
                messagebox.showwarning("Warning", f"config.txt not found in {batch_path}")
                self.config_data[batch_path] = {}

        if not self.image_batches:
            messagebox.showinfo("Info", "No image batches found.")
            return
        # Don't reset indices when adding new batches.
        # self.current_batch_index = 0
        # self.current_subfolder_index = 0
        self.setup_spreadsheet()  # Refresh the spreadsheet to include new data
        self.display_current_images()

    def load_config(self, config_path: str) -> Dict:
        config = {}
        try:
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Temperature:"):
                        config["Temperature"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Top P:"):
                        config["Top P"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Top K:"):
                        config["Top K"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Max Output Tokens:"):
                        config["Max Output Tokens"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Prompt:"):
                        config["Prompt"] = line.split(":", 1)[1].strip()
        except FileNotFoundError:
            messagebox.showwarning("Warning", f"Config file not found: {config_path}")
            return {}
        except Exception as e:
            messagebox.showerror("Error", f"Error loading config file: {e}")
            return {}
        return config

    def display_current_images(self):
        if not self.image_batches:
            self.clear_image_and_config()
            return

        batch_paths = list(self.image_batches.keys())
        current_batch_path = batch_paths[self.current_batch_index]
        current_subfolder_path = self.image_batches[current_batch_path][self.current_subfolder_index]

        generated_image_path = os.path.join(current_subfolder_path, "gemini_image.png")
        self.load_and_display_image(generated_image_path, self.generated_image_label)

        reference_image_files = [f for f in os.listdir(current_subfolder_path)
                                  if os.path.isfile(os.path.join(current_subfolder_path, f)) and f != "gemini_image.png"]

        if reference_image_files:
             reference_image_path = os.path.join(current_subfolder_path, reference_image_files[0])
             self.load_and_display_image(reference_image_path, self.reference_image_label)
        else:
            messagebox.showwarning("Warning", "No reference image found in subfolder.")
            self.reference_image_label.config(image="")

        config = self.config_data.get(current_batch_path, {})
        self.display_config(config)

        self.batch_index_label.config(text=f"Batch Index: {self.current_batch_index}")
        self.image_index_label.config(text=f"Image Index: {self.current_subfolder_index}")

        self.update_rating_buttons()


    def clear_image_and_config(self):
        self.generated_image_label.config(image="")
        self.reference_image_label.config(image="")
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete("1.0", tk.END)
        self.config_text.insert("1.0", "No batches loaded.")
        self.config_text.config(state=tk.DISABLED)

        self.batch_index_label.config(text="Batch Index: N/A")
        self.image_index_label.config(text="Image Index: N/A")

    def load_and_display_image(self, image_path, label_widget):
        try:
            img = Image.open(image_path)
            max_size = (400, 400)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label_widget.config(image=photo)
            label_widget.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")
            label_widget.config(image="")


    def display_config(self, config: Dict):
        self.config_text.config(state=tk.NORMAL)
        self.config_text.delete("1.0", tk.END)
        config_str = ""
        for key, value in config.items():
            if key != "Prompt":
                config_str += f"{key}: {value}\n"
        if "Prompt" in config:
            config_str += f"Prompt: {config['Prompt']}\n"

        self.config_text.insert("1.0", config_str)
        self.config_text.config(state=tk.DISABLED)

    def prev_subfolder(self):
        if self.current_subfolder_index > 0:
            self.current_subfolder_index -= 1
            self.display_current_images()

    def next_subfolder(self):
        batch_paths = list(self.image_batches.keys())
        current_batch_path = batch_paths[self.current_batch_index]

        if self.current_subfolder_index < len(self.image_batches[current_batch_path]) - 1:
            self.current_subfolder_index += 1
            self.display_current_images()

    def prev_batch(self):
        if self.current_batch_index > 0:
            self.current_batch_index -= 1
            self.current_subfolder_index = 0
            self.display_current_images()

    def next_batch(self):
        if self.current_batch_index < len(self.image_batches) - 1:
            self.current_batch_index += 1
            self.current_subfolder_index = 0
            self.display_current_images()


    def get_rating(self, batch_index: int, image_index: int, criterion: str) -> int | None:
        for rating_entry in self.ratings:
            if (rating_entry['Batch Index'] == batch_index and
                rating_entry['Image Index'] == image_index and
                criterion in rating_entry):
                return self.rating_mapping.get(rating_entry[criterion])
        return None

    def set_rating(self, criterion: str, rating_value: str):
        """Sets the rating and visually updates the buttons."""

        batch_paths = list(self.image_batches.keys())
        current_batch_path = batch_paths[self.current_batch_index]  # noqa: F841

        existing_rating_index = None
        for i, rating_entry in enumerate(self.ratings):
            if (rating_entry['Batch Index'] == self.current_batch_index and
                rating_entry['Image Index'] == self.current_subfolder_index):
                existing_rating_index = i
                break

        if existing_rating_index is not None:
            self.ratings[existing_rating_index][criterion] = rating_value
        else:
            rating_entry = {
                'Batch Index': self.current_batch_index,
                'Image Index': self.current_subfolder_index,
                "Whole Object": "NA",
                "Match Desc": "NA",
                "Match Style": "NA",
                "Reasoning": "NA",
            }
            rating_entry[criterion] = rating_value
            self.ratings.append(rating_entry)

        if self.selected_buttons[criterion]:
            self.selected_buttons[criterion].config(relief=tk.RAISED)

        for button in self.rating_button_frames[criterion].winfo_children():
            if button.cget('text') == rating_value:
                button.config(relief=tk.SUNKEN)
                self.selected_buttons[criterion] = button
                break

        self.setup_spreadsheet()


    def update_rating_buttons(self):
        for criterion in self.rating_button_frames:
            current_rating = self.get_rating(self.current_batch_index, self.current_subfolder_index, criterion)
            for button in self.rating_button_frames[criterion].winfo_children():
                if current_rating is not None and button.cget('text') == self.reverse_rating_mapping.get(current_rating):
                    button.config(relief=tk.SUNKEN)
                    self.selected_buttons[criterion] = button
                else:
                    button.config(relief=tk.RAISED)
                    if button == self.selected_buttons[criterion]:
                        self.selected_buttons[criterion] = None

    def save_rating(self):
        self.setup_spreadsheet() # The spreadsheet is updated automatically now.

    def show_summary(self):
        if not self.ratings:
             messagebox.showinfo("Info", "No ratings to summarize.")
             return

        aggregated_ratings = []
        for rating_entry in self.ratings:
            batch_idx = rating_entry['Batch Index']
            image_idx = rating_entry['Image Index']
            config = self.config_data.get(list(self.image_batches.keys())[batch_idx], {})

            whole_object_score = self.rating_mapping.get(rating_entry.get("Whole Object", "NA"), 0)
            match_desc_score = self.rating_mapping.get(rating_entry.get("Match Desc", "NA"), 0)
            match_style_score = self.rating_mapping.get(rating_entry.get("Match Style", "NA"), 0)
            reasoning_score = self.rating_mapping.get(rating_entry.get("Reasoning", "NA"), 0)

            average_score = (whole_object_score + match_desc_score + match_style_score + reasoning_score) / 4

            aggregated_ratings.append({
                'Batch Index': batch_idx,
                'Image Index': image_idx,
                'Temperature': config.get('Temperature', 'N/A'),
                'Top P': config.get('Top P', 'N/A'),
                'Top K': config.get('Top K', 'N/A'),
                'Max Tokens': config.get('Max Output Tokens', 'N/A'),
                'Whole Object': rating_entry.get("Whole Object", "NA"),
                'Match Desc': rating_entry.get("Match Desc", "NA"),
                'Match Style': rating_entry.get("Match Style", "NA"),
                'Reasoning': rating_entry.get("Reasoning", "NA"),
                'Average Score': average_score
            })

        sorted_ratings = sorted(aggregated_ratings, key=lambda x: x['Average Score'], reverse=True)
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Rating Summary")

        summary_tree = ttk.Treeview(summary_window, columns=(
            "Batch Index", "Image Index", "Temperature", "Top P", "Top K", "Max Tokens",
            "Whole Object", "Match Desc", "Match Style", "Reasoning", "Average Score"
        ), show="headings")
        summary_tree.pack(fill=tk.BOTH, expand=True)
        summary_tree.heading("Batch Index", text="Batch Index")
        summary_tree.column("Batch Index", width=80)
        summary_tree.heading("Image Index", text="Image Index")
        summary_tree.column("Image Index", width=80)
        summary_tree.heading("Temperature", text="Temperature")
        summary_tree.column("Temperature", width=80)
        summary_tree.heading("Top P", text="Top P")
        summary_tree.column("Top P", width=80)
        summary_tree.heading("Top K", text="Top K")
        summary_tree.column("Top K", width=80)
        summary_tree.heading("Max Tokens", text="Max Tokens")
        summary_tree.column("Max Tokens", width=80)
        summary_tree.heading("Whole Object", text="Whole Object")
        summary_tree.column("Whole Object", width=100)
        summary_tree.heading("Match Desc", text="Match Desc")
        summary_tree.column("Match Desc", width=100)
        summary_tree.heading("Match Style", text="Match Style")
        summary_tree.column("Match Style", width=100)
        summary_tree.heading("Reasoning", text="Reasoning")
        summary_tree.column("Reasoning", width=100)
        summary_tree.heading("Average Score", text="Average Score")
        summary_tree.column("Average Score", width=100)

        for rating_data in sorted_ratings:
            summary_tree.insert("", "end", values=(
                rating_data['Batch Index'],
                rating_data['Image Index'],
                rating_data['Temperature'],
                rating_data['Top P'],
                rating_data['Top K'],
                rating_data['Max Tokens'],
                rating_data["Whole Object"],
                rating_data["Match Desc"],
                rating_data["Match Style"],
                rating_data["Reasoning"],
                rating_data['Average Score']
            ))
    def save_to_csv(self):
        if not self.ratings:
            messagebox.showinfo("Info", "No ratings to save.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = ["Batch Index", "Image Index", "Batch Path", "Image Path", "Temperature", "Top P", "Top K", "Max Tokens",
                              "Whole Object", "Match Desc", "Match Style", "Reasoning"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for rating_entry in self.ratings:
                    batch_idx = rating_entry['Batch Index']
                    image_idx = rating_entry['Image Index']
                    batch_paths = list(self.image_batches.keys())
                    batch_path = batch_paths[batch_idx]
                    image_path = self.image_batches[batch_path][image_idx]
                    config = self.config_data.get(batch_path, {})
                    row = {
                        'Batch Index': batch_idx,
                        'Image Index': image_idx,
                        'Batch Path': batch_path,
                        'Image Path': image_path,
                        'Temperature': config.get('Temperature', 'N/A'),
                        'Top P': config.get('Top P', 'N/A'),
                        'Top K': config.get('Top K', 'N/A'),
                        'Max Tokens': config.get('Max Output Tokens', 'N/A'),
                        "Whole Object": rating_entry.get("Whole Object", "NA"),
                        "Match Desc": rating_entry.get("Match Desc", "NA"),
                        "Match Style": rating_entry.get("Match Style", "NA"),
                        "Reasoning": rating_entry.get("Reasoning", "NA"),
                    }
                    writer.writerow(row)

            messagebox.showinfo("Saved", f"Ratings saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving to CSV: {e}")

    def new_project(self):
        """Clears all data to start a new project."""
        if self.ratings or self.image_batches:  # Check for unsaved changes
            response = messagebox.askyesnocancel("New Project", "Do you want to save the current project before starting a new one?")
            if response == True:  # User wants to save
                self.save_project()  # Call the save_project function
            elif response == False: #user wants to discard
                pass
            else: # User cancelled
                return

        # Clear all data structures
        self.image_batches = {}
        self.current_batch_index = 0
        self.current_subfolder_index = 0
        self.config_data = {}
        self.ratings = []
        self.selected_buttons = {}  # Reset selected buttons
        self.project_filepath = None #clear the path
        self.sort_column = None  # Reset the sort column
        self.sort_reverse = False  # Reset the sort order
        # Clear the spreadsheet
        for item in self.spreadsheet.get_children():
            self.spreadsheet.delete(item)

        # Reset the UI
        self.clear_image_and_config()
        for criterion in self.rating_button_frames:  # Recreate rating buttons
            self.create_rating_buttons(criterion)
        self.update_rating_buttons()  # Ensure buttons are in default state


    def save_project(self):
        """Saves the current project to the current file (if set) or prompts for a new file."""
        if self.project_filepath:
            self.save_project_data(self.project_filepath)
        else:
            self.save_project_as()  # If no file is set, use "Save As"


    def save_project_as(self):
        """Prompts the user for a file to save the project and saves it."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".irproj",  # Custom extension
            filetypes=[("Image Reviewer Project", "*.irproj"), ("All files", "*.*")]
        )
        if filepath:
            self.save_project_data(filepath)
            self.project_filepath = filepath  # Store the path


    def save_project_data(self, filepath: str):
        """Saves the project data to the specified file."""
        project_data = {
            'image_batches': self.image_batches,
            'current_batch_index': self.current_batch_index,
            'current_subfolder_index': self.current_subfolder_index,
            'config_data': self.config_data,
            'ratings': self.ratings,
            'sort_column': self.sort_column,  # Save the sort column
            'sort_reverse': self.sort_reverse,  # Save the sort order
            #  selected_buttons cannot be saved
        }

        try:
            with open(filepath, 'wb') as f:  # 'wb' for binary write
                pickle.dump(project_data, f)  # Serialize the data
            messagebox.showinfo("Saved", f"Project saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving project: {e}")


    def open_project(self):
      """Opens a previously saved project file."""
      if self.ratings or self.image_batches:  # Check for unsaved changes
          response = messagebox.askyesnocancel("Open Project", "Do you want to save the current project before opening another?")
          if  response == True:
              self.save_project()
          elif response == False:
              pass
          else: #user cancelled
              return
      filepath = filedialog.askopenfilename(
            filetypes=[("Image Reviewer Project", "*.irproj"), ("All files", "*.*")]
        )
      if filepath:
          try:
              with open(filepath, 'rb') as f:  # 'rb' for binary read
                  project_data = pickle.load(f)  # Deserialize the data
              
              # Restore data
              self.image_batches = project_data['image_batches']
              self.current_batch_index = project_data['current_batch_index']
              self.current_subfolder_index = project_data['current_subfolder_index']
              self.config_data = project_data['config_data']
              self.ratings = project_data['ratings']
              self.project_filepath = filepath #remember file path
              self.sort_column = project_data.get('sort_column')  # Load the sort column
              self.sort_reverse = project_data.get('sort_reverse')  # Load the sort order
              # selected buttons cannot be loaded, need to reinitialize
              for criterion in self.rating_button_frames:  # Recreate rating buttons
                  self.create_rating_buttons(criterion)  

              # Refresh UI
              self.setup_spreadsheet()
              self.display_current_images()
              # self.update_rating_buttons()  # Update based on loaded ratings
              messagebox.showinfo("Loaded", f"Project loaded from {filepath}")

          except Exception as e:
              messagebox.showerror("Error", f"Error loading project: {e}")

root = tk.Tk()
app = ImageReviewer(root)
root.mainloop()