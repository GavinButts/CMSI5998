import os
import pandas as pd
from sklearn.model_selection import train_test_split
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset

# Set Hugging Face API token
os.environ["HF_API_KEY"] = os.getenv('HF_API_KEY')

# Initialize MongoDB client using environment variable
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['news_db']
collection = db['articles']

# Load data from MongoDB
cursor = collection.find({"content": {"$exists": True}}, {"content": 1})
data = list(cursor)

# Create DataFrame
df = pd.DataFrame(data)

# Ensure content is not null
df = df.dropna(subset=['content'])

# Split data into training and testing sets
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("PY007/TinyLlama-1.1B-Chat-v0.1")
model = AutoModelForCausalLM.from_pretrained("PY007/TinyLlama-1.1B-Chat-v0.1")

# Tokenize the data
def tokenize_function(examples):
    return tokenizer(examples["content"], truncation=True, padding="max_length", max_length=512)

# Create Hugging Face datasets
train_dataset = Dataset.from_pandas(train_df)
test_dataset = Dataset.from_pandas(test_df)

# Apply tokenization
train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

# Remove the original 'content' column
train_dataset = train_dataset.remove_columns(["_id", "content"])
test_dataset = test_dataset.remove_columns(["_id", "content"])

# Set the format for the datasets
train_dataset.set_format("torch")
test_dataset.set_format("torch")

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# Fine-tune the model
trainer.train()

# Save the model
model.save_pretrained("./finetuned-tiny-llama")
tokenizer.save_pretrained("./finetuned-tiny-llama")
