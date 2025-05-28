# models.py
from datetime import datetime
from uuid import uuid4

from mongoengine import (
    connect, Document, EmbeddedDocument,
    StringField, EmailField, DateTimeField, ListField,
    EmbeddedDocumentField, ReferenceField, UUIDField
)

class User(Document):
    """
    A registered user.

    • email is unique  
    • password should be stored **hashed** (BCrypt/Argon2, never plain text!)
    """
    meta = {"collection": "users"}

    uuid      = UUIDField(default=uuid4, unique=True)   # public ID
    name      = StringField(required=True)
    email     = EmailField(required=True, unique=True)
    password  = StringField(required=True)              # store a hash
    created_at = DateTimeField(default=datetime.utcnow)

    # Convenience: MongoEngine automatically adds `sessions` back-reference
    #   if we define `reverse_delete_rule` below on Session.creator

