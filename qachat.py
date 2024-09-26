from dotenv import load_dotenv
import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

# Load environment variables
load_dotenv()

# Configure the Gemini model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Flask application setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Function to get Gemini AI response
def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response

# Define Flask route for getting a response
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    response_chunks = get_gemini_response(question)

    response_text = "".join([chunk.text for chunk in response_chunks])

    return jsonify({
        "question": question,
        "response": response_text
    })

# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
