# # from flask import Flask, render_template, request
# # import requests

# # app = Flask(__name__)

# # @app.route("/", methods=["GET", "POST"])
# # def index():
# #     result = None
# #     input_text = ""
    
# #     if request.method == "POST":
# #         input_text = request.form.get("text", "")
# #         if input_text.strip():
# #             url = "https://api.languagetool.org/v2/check"
# #             data = {"text": input_text, "language": "en-US"}
            
# #             try:
# #                 response = requests.post(url, data=data)
# #                 response.raise_for_status()
# #                 result = response.json()
# #             except Exception as e:
# #                 result = {"error": str(e)}
    
# #     return render_template("index.html", result=result, input_text=input_text)

# # if __name__ == "__main__":
# #     app.run(debug=True)


# from flask import Flask, render_template, request
# import requests
# from supabase import create_client, Client

# app = Flask(__name__)

# # Configure Supabase client
# supabase_url = 'your_supabase_project_url'  # Replace with your Supabase URL
# supabase_key = 'your_supabase_api_key'       # Replace with your Supabase API key
# supabase: Client = create_client(supabase_url, supabase_key)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     result = None
#     input_text = ""
    
#     if request.method == "POST":
#         input_text = request.form.get("text", "")
#         if input_text.strip():
#             url = "https://api.languagetool.org/v2/check"
#             data = {"text": input_text, "language": "en-US"}
            
#             try:
#                 response = requests.post(url, data=data)
#                 response.raise_for_status()
#                 result = response.json()

#                 # Save the result to the Supabase database
#                 supabase.table('results').insert({
#                     'input_text': input_text,
#                     'language_tool_response': result
#                 }).execute()

#             except Exception as e:
#                 result = {"error": str(e)}
    
#     # Fetch all previous results from Supabase
#     previous_results = supabase.table('results').select('*').execute().data
    
#     return render_template("index.html", result=result, input_text=input_text, previous_results=previous_results)

# if __name__ == "__main__":
#     app.run(debug=True)


# from flask import Flask, render_template, request
# import requests
# from supabase import create_client, Client
# import os
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = Flask(__name__)

# # Supabase configuration (use environment variables for security)
# SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zjplzurwgipqextvgoqy.supabase.co")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpqcGx6dXJ3Z2lwcWV4dHZnb3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg2OTI1MTMsImV4cCI6MjA1NDI2ODUxM30.ZJw457O7pcPIH2wM3lq6x01RJ3RmH0Nr1QH8ymCSN4Y")
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     result = None
#     input_text = ""
#     chat_history = []

#     # Fetch chat history from Supabase (limit to last 10 entries)
#     try:
#         response = supabase.table("chat_history").select("*").order("created_at", desc=True).limit(10).execute()
#         chat_history = response.data
#     except Exception as e:
#         logger.error(f"Error fetching chat history: {e}")
#         chat_history = []

#     if request.method == "POST":
#         input_text = request.form.get("text", "").strip()
#         if input_text:
#             url = "https://api.languagetool.org/v2/check"
#             data = {"text": input_text, "language": "en-US"}

#             try:
#                 # Call LanguageTool API
#                 response = requests.post(url, data=data)
#                 response.raise_for_status()
#                 result = response.json()

#                 # Validate result before saving to Supabase
#                 if isinstance(result, dict) and "matches" in result:
#                     # Save to Supabase
#                     supabase.table("chat_history").insert({
#                         "input_text": input_text,
#                         "result": result
#                     }).execute()
#                 else:
#                     result = {"error": "Invalid response from LanguageTool API"}
#                     logger.error(f"Invalid API response: {result}")
#             except requests.exceptions.RequestException as e:
#                 result = {"error": f"LanguageTool API error: {e}"}
#                 logger.error(f"API request failed: {e}")
#             except Exception as e:
#                 result = {"error": f"An error occurred: {e}"}
#                 logger.error(f"Unexpected error: {e}")

#     return render_template("index.html", result=result, input_text=input_text, chat_history=chat_history)

# if __name__ == "__main__":
#     app.run(debug=True)

# Updated code start
from flask import Flask, render_template, request
import requests
import json
import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    input_text = ""
    new_entry = None  # New history entry from this request (if any)

    if request.method == "POST":
        input_text = request.form.get("text", "").strip()
        if input_text:
            original_input = input_text  # Save the original input text
            url = "https://api.languagetool.org/v2/check"
            data = {"text": original_input, "language": "en-US"}
            
            try:
                # Call the LanguageTool API
                response_api = requests.post(url, data=data)
                response_api.raise_for_status()
                api_response = response_api.json()
                
                # Extract only necessary fields for the chat history:
                matches = api_response.get("matches", [])
                errors_list = []
                for match in matches:
                    error_item = {
                        # Extract the error category (which contains both id and name)
                        "category": match.get("rule", {}).get("category", {}),
                        "message": match.get("message"),
                        # Use the first suggestion if available; otherwise, None
                        "suggestion": (match.get("replacements", [{}])[0].get("value")
                                       if match.get("replacements") else None),
                        "context": match.get("context", {}).get("text")
                    }
                    errors_list.append(error_item)
                error_count = len(errors_list)
                # Clear the text area after a successful API call
                input_text = ""
            except Exception as e:
                api_response = {"error": str(e)}
                errors_list = []
                error_count = 0

            # Build a history entry with only the necessary fields.
            new_entry = {
                "input_text": original_input,
                "error_count": error_count,
                "errors": errors_list,
                "timestamp": datetime.datetime.now().isoformat()
            }
            # We still pass the full API response to show details in the current request result.
            result = api_response

    # Pass new_entry as JSON (or an empty list if no new entry) to the UI.
    history_entry = json.dumps([new_entry]) if new_entry else json.dumps([])
    return render_template("index.html", result=result, input_text=input_text, history_entry=history_entry)

if __name__ == "__main__":
    app.run(debug=True)