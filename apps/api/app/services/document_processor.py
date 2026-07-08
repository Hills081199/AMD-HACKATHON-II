"""
Document processing service.
Extracts text from documents and generates mastery tree using OpenAI or Gemini AI.
"""
import os
import json
import re
from typing import List, Dict, Any
from datetime import datetime

from openai import OpenAI

# Document extraction libraries
import fitz  # PyMuPDF for PDF
from pptx import Presentation  # python-pptx for PPTX
from docx import Document as DocxDocument  # python-docx for DOCX


# Load configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from PDF file."""
    text_parts = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        doc.close()
    except Exception as e:
        raise Exception(f"Failed to extract PDF: {str(e)}")
    return "\n\n".join(text_parts)


def extract_text_from_pptx(file_path: str) -> str:
    """Extract text content from PowerPoint file."""
    text_parts = []
    try:
        prs = Presentation(file_path)
        for slide_num, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)
            if slide_text:
                text_parts.append(f"[Slide {slide_num + 1}]\n" + "\n".join(slide_text))
    except Exception as e:
        raise Exception(f"Failed to extract PPTX: {str(e)}")
    return "\n\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from Word document."""
    text_parts = []
    try:
        doc = DocxDocument(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
    except Exception as e:
        raise Exception(f"Failed to extract DOCX: {str(e)}")
    return "\n\n".join(text_parts)


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from a document based on its type."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "pptx":
        return extract_text_from_pptx(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


MASTERY_TREE_PROMPT = """You are an expert educational curriculum designer. Analyze the following learning materials and create a structured mastery tree (skill tree / learning path).

## Input Documents:
{documents}

## Your Task:
1. Identify the main topic/subject from the documents
2. Extract key concepts and skills that need to be learned
3. Determine prerequisite relationships between concepts
4. Create a dependency graph where:
   - Each node is a concept/skill
   - Edges represent "must learn X before Y" relationships
   - Nodes are organized into levels (0 = foundational, higher = more advanced)

## Output Format:
Return a JSON object with this exact structure:
{{
  "topic": "Main topic title",
  "nodes": [
    {{
      "id": "n1",
      "title": "Concept Name",
      "concept_key": "concept_name_snake_case",
      "level": 0,
      "prerequisites": [],
      "lesson": {{
        "summary": "2-3 sentence explanation of this concept",
        "real_world_example": "A practical example of how this concept is used"
      }},
      "quiz": {{
        "pass_threshold": 0.7,
        "questions": [
          {{
            "id": "q1",
            "type": "mcq",
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer_index": 0
          }}
        ]
      }},
      "sources": [
        {{"doc_id": "doc_001", "title": "Document name", "page": 1}}
      ]
    }}
  ],
  "edges": [
    {{"source": "n1", "target": "n2"}}
  ]
}}

## Requirements:
- Create 5-15 nodes depending on content complexity
- Each node should have 1-3 quiz questions
- Ensure no circular dependencies
- Level 0 nodes have no prerequisites
- Higher level nodes depend on lower level nodes
- Reference specific document pages in sources when possible
- Make quiz questions directly answerable from the content

Return ONLY valid JSON, no markdown formatting or code blocks."""


def generate_mastery_tree_openai(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate a mastery tree from extracted document contents using OpenAI.

    Args:
        documents: List of dicts with 'filename' and 'content' keys

    Returns:
        Mastery tree structure with nodes and edges
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    # Format documents for prompt
    doc_text = ""
    for i, doc in enumerate(documents):
        doc_text += f"\n### Document {i+1}: {doc['filename']}\n"
        doc_text += doc['content'][:50000]  # Limit content per doc
        doc_text += "\n"

    prompt = MASTERY_TREE_PROMPT.format(documents=doc_text)

    # Call OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert educational curriculum designer. Always respond with valid JSON only, no markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=8192,
        response_format={"type": "json_object"}
    )

    # Parse response
    response_text = response.choices[0].message.content.strip()

    # Clean up response if wrapped in code blocks
    if response_text.startswith("```"):
        response_text = re.sub(r'^```json?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)

    try:
        tree_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}\nResponse: {response_text[:500]}")

    # Validate structure
    if "nodes" not in tree_data:
        raise ValueError("Generated tree missing 'nodes' field")
    if "edges" not in tree_data:
        tree_data["edges"] = []
    if "topic" not in tree_data:
        tree_data["topic"] = "Untitled Topic"

    return tree_data


def generate_mastery_tree(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Generate a mastery tree from extracted document contents.
    Uses OpenAI by default, can switch to Gemini via LLM_PROVIDER env var.
    """
    # Always use OpenAI for now (can add Gemini back later if needed)
    return generate_mastery_tree_openai(documents)


def calculate_node_positions(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """
    Calculate x,y positions for nodes based on their level and connections.
    """
    # Group nodes by level
    levels = {}
    for node in nodes:
        level = node.get("level", 0)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)

    # Position nodes
    y_spacing = 140
    x_spacing = 200

    for level, level_nodes in levels.items():
        y = level * y_spacing
        total_width = (len(level_nodes) - 1) * x_spacing
        start_x = -total_width / 2

        for i, node in enumerate(level_nodes):
            node["position"] = {
                "x": start_x + i * x_spacing,
                "y": y
            }

    return nodes


async def process_documents(topic_id: str, file_paths: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Main entry point for document processing.

    Args:
        topic_id: UUID of the topic
        file_paths: List of dicts with 'path', 'filename', 'file_type' keys

    Returns:
        Complete mastery tree data
    """
    # Extract text from all documents
    documents = []
    for file_info in file_paths:
        try:
            content = extract_text(
                file_info['path'],
                file_info['file_type']
            )
            documents.append({
                'filename': file_info['filename'],
                'content': content,
                'doc_id': f"doc_{len(documents)+1:03d}"
            })
        except Exception as e:
            print(f"Warning: Failed to extract {file_info['filename']}: {e}")

    if not documents:
        raise ValueError("No documents could be processed")

    # Generate mastery tree
    tree_data = generate_mastery_tree(documents)

    # Calculate positions
    tree_data["nodes"] = calculate_node_positions(
        tree_data["nodes"],
        tree_data["edges"]
    )

    # Add metadata
    tree_data["topic_id"] = topic_id
    tree_data["generated_at"] = datetime.utcnow().isoformat() + "Z"
    tree_data["document_count"] = len(documents)

    return tree_data
