from flask import Flask, request, jsonify
from PyPDF2 import PdfReader  # Make sure PyPDF2 is installed for PDF extraction
import os
import google.generativeai as genai
from flask_cors import CORS  # Import CORS
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Configure the Gemini model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

summaries = {}
summary_prompt = """You are a PDF summarizer. Summarize the following text 
and provide the important summary in points within 250 words: """

question_prompt = """You are an assistant that answers questions based on the provided text. 
Please provide a detailed answer to the following question: """

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_gemini_content(text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    try:
        response = model.generate_content(prompt + text)

        if response and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "No valid response generated. The content may have been blocked or no text was produced."

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Route to upload PDFs and generate summaries
def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response
@app.route("/ask", methods=["POST"])
def ask():
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
    
    
    
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    uploaded_files = request.files.getlist('files')
    
    if not uploaded_files:
        return jsonify({"error": "No files uploaded"}), 400


    for uploaded_file in uploaded_files:
        file_name = uploaded_file.filename
        document_text = extract_text_from_pdf(uploaded_file)
        summary = generate_gemini_content(document_text, summary_prompt)
        summaries[file_name] = {
            "document_text": document_text,
            "summary": summary,
            "chat_history": []
        }

    return jsonify(summaries)


# Route for asking questions based on a PDF's content
@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.json
    selected_file = data.get("file_name")
    question = data.get("question")
    
    if not selected_file or not question:
        return jsonify({"error": "File name or question is missing"}), 400

    if selected_file not in summaries:
        return jsonify({"error": f"No file with name {selected_file} found"}), 400

    document_text = summaries[selected_file]["document_text"]
    answer = generate_gemini_content(document_text, question_prompt + question)

    # Store question and answer in chat history
    summaries[selected_file]["chat_history"].append({"question": question, "answer": answer})

    return jsonify({"file_name": selected_file, "question": question, "answer": answer, "chat_history": summaries[selected_file]["chat_history"]})

# Start the Flask server
if __name__ == "__main__":
    summaries = {}  # To store PDF summaries and their chat history
    app.run(host="0.0.0.0", port=5000)
