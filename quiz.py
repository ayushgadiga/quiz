import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sqlite3
import random
from datetime import datetime

# ==========================================
# 1. DATABASE SETUP & EXCEPTION HANDLING
# ==========================================
def init_db():
    try:
        conn = sqlite3.connect("quiz_data.db")
        cursor = conn.cursor()
        
        # Table for Questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                q_type TEXT,
                question TEXT,
                opt1 TEXT, opt2 TEXT, opt3 TEXT, opt4 TEXT,
                correct_ans TEXT
            )
        ''')
        
        # Table for User Scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                score INTEGER,
                total INTEGER,
                date_taken TEXT
            )
        ''')
        
        # Insert a sample question if DB is empty
        cursor.execute("SELECT COUNT(*) FROM questions")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO questions (q_type, question, opt1, opt2, opt3, opt4, correct_ans)
                VALUES ('MCQ', 'What is the capital of Python?', 'Snake', 'Montréal', 'Guido', 'None', 'None')
            ''')
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to initialize DB: {e}")

# ==========================================
# 2. OOP: CLASSES & INHERITANCE
# ==========================================
class Question:
    def __init__(self, text, correct_answer):
        self.text = text
        self.correct_answer = correct_answer

    def check_answer(self, user_answer):
        return str(user_answer).strip().lower() == str(self.correct_answer).strip().lower()

class MCQ(Question):
    def __init__(self, text, options, correct_answer):
        super().__init__(text, correct_answer)
        self.options = options # List of 4 options

class TrueFalse(Question):
    def __init__(self, text, correct_answer):
        super().__init__(text, correct_answer)
        self.options = ["True", "False"]

# ==========================================
# 3. MAIN APPLICATION (TKINTER GUI)
# ==========================================
class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Quiz Exam")
        self.root.geometry("500x400")
        
        # State variables
        self.current_user = ""
        self.question_list = []
        self.current_q_index = 0
        self.score = 0
        self.time_left = 60 # 60 seconds total for the quiz
        self.timer_id = None
        self.selected_option = tk.StringVar()

        self.main_menu()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- Main Menu ---
    def main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Main Menu", font=("Arial", 20, "bold")).pack(pady=20)
        
        tk.Button(self.root, text="Start Quiz", width=20, command=self.pre_quiz_setup).pack(pady=10)
        tk.Button(self.root, text="Admin: Add Question", width=20, command=self.admin_menu).pack(pady=10)
        tk.Button(self.root, text="View History", width=20, command=self.view_history).pack(pady=10)
        tk.Button(self.root, text="Exit", width=20, command=self.root.quit).pack(pady=10)

    # --- Admin Logic ---
    def admin_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Add New Question", font=("Arial", 16)).pack(pady=10)
        
        q_type_var = tk.StringVar(value="MCQ")
        
        tk.Radiobutton(self.root, text="Multiple Choice", variable=q_type_var, value="MCQ").pack()
        tk.Radiobutton(self.root, text="True / False", variable=q_type_var, value="TF").pack()
        
        tk.Label(self.root, text="Question:").pack()
        q_entry = tk.Entry(self.root, width=50)
        q_entry.pack()

        tk.Label(self.root, text="Options (Comma separated, exactly 4 for MCQ):").pack()
        opt_entry = tk.Entry(self.root, width=50)
        opt_entry.pack()
        
        tk.Label(self.root, text="Correct Answer (Must match an option exactly):").pack()
        ans_entry = tk.Entry(self.root, width=50)
        ans_entry.pack()

        def save_q():
            q_type = q_type_var.get()
            q = q_entry.get()
            opts = [o.strip() for o in opt_entry.get().split(",")]
            ans = ans_entry.get().strip()

            try:
                if not q or not ans:
                    raise ValueError("Question and Answer cannot be empty.")
                
                conn = sqlite3.connect("quiz_data.db")
                cursor = conn.cursor()
                
                if q_type == "MCQ":
                    if len(opts) != 4:
                        raise ValueError("MCQ requires exactly 4 comma-separated options.")
                    cursor.execute("INSERT INTO questions (q_type, question, opt1, opt2, opt3, opt4, correct_ans) VALUES (?,?,?,?,?,?,?)",
                                   (q_type, q, opts[0], opts[1], opts[2], opts[3], ans))
                else:
                    cursor.execute("INSERT INTO questions (q_type, question, opt1, opt2, opt3, opt4, correct_ans) VALUES (?,?,?,?,?,?,?)",
                                   (q_type, q, "True", "False", "", "", ans))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Question added!")
                self.main_menu()
                
            except ValueError as ve:
                messagebox.showwarning("Input Error", str(ve))
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))

        tk.Button(self.root, text="Save Question", command=save_q).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    # --- Quiz Logic ---
    def pre_quiz_setup(self):
        user = simpledialog.askstring("Username", "Enter your name:")
        if user:
            self.current_user = user
            self.load_questions()
        else:
            messagebox.showwarning("Required", "Username is required to start.")

    def load_questions(self):
        try:
            conn = sqlite3.connect("quiz_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM questions")
            rows = cursor.fetchall()
            conn.close()

            self.question_list = []
            for r in rows:
                # r = (id, type, q, o1, o2, o3, o4, ans)
                if r[1] == "MCQ":
                    obj = MCQ(r[2], [r[3], r[4], r[5], r[6]], r[7])
                else:
                    obj = TrueFalse(r[2], r[7])
                self.question_list.append(obj)
            
            # Use of random module + lists
            random.shuffle(self.question_list)
            
            if not self.question_list:
                messagebox.showinfo("No Questions", "Admin needs to add questions first.")
                return

            self.current_q_index = 0
            self.score = 0
            self.time_left = 60
            self.start_quiz_ui()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load questions: {e}")

    def start_quiz_ui(self):
        self.clear_window()
        
        # Timer Label
        self.timer_label = tk.Label(self.root, text=f"Time Left: {self.time_left}s", font=("Arial", 12, "bold"), fg="red")
        self.timer_label.pack(anchor="ne", padx=10, pady=5)
        
        self.q_label = tk.Label(self.root, text="", font=("Arial", 14), wraplength=400)
        self.q_label.pack(pady=20)
        
        self.radio_frame = tk.Frame(self.root)
        self.radio_frame.pack()
        
        self.next_btn = tk.Button(self.root, text="Next / Submit", command=self.check_and_next)
        self.next_btn.pack(pady=20)
        
        self.run_timer()
        self.show_question()

    def run_timer(self):
        if self.time_left > 0:
            self.timer_label.config(text=f"Time Left: {self.time_left}s")
            self.time_left -= 1
            self.timer_id = self.root.after(1000, self.run_timer)
        else:
            self.timer_label.config(text="Time's Up!")
            messagebox.showinfo("Time's Up", "You ran out of time!")
            self.end_quiz()

    def show_question(self):
        for widget in self.radio_frame.winfo_children():
            widget.destroy()

        self.selected_option.set("") # Reset selection
        
        current_q = self.question_list[self.current_q_index]
        self.q_label.config(text=f"Q{self.current_q_index + 1}: {current_q.text}")
        
        # Tkinter Radio Buttons
        for opt in current_q.options:
            tk.Radiobutton(self.radio_frame, text=opt, variable=self.selected_option, value=opt, font=("Arial", 12)).pack(anchor="w")

    def check_and_next(self):
        user_ans = self.selected_option.get()
        if not user_ans:
            messagebox.showwarning("Warning", "Please select an option.")
            return

        # Check answer using OOP method
        current_q = self.question_list[self.current_q_index]
        if current_q.check_answer(user_ans):
            self.score += 1

        self.current_q_index += 1
        
        if self.current_q_index < len(self.question_list):
            self.show_question()
        else:
            self.end_quiz()

    def end_quiz(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id) # Stop timer
        
        try:
            # Save to DB
            conn = sqlite3.connect("quiz_data.db")
            cursor = conn.cursor()
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("INSERT INTO user_scores (username, score, total, date_taken) VALUES (?, ?, ?, ?)",
                           (self.current_user, self.score, len(self.question_list), date_now))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not save score: {e}")

        messagebox.showinfo("Quiz Finished", f"Your Score: {self.score} / {len(self.question_list)}")
        self.main_menu()

    # --- History Logic ---
    def view_history(self):
        self.clear_window()
        tk.Label(self.root, text="Score History", font=("Arial", 16, "bold")).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=("User", "Score", "Total", "Date"), show='headings')
        tree.heading("User", text="User")
        tree.heading("Score", text="Score")
        tree.heading("Total", text="Total")
        tree.heading("Date", text="Date")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            conn = sqlite3.connect("quiz_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username, score, total, date_taken FROM user_scores ORDER BY id DESC")
            for row in cursor.fetchall():
                tree.insert("", tk.END, values=row)
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load history: {e}")
            
        tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=10)

# ==========================================
# 4. APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    init_db() # Create tables if they don't exist
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()