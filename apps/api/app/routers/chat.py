"""Chat endpoint for Q&A about documents in a topic."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.topic import Topic, Node, ProcessingStatus
from app.models.user import User
from app.auth.dependencies import get_current_user_optional
from app.services.teach import FireworksClient

router = APIRouter()

_fireworks = FireworksClient()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    topic_id: str


def _build_context(topic: Topic, nodes: list[Node]) -> str:
    """Build context from topic nodes for the chat."""
    context_parts = []

    # Add topic title
    context_parts.append(f"Topic: {topic.title or 'Untitled'}")
    context_parts.append("")

    # Add node summaries (lessons)
    for node in nodes:
        if node.lesson_summary:
            context_parts.append(f"## {node.title}")
            context_parts.append(node.lesson_summary)
            if node.lesson_example:
                context_parts.append(f"Example: {node.lesson_example}")
            context_parts.append("")

    return "\n".join(context_parts)


@router.post("/{topic_id}", response_model=ChatResponse)
def chat_with_document(
    topic_id: str,
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Chat with AI about the content in a topic/learning path."""

    # Get topic
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Topic is still processing. Chat is available after processing completes."
        )

    # Get nodes with content
    nodes = db.query(Node).filter(Node.topic_id == topic_id).order_by(Node.level).all()

    # Build context from nodes
    context = _build_context(topic, nodes)

    # Build the prompt
    system_prompt = f"""You are Atlas AI, a helpful learning assistant. You help users understand the content in their learning materials.

Here is the content from the user's learning path:

{context}

Instructions:
- Answer questions based on the content above
- If the question is not related to the content, politely redirect to the topic
- Be concise but thorough
- Use examples when helpful
- If you don't know something based on the content, say so
- Respond in the same language as the user's question"""

    user_message = request.message

    try:
        # Call Fireworks AI
        response = _fireworks.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        ai_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not ai_response:
            ai_response = "I'm sorry, I couldn't generate a response. Please try again."

        return ChatResponse(
            response=ai_response,
            topic_id=topic_id,
        )

    except Exception as e:
        print(f"[Chat] Error calling Fireworks AI: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to get response from AI. Please try again."
        )
