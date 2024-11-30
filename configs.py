
#* System Imports
import os
import sys
import textwrap

#* Camel AI Imports
from camel.agents import CriticAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from camel.toolkits.search_toolkit import SearchToolkit
from camel.toolkits.math_toolkit import MathToolkit
#* Custom Files
from personas import agents_personas as _personas
#* PDF PARSING 
import base64
import pdfplumber
from io import BytesIO
from openai import OpenAI

########################################################
#
#                      BACKEND LLM
#
########################################################

os.environ["OPENAI_API_KEY"] = "your_api_key_here"
#os.environ["GOOGLE_API_KEY"] = "your_api_key_here" # For Google Search or Google Maps Toolkit
PLATFORM = ModelPlatformType.OPENAI
MODEL = ModelType.GPT_4O
TEMPERATURE = 0.0

########################################################
#
#                      AGENTS' DETAILS
#
########################################################

NAMES = [
         "Problem Formulation Agent",
         "Breadth and Depth Agent",
         "Ambiguity and Uncertainty Agent",
         "System Complexity Agent",
         "Technical Innovation and Risk Management Agent",
         "Societal and Ethical Consideration Agent",
         "Methodology and Approach Agent",
         "Comprehensive Evaluation Agent"
         ]

ROLES = [
         "Problem Formulation Agent",
         "Breadth and Depth Agent",
         "Ambiguity and Uncertainty Agent",
         "System Complexity Agent",
         "Technical Innovation and Risk Management Agent",
         "Societal and Ethical Consideration Agent",
         "Methodology and Approach Agent",
         "Comprehensive Evaluation Agent"
         ]
__Allowed_Tools_per_Agents={
    "Problem Formulation Agent": ["search", "calculator"],
    "Breadth and Depth Agent": ["search", "calculator"],
    "Ambiguity and Uncertainty Agent": ["search", "calculator"],
    "System Complexity Agent": ["search", "calculator"],
    "Technical Innovation and Risk Management Agent": ["search", "calculator"],
    "Societal and Ethical Consideration Agent": ["search", "calculator"],
    "Methodology and Approach Agent": ["search", "calculator"],
    "Comprehensive Evaluation Agent": ["search", "calculator"]
}
PERSONAS = _personas
__TOOLS_MAP = {
    "search": SearchToolkit().get_tools(),
    "calculator": MathToolkit().get_tools(),
}

TOOLS = {}
for name in NAMES:
    allowed_tools = __Allowed_Tools_per_Agents[name]
    for tool in allowed_tools:
        if name not in TOOLS:
            TOOLS[name] = []
        TOOLS[name].extend(__TOOLS_MAP[tool])


COLORS = {
    "Problem Formulation Agent": "#a88585",
    "Breadth and Depth Agent": "#628fbd",
    "Ambiguity and Uncertainty Agent": "#038003",
    "System Complexity Agent": "#cc7e31",
    "Technical Innovation and Risk Management Agent": "#010e3b",
    "Societal and Ethical Consideration Agent": "#ff99cc",
    "Methodology and Approach Agent": "#6c8c4c",
    "Comprehensive Evaluation Agent": "#556B2F"
}


########################################################
#
#                  PROJECT HANDLING
#
########################################################
def extract_text_form_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

PDF_PATH = ""
DETAILS = ""
PROJECT = ""

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_image(base64_image):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this image?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content

def extract_text_with_images_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        full_text = ''
        
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            full_text += f"\n\n--- Page {page_num} ---\n{text}\n"
            for image_index, image in enumerate(page.images, start=1):
                x0, top, x1, bottom = image['x0'], image['top'], image['x1'], image['bottom']
                cropped_image = page.within_bbox((x0, top, x1, bottom)).to_image()
                image_bytes = BytesIO()
                cropped_image.save(image_bytes, format='PNG')
                base64_image = encode_image(image_bytes.getvalue())
                image_description = analyze_image(base64_image)
                full_text += f"\n\n[Image {image_index} on Page {page_num}]: {image_description}\n"
    
    return full_text

