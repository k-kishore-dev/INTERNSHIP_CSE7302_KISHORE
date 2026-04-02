from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import pandas as pd
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import requests

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

embed_model = SentenceTransformer('all-MiniLM-L6-v2')

documents = []
index = None


def extract_text_from_file(filepath):

    text = ""

    if filepath.endswith(".xlsx"):
        df = pd.read_excel(filepath)

        rows = []
        for _, row in df.iterrows():
            row_text = ", ".join([f"{col}: {row[col]}" for col in df.columns])
            rows.append(row_text)

        text = "\n".join(rows)

    elif filepath.endswith(".pdf"):

        reader = PdfReader(filepath)

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

    return text


def create_vector_store(text):

    global documents

    documents = [line for line in text.split("\n") if line.strip() != ""]

    embeddings = embed_model.encode(documents)

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    idx = faiss.IndexFlatL2(dimension)

    idx.add(embeddings)

    return idx


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    global index

    file = request.files["file"]

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    file.save(filepath)

    text = extract_text_from_file(filepath)

    index = create_vector_store(text)

    return jsonify({"message": "Document processed successfully"})


@app.route("/chat", methods=["POST"])
def chat():

    global index

    if index is None:
        return jsonify({"reply": "Please upload a document first."})

    query = request.json["message"]

    query_embedding = embed_model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    D, I = index.search(query_embedding, k=3)

    context = ""

    for i in I[0]:
        context += documents[i] + "\n"

    prompt = f"""
Answer the question using the context.

Context:
{context}

Question:
{query}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 120
            }
        }
    )

    answer = response.json()["response"]

    return jsonify({"reply": answer})


if __name__ == "__main__":
    app.run(debug=True)