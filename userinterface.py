import os
import tkinter as tk
import pandas as pd
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

# Import your scoring functions
from score_game import score_board


class TicketSelectionWindow:
    def __init__(self, master, dest_tickets, ticket_count, color):
        self.master = master
        self.dest_tickets = dest_tickets
        self.ticket_count = ticket_count
        self.color = color

        self.selected_tickets = set()

        self.selection_window = tk.Toplevel(self.master)
        self.selection_window.title("Select Tickets")

        self.create_checkboxes()


    def create_checkboxes(self):
        frame = tk.Frame(self.selection_window)
        frame.pack(padx=10, pady=10)

        self.checkbox_vars = [tk.BooleanVar() for _ in range(len(self.dest_tickets))]

        # Set the number of checkboxes to display in each row
        CHECKBOXES_PER_ROW = 3

        for i, ticket in enumerate(sorted(self.dest_tickets)):
            # Calculate row and column for each checkbox
            row = i // CHECKBOXES_PER_ROW
            col = i % CHECKBOXES_PER_ROW

            checkbox = tk.Checkbutton(frame, text=ticket, variable=self.checkbox_vars[i], onvalue=True, offvalue=False)
            checkbox.grid(row=row, column=col, sticky=tk.W)

        # Create a frame specifically for the Checkbuttons
        self.checkbox_frame = frame

        # Button to submit the selected tickets
        self.submit_button = tk.Button(self.selection_window, text="Submit", command=self.submit_tickets)
        self.submit_button.pack(pady=10)

    def submit_tickets(self):
        # Use the frame specifically created for the Checkbuttons
        children_except_button = [child for child in self.checkbox_frame.winfo_children() if child != self.submit_button]

        selected_checkboxes = [checkbox for checkbox, var in zip(children_except_button, self.checkbox_vars) if isinstance(checkbox, tk.Checkbutton) and var.get()]
        if len(selected_checkboxes) != self.ticket_count:
            messagebox.showerror("Error", f"Please select exactly {self.ticket_count} tickets.")
            return

        selected_tickets = {checkbox.cget("text") for checkbox in selected_checkboxes}


        # Update the selected_tickets attribute
        self.selected_tickets = selected_tickets

        # Destroy the window
        self.selection_window.destroy()

    def get_selected_tickets(self):
        return self.selected_tickets


class TicketToRideScorerGUI:
    def __init__(self, master):
        self.colors = ['red', 'green', 'blue', 'black', 'yellow']

        all_tickets_df = pd.read_csv('game_data/destinations.csv')
        self.tickets = set(zip(all_tickets_df['Source'], all_tickets_df['Target']))

        self.game_tickets = {}
        self.image_path = ''

        self.master = master
        self.master.title("Ticket to Ride Scorer")

        # Entry widget for image path
        self.image_path_entry = tk.Entry(master, width=50)
        self.image_path_entry.grid(row=0, column=0, padx=10, pady=10)

        # Button to move to the next step
        self.next_button = tk.Button(master, text="Next", command=self.check_image)
        self.next_button.grid(row=1, column=0, columnspan=2, pady=10)


    
    def check_image(self):
        # Get the image path from the entry widget
        self.image_path = self.image_path_entry.get()

        # Check if the file exists
        if not os.path.exists(self.image_path) or not os.path.isfile(self.image_path):
            messagebox.showerror("Error", f"The file '{self.image_path}' does not exist.")
            return
        else:
            
            for color in self.colors:
                self.game_tickets[color] = []
                self.show_ticket_window(color)

            self.calculate_score()
            

    def show_ticket_window(self, color):
        # Create a new window to get user tickets
        ticket_window = tk.Toplevel(self.master)
        ticket_window.title(str(color).capitalize() + ' Destination Tickets')

        # Label and dropdown menu for selecting the number of tickets
        label = tk.Label(ticket_window, text=f"Select the number of tickets for {color} : ")
        label.grid(row=0, column=0, padx=10, pady=10)

        # Create a list of numbers from 1 to 41 for the dropdown menu
        ticket_options = [str(i) for i in range(1, 42)]

        # Use an IntVar to store the selected value from the dropdown
        selected_tickets = tk.IntVar(ticket_window)

        # Dropdown menu
        ticket_dropdown = tk.OptionMenu(ticket_window, selected_tickets, *ticket_options)
        ticket_dropdown.grid(row=0, column=1, padx=10, pady=10)

        # Button to submit the number of tickets
        submit_button = tk.Button(ticket_window, text="Enter", command=lambda: self.select_tickets(ticket_window, color, selected_tickets.get()))
        submit_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.master.wait_window(ticket_window)


    def select_tickets(self, window, color, num_tickets):
        try:

            # Initialize data
            ticket_count = int(num_tickets)

            # Use color and num_tickets as needed
            print(f"Selected color: {color}")
            print(f"Selected number of tickets: {num_tickets}")

            # Close the ticket_window
            window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")

        if ticket_count > 0:
            ticket_selection = TicketSelectionWindow(self.master, self.tickets, ticket_count, color)
            # Wait for the selection window to be closed
            self.master.wait_window(ticket_selection.selection_window)

            # Get the selected tickets after the window is closed
            selected_tickets = ticket_selection.get_selected_tickets()

            for tick in selected_tickets:
                self.game_tickets[color].append(tick)

            self.tickets -= selected_tickets
            print(f"{color} selected tickets:", selected_tickets)

        


    def calculate_score(self):

        # Call your scoring function with user tickets
        try:
            # Pass self.tickets to your scoring function
            score_board(self.image_path, self.game_tickets)
            messagebox.showinfo("Success", "Score calculation complete!")

            # Close the GUI (assuming self.master is the root window)
            self.master.destroy()
        except Exception as e:
           messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TicketToRideScorerGUI(root)
    root.mainloop()
