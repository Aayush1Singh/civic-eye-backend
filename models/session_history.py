from datetime import datetime
from uuid import uuid4

from mongoengine import (
    connect, Document, EmbeddedDocument,
    StringField, EmailField, DateTimeField, ListField,
    EmbeddedDocumentField, ReferenceField, UUIDField
)
class DocumentMeta(EmbeddedDocument):
    pdf_name  = StringField()
    num_pages = StringField()
    lang      = StringField()

class QueryItem(EmbeddedDocument):
    query     = StringField(required=True)
    response  = StringField(required=True)
    asked_at  = DateTimeField(default=datetime.utcnow)

class Session(Document):
    """
    One RAG chat session for a single PDF (or group of PDFs).

    • creator  → reference to owning User  
    • embedding_index = Redis index name (often the same as `session_id`)
    """
    meta = {
        "collection": "sessions",
        "indexes": ["session_id", "creator"]  # MongoDB indexes
    }

    session_id       = StringField(required=True, unique=True)  # UUID / ulid / etc.
    creator          = ReferenceField(User, reverse_delete_rule=2)  # CASCADE
    summary          = StringField()
    document_meta    = EmbeddedDocumentField(DocumentMeta)
    chat_history     = ListField(EmbeddedDocumentField(QueryItem))
    status           = StringField(choices=("active", "expired", "deleted"), default="active")
    embedding_index  = StringField()   # Redis index
    created_at       = DateTimeField(default=datetime.utcnow)
