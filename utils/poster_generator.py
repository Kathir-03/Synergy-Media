# poster_generator.py
import google.generativeai as gen
from PIL import Image
from io import BytesIO
import os
from google import genai

model = gen.GenerativeModel('gemini-2.5-flash')
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

def generate_poster(name, description, image_path):
    # Text generation
    text_prompt = f"""
    Header Options:

    Generate a header, for this product {name} for a suitable poster
    Body Content:

    Using the provided {description}, write a single, synthesized version of the body copy suitable for a poster. 
    This content must be concise and persuasive.

    Structure it with a short introductory sentence followed by bullet points.

    Crucially, the bullet points should translate the product's key features into clear, compelling benefits for the customer.

    Call to Action (CTA) Options:

    Generate a Calls to Action that is direct and action-oriented, creates urgency, or is informational.
    """
    text_response = model.generate_content(text_prompt)

    # Poster generation
    with Image.open(image_path) as img:
        poster_prompt = f"""
        Create a poster-like image for a product. The poster should feature a prominent header, 
        detailed body content derived from the provided description, and a clear Call to Action. 
        The product itself, sourced by extracting only the product element from the given image, 
        should be integrated into the poster design in a visually appealing and poster-like manner. 
        The overall aesthetic should be modern and engaging, suitable for promotional purposes.

        Use the header, body and CTA from the given text below.
        Make sure the content is accordingly to it and does not mismatch.
        {name} as the main header as this is the company/product name.
        {text_response.text}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[poster_prompt, img],
        )

    poster_text, poster_image_path = "", None
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            poster_text += part.text
        elif part.inline_data is not None:
            gen_img = Image.open(BytesIO(part.inline_data.data))
            poster_image_path = "poster.png"
            gen_img.save(poster_image_path)

    return poster_text, poster_image_path
