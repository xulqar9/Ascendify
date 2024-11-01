import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
from datetime import datetime, timedelta
import asyncio

class Ascendify(toga.App):
    def __init__(self):
        super().__init__(formal_name="Ascendify", app_id="com.Ascendify", app_name="Ascendify")
        self.interval_minutes = None

    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # User inputs for wake, sleep, exercise details, frequency selection
        self.wake_time_input = toga.TextInput(placeholder="Enter wake-up time (HH:MM)", style=Pack(width=200))
        self.sleep_time_input = toga.TextInput(placeholder="Enter sleep time (HH:MM)", style=Pack(width=200))
        self.set_time_button = toga.Button("Set Time Interval", on_press=self.set_time_interval, style=Pack(padding=(5, 0)))
        self.exercise_input = toga.TextInput(placeholder="Enter exercise (e.g., Push-ups)", style=Pack(width=200))
        self.rep_goal_input = toga.TextInput(placeholder="Enter daily reps", style=Pack(width=200))
        self.add_exercise_button = toga.Button("Add Exercise", on_press=self.add_exercise, style=Pack(padding=(5, 0)))

        # Frequency options for reminders
        self.frequency_options = ["Every hour", "Every 30 minutes", "Every 2 hours", "Custom", "Every minute"]
        self.frequency_select = toga.Selection(items=self.frequency_options, on_change=self.set_frequency, style=Pack(width=200))
        self.custom_interval_input = toga.TextInput(placeholder="Custom interval (minutes)", style=Pack(width=200))
        
        # Labels for status and reminders
        self.status_label = toga.Label("Set wake/sleep times, add exercises, and choose reminder frequency.", style=Pack(padding=(5, 0)))
        self.reps_per_interval_label = toga.Label("", style=Pack(padding=(5, 0)))
        self.countdown_label = toga.Label("", style=Pack(padding=(5, 0)))

        # Boxes for exercises and labels
        self.exercise_list_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        self.exercises = {}
        self.remaining_reps = {}

        # Add widgets to main box
        main_box.add(self.wake_time_input)
        main_box.add(self.sleep_time_input)
        main_box.add(self.set_time_button)
        main_box.add(self.exercise_input)
        main_box.add(self.rep_goal_input)
        main_box.add(self.frequency_select)
        main_box.add(self.custom_interval_input)
        main_box.add(self.add_exercise_button)
        main_box.add(self.status_label)
        main_box.add(self.reps_per_interval_label)
        main_box.add(self.exercise_list_box)
        main_box.add(self.countdown_label)

        # Create main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    def set_time_interval(self, widget):
        try:
            self.wake_time = datetime.strptime(self.wake_time_input.value, "%H:%M")
            self.sleep_time = datetime.strptime(self.sleep_time_input.value, "%H:%M")
            if self.sleep_time < self.wake_time:
                self.sleep_time += timedelta(days=1)  # Next day adjustment
            self.awake_hours = (self.sleep_time - self.wake_time).total_seconds() / 3600
            self.status_label.text = f"Awake time set: {self.awake_hours:.1f} hours."
            self.calculate_reps_per_interval()
        except ValueError:
            self.status_label.text = "Enter wake/sleep times in HH:MM format."

    def add_exercise(self, widget):
        try:
            exercise_name = self.exercise_input.value
            rep_goal = int(self.rep_goal_input.value)
            if exercise_name and rep_goal > 0:
                self.exercises[exercise_name] = rep_goal
                self.remaining_reps[exercise_name] = rep_goal
                self.update_exercise_list()
                self.status_label.text = f"{exercise_name} with {rep_goal} reps added."
                asyncio.ensure_future(self.start_reminders())
            else:
                self.status_label.text = "Enter a valid exercise and rep goal."
        except ValueError:
            self.status_label.text = "Rep goal should be a number."

    def set_frequency(self, widget=None):
        try:
            frequency = self.frequency_select.value
            if frequency == "Every 30 minutes":
                self.interval_minutes = 30
            elif frequency == "Every minute":
                self.interval_minutes = 1
            elif frequency == "Every hour":
                self.interval_minutes = 60
            elif frequency == "Every 2 hours":
                self.interval_minutes = 120
            else:
                self.interval_minutes = int(self.custom_interval_input.value)
            self.status_label.text = f"Interval set to {self.interval_minutes} minutes."
            self.calculate_reps_per_interval()
        except ValueError:
            self.status_label.text = "Enter a valid custom interval in minutes."

    def calculate_reps_per_interval(self):
        if not self.interval_minutes or not self.awake_hours:
            return
        reps_text = ""
        for exercise, goal in self.exercises.items():
            reps_per_interval = goal / (self.awake_hours * 60 / self.interval_minutes)
            reps_text += f"{exercise}: {int(reps_per_interval)} reps per interval\n"
        self.reps_per_interval_label.text = reps_text

    async def start_reminders(self):
        self.countdown_label.text = ""
        while any(self.remaining_reps.values()):
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=self.interval_minutes)

            while datetime.now() < end_time:
                remaining_time = end_time - datetime.now()
                await self.update_countdown(remaining_time)
                await asyncio.sleep(1)

            for exercise, total_reps in self.remaining_reps.items():
                reps_to_do = total_reps // (self.awake_hours * 60 / self.interval_minutes)
                self.show_reminder_popup(exercise, int(reps_to_do))

    async def update_countdown(self, remaining_time):
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.countdown_label.text = f"Next reminder in: {hours:02d}:{minutes:02d}:{seconds:02d}"

    def show_reminder_popup(self, exercise, reps_to_do):
        reminder_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        reminder_label = toga.Label(f"Time to do {reps_to_do} {exercise}! Log completed reps.", style=Pack(padding=(5, 0)))
        reminder_window = toga.Window(title="Exercise Reminder")

        complete_button = toga.Button(
            "Done", 
            on_press=lambda x: self.log_reps(exercise, reps_to_do, reminder_window), 
            style=Pack(padding=(5, 0))
        )

        reminder_box.add(reminder_label)
        reminder_box.add(complete_button)
        reminder_window.content = reminder_box
        reminder_window.show()

    def log_reps(self, exercise, reps_done, reminder_window=None):
        if exercise in self.remaining_reps:
            self.remaining_reps[exercise] -= reps_done
            if self.remaining_reps[exercise] <= 0:
                self.status_label.text = f"{exercise} goal complete!"
                self.remaining_reps[exercise] = 0
            else:
                self.status_label.text = f"{self.remaining_reps[exercise]} reps remaining for {exercise}."
            self.update_exercise_list()

        if reminder_window:
            reminder_window.close()

    def update_exercise_list(self):
        """Updates display of exercises, their daily goals, and remaining reps, with edit/delete options."""
        self.exercise_list_box.clear()

        for exercise_name, goal in self.exercises.items():
            exercise_row = toga.Box(style=Pack(direction=ROW, padding=5))
            exercise_label = toga.Label(f"{exercise_name}: {goal} reps (Left: {self.remaining_reps[exercise_name]})",style=Pack(padding=(0, 5), width=300))
            edit_button = toga.Button("Edit", on_press=lambda w, ex=exercise_name: self.edit_exercise(ex), style=Pack(padding=5))
            delete_button = toga.Button("Delete", on_press=lambda w, ex=exercise_name: self.delete_exercise(ex), style=Pack(padding=5))

            exercise_row.add(exercise_label)
            exercise_row.add(edit_button)
            exercise_row.add(delete_button)

            self.exercise_list_box.add(exercise_row)

    def edit_exercise(self, exercise_name):
        """Allows user to edit the rep goal for a specific exercise."""
        new_goal_input = toga.TextInput(placeholder=f"New goal for {exercise_name} (Current: {self.exercises[exercise_name]})")
        confirm_button = toga.Button("Confirm", on_press=lambda w: self.confirm_edit(exercise_name, new_goal_input.value))

        edit_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        edit_box.add(new_goal_input)
        edit_box.add(confirm_button)

        edit_window = toga.Window(title=f"Edit {exercise_name}")
        edit_window.content = edit_box
        edit_window.show()

    def confirm_edit(self, exercise_name, new_goal):
        try:
            new_goal = int(new_goal)
            if new_goal > 0:
                self.exercises[exercise_name] = new_goal
                self.remaining_reps[exercise_name] = new_goal
                self.update_exercise_list()
        except ValueError:
            self.status_label.text = "Enter a valid rep goal number."

    def delete_exercise(self, exercise_name):
        """Deletes an exercise from the list."""
        if exercise_name in self.exercises:
            del self.exercises[exercise_name]
            del self.remaining_reps[exercise_name]
            self.update_exercise_list()
            self.status_label.text = f"Deleted {exercise_name}."



def main():
    return Ascendify()

if __name__ == "__main__":
    main().main_loop()