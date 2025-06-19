# =========================
# File: gpt_module.py
# Purpose: Handle AI responses using Google Gemini
# =========================

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def ask_gpt(prompt):
    """
    Send a prompt to Gemini and get a response
    """
    try:
        # Create the model
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Enhanced prompt for barber shop context
        enhanced_prompt = f"""
        You are an AI assistant for Elite Barber Shop. You are professional, friendly, and knowledgeable about barbering and grooming services.
        
        Context: This is a barber shop booking system. Customers can book appointments, ask about services, get grooming advice, and general questions.
        
        Available services:
        - Classic Haircut ($25)
        - Fade Cut ($30)
        - Beard Trim ($15)
        - Mustache Trim ($10)
        - Hot Towel Shave ($35)
        - Hair Wash & Style ($40)
        - Eyebrow Trim ($12)
        - Hair Treatment ($50)
        - Full Service Package ($65)
        
        Business hours: Monday-Friday 9AM-6PM, Saturday 9AM-5PM, Sunday Closed
        
        If customers ask about booking, mention they can type 'book' to start the booking process.
        If they ask about availability, mention they can type 'view slots' to see available times.
        
        Customer question: {prompt}
        
        Provide a helpful, professional response. Keep responses concise but informative.
        """
        
        # Generate response
        response = model.generate_content(enhanced_prompt)
        
        return response.text
        
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please try again in a moment, or type 'book' to make an appointment."

def ask_gpt_with_context(prompt, context=""):
    """
    Ask Gemini with additional context
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        full_prompt = f"""
        You are an AI assistant for Elite Barber Shop.
        
        Additional context: {context}
        
        Customer question: {prompt}
        
        Provide a helpful, professional response about barbering services, grooming tips, or general assistance.
        """
        
        response = model.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return "I'm sorry, I'm experiencing technical difficulties. Please try again later."

def get_booking_suggestion(customer_request):
    """
    Generate smart booking suggestions based on customer request
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""
        You are an AI assistant for Elite Barber Shop. A customer is asking about booking.
        
        Customer request: {customer_request}
        
        Based on their request, suggest the most appropriate service from our menu:
        - Classic Haircut ($25) - Traditional styling
        - Fade Cut ($30) - Modern fade styles
        - Beard Trim ($15) - Professional grooming
        - Mustache Trim ($10) - Precise shaping
        - Hot Towel Shave ($35) - Luxury experience
        - Hair Wash & Style ($40) - Complete service
        - Eyebrow Trim ($12) - Detail grooming
        - Hair Treatment ($50) - Nourishing care
        - Full Service Package ($65) - Complete grooming experience
        
        Provide a brief, helpful response suggesting the best service(s) for their needs.
        End with "Type 'book' to start your appointment booking!"
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating booking suggestion: {e}")
        return "I'd be happy to help you choose the right service! Type 'book' to start your appointment booking."

def get_grooming_advice(question):
    """
    Provide grooming and styling advice
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""
        You are a professional barber AI assistant with expertise in men's grooming and styling.
        
        Customer question about grooming/styling: {question}
        
        Provide helpful, professional advice about:
        - Hair styling techniques
        - Beard grooming tips
        - Product recommendations
        - Maintenance advice
        - Styling trends
        
        Keep the response practical and easy to follow. End with a suggestion to visit Elite Barber Shop for professional service.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error getting grooming advice: {e}")
        return "I'd love to help with grooming advice! For the best personalized tips, visit Elite Barber Shop where our experts can assess your specific needs."

def handle_complaint_or_feedback(message):
    """
    Handle customer complaints or feedback professionally
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""
        You are a customer service AI for Elite Barber Shop. Handle this customer message professionally:
        
        Customer message: {message}
        
        Respond with empathy and professionalism. If it's a complaint:
        - Acknowledge their concern
        - Apologize if appropriate
        - Offer a solution or next steps
        - Maintain a helpful tone
        
        If it's positive feedback:
        - Thank them genuinely
        - Encourage them to return
        - Mention they can book again easily
        
        Keep the response warm and professional.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error handling feedback: {e}")
        return "Thank you for your feedback! We truly appreciate hearing from our customers. If you need any assistance, please let us know."

# Test function
def test_gemini_connection():
    """
    Test if Gemini API is working
    """
    try:
        response = ask_gpt("Hello, this is a test message.")
        print("✅ Gemini API connection successful!")
        print(f"Test response: {response}")
        return True
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection when running this file directly
    test_gemini_connection()