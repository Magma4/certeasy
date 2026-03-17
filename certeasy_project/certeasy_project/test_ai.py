import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

@csrf_exempt
def generate_ai_content(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        topic = data.get('topic', 'General Knowledge')
        content_type = data.get('type', 'flashcards') # flashcards or quiz
        count = data.get('count', 5)

        # Check if OpenAI API key is configured
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key == "mock":
            # Return mock data
            if content_type == 'flashcards':
                mock_data = {
                    "flashcards": [
                        {"question": f"What is the main concept of {topic}?", "answer": f"The core principle relates to understanding {topic} fundamentals."},
                        {"question": "How does this apply in practice?", "answer": "It is used daily in professional environments."},
                        {"question": "What is a key term?", "answer": "Definition of the key term."}
                    ]
                }
            else:
                mock_data = {
                    "quiz": [
                        {
                            "question": f"Which of the following describes {topic}?",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Option A"
                        }
                    ]
                }
            return JsonResponse(mock_data)

        # Use actual OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"Generate {count} {content_type} about {topic}. Format the output as JSON."
        if content_type == 'flashcards':
            prompt += ' The JSON should have a key "flashcards" containing an array of objects with "question" and "answer" keys.'
        else:
            prompt += ' The JSON should have a key "quiz" containing an array of objects with "question", an array of 4 "options", and the "correct_answer" string.'

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert tutor creating study materials. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def transcribe_audio(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        audio_file = request.FILES['audio']

        # Check if OpenAI API key is configured
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key or api_key == "mock":
            return JsonResponse({
                'text': "This is a mock transcription of the recorded lecture. In a production environment with an OpenAI API key, this would be the actual transcribed text from your audio file.",
                'summary': "Mock summary: A lecture recording was processed."
            })

        client = OpenAI(api_key=api_key)

        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        try:
            # Transcribe with Whisper
            with open(temp_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )

            text = transcript.text

            # Generate summary
            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize the following lecture transcription in a few bullet points."},
                    {"role": "user", "content": text}
                ]
            )

            summary = summary_response.choices[0].message.content

            return JsonResponse({
                'text': text,
                'summary': summary
            })

        finally:
            os.unlink(temp_path)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

import PyPDF2

@csrf_exempt
def extract_pdf_text(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        if 'pdf' not in request.FILES:
            return JsonResponse({'error': 'No PDF file provided'}, status=400)

        pdf_file = request.FILES['pdf']

        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        # Only read up to the first 5 pages to limit text length
        num_pages = min(len(pdf_reader.pages), 5)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"

        return JsonResponse({
            'text': text[:5000] # Limiting to 5000 chars to avoid massive prompts
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