#Folder to save the agents' responses on the proposal as a pdf file
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)


########################################################
#
#                  USER INTERFACE
#
########################################################

TITLE_HTML = """<h1 style="text-align: center; background-color:#f8b195; color: #FFFFFF; font-family: Arial, sans-serif; margin-top:10px; margin-bottom:10px; padding-top:5px; padding-bottom:5px; border-radius:10px;">
                Multi-Agents Powered Senior Design Project Co-Pilot
            </h1>"""
AGENTS_RESPONSE_SECTION_TITLE = """<h2 style="text-align: center; background-color:#c06c84; color: #FFFFFF; font-family: Arial, sans-serif; margin-top:10px; margin-bottom:20px; padding-top:5px; padding-bottom:5px; border-radius:10px;">
                Multi-Agent System Responses and Scores
            </h2>"""
INPUT_SECTION_TITLE = """<h2 style="text-align: center; background-color:#c06c84; color: #FFFFFF; font-family: Arial, sans-serif; margin-top:10px; margin-bottom:20px; padding-top:5px; padding-bottom:5px; border-radius:10px;">
                Input Section
            </h2>"""
METRICS_TITLE = """<h2 style="text-align: center; background-color:#c06c84; color: #FFFFFF; font-family: Arial, sans-serif; margin-top:10px; margin-bottom:20px; padding-top:5px; padding-bottom:5px; border-radius:10px;">
                NLP-based Scores
            </h2>"""
Badges_CSS = """

#metrics-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}

.badge {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    width: 300px;
    background-color: #1c1c1e; 
    color: #ffffff; 
    padding: 20px;
    border-radius: 15px; 
    font-family: Arial, sans-serif;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    margin: 10px;
    cursor: default; 
    transition: transform 0.3s ease;
}
.badge:hover {
    transform: translateY(-10px); 
}

.badge h3 {
    display: flex;
    align-items: center;
    gap: 5px; 
    font-size: 18px;
    font-weight: bold;
    margin: 10px 0 5px;
    color: #ffffff;
}

.badge p {
    font-size: 14px;
    color: #FDFBD4; 
    margin: 5px 0 0;
}

.Lexical:hover, .Average:hover, .Clause:hover, .Flesch:hover {
    background-color: #1c1c1e; 
}
.Lexical{
    background-color: MediumSeaGreen;
}
.Average{
    background-color: salmon;
}
.Clause{
    background-color: darkblue;
}
.Flesch{
    background-color: tomato;
}

""" 
Badges_HTML = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<div id="metrics-badges">
                <div class="badge Lexical">
                    <h3><i class="fas fa-link"></i> Lexical Cohesion</h3>
                    <p>Score: {lexical_cohesion_score}</p>
                    <p>Measures thematic consistency by analyzing word repetition or related terms, indicating how well the content in the proposal is built on multiple ideas. Scores range from 0 (no cohesion) to 1 (full thematic consistency).</p>
                </div>
                <div class="badge Clause">
                    <h3><i class="fas fa-stream"></i> Clause Density</h3>
                    <p>Score: {clause_density_score}</p>
                    <p>Captures sentence complexity by measuring clauses per sentence, reflecting layered perspectives. Scores range from 1 (simple, single-idea sentences) to 3+ (highly complex, multi-idea sentences)</p>
                </div>
                <div class="badge Flesch">
                    <h3><i class="fas fa-book-reader"></i> Flesch-Kincaid</h3>
                    <p>Score: {flesch_kincaid_score}</p>
                    <p>Estimates readability, indicating the U.S. grade level needed to understand the text for first time. An ideal range balancing accessibility and sophistication (0–16 scale) for bachelor's-level academic purposes.</p>
                </div>
                <div class="badge Average">
                    <h3><i class="fas fa-text-width"></i> Avg Sentence Length</h3>
                    <p>Score: {avg_sentence_length_score}</p>
                    <p>Indicates structural complexity and content depth. Shorter sentences enhance readability, while longer ones may reflect richer perspectives but harder to follow.</p>
                </div>
            </div>
"""
