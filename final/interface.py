import os
import tkinter as tk
from tkinter import scrolledtext
from transformers import AutoTokenizer, AutoModelForCausalLM

class ModelInterfaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Model Interface")

        # Load the fine-tuned model and tokenizer
        self.model_directory = "./NewsLlama"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_directory)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_directory)

        # Set up the GUI components
        self.setup_gui()

    def setup_gui(self):
        # Input label and text box
        self.input_label = tk.Label(self.root, text="Enter text:")
        self.input_label.pack(pady=5)

        self.input_text = tk.Entry(self.root, width=80)
        self.input_text.pack(pady=5)

        # Generate button
        self.generate_button = tk.Button(self.root, text="Generate Response", command=self.generate_response)
        self.generate_button.pack(pady=5)

        # Output label and text box
        self.output_label = tk.Label(self.root, text="Model response:")
        self.output_label.pack(pady=5)

        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20, wrap=tk.WORD)
        self.output_text.pack(pady=5)

    def generate_response(self):
        user_input = self.input_text.get()
        if user_input:
            response = self.get_model_response(user_input)
            self.output_text.insert(tk.END, f"You: {user_input}\n")
            self.output_text.insert(tk.END, f"Model: {response}\n\n")
            self.input_text.delete(0, tk.END)
            self.output_text.yview(tk.END)

    def get_model_response(self, input_text):
        inputs = self.tokenizer(input_text, return_tensors="pt")
        outputs = self.model.generate(inputs["input_ids"], max_length=100, num_return_sequences=1)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

def main():
    root = tk.Tk()
    app = ModelInterfaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
