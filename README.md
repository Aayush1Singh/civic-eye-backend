# Legal Backend API

## Overview

This project is a backend API for a legal information system that provides advanced search, document analysis, and conversational capabilities over a large corpus of Indian central acts. It is designed to power legal research tools, chatbots, and document analysis platforms.

## Features

- **Embeddings of 45+ Central Acts:**
  - The system preprocesses and embeds over 45 major Indian central acts, enabling fast and semantically rich search and retrieval.
- **Session-Based Query Resolution:**
  - Each user interaction is managed via sessions, allowing for context-aware query resolution and persistent chat history.
- **Similar Case Search:**
  - Users can search for legal cases similar to their queries, leveraging advanced embedding and retrieval techniques.
- **Document Analysis:**
  - Upload and analyze legal documents, extracting relevant information and linking it to the central acts database.
- **User Authentication & Management:**
  - Secure signup, signin, JWT-based authentication, and password reset functionality.
- **Rate Limiting & Security:**
  - Prevents abuse with session and rate management, and uses encrypted password storage.
- **Cross-Origin Support:**
  - CORS enabled for integration with modern web frontends.

## Why is it Unique?

- **Deep Legal Embedding:**
  - Unlike generic search engines, this backend uses embeddings specifically trained on Indian legal texts, providing highly relevant and context-aware results.
- **Integrated Session Management:**
  - Maintains user context across queries, enabling conversational and multi-step legal research.
- **Case Similarity Search:**
  - Goes beyond keyword search by finding semantically similar cases, aiding legal professionals in research.
- **Document-to-Act Linking:**
  - Analyzes uploaded documents and links them to relevant sections of central acts, streamlining legal analysis.

## Technologies Used

- **FastAPI:** High-performance Python web framework for building APIs.
- **MongoDB:** NoSQL database for storing users, sessions, and chat history.
- **Redis:** Used for fast session and embedding storage.
- **JWT (JSON Web Tokens):** For secure authentication.
- **Fernet (cryptography):** For password encryption.
- **PDF Processing Libraries:** For extracting and analyzing legal documents.
- **Docker:** For containerized deployment.

## Project Structure

- `main.py` — FastAPI application entry point
- `routers/` — API route handlers (sessions, chat, PDF handling)
- `services/` — Core business logic (embedding, analysis, database, LLMs)
- `models/` — Data models (users, session history)
- `all_central_acts_pdfs/` — Source PDFs of central acts
- `preprocessed_docs/` — Cropped/processed PDFs
- `processed_pages/` — Image outputs from PDF processing
- `redis_data/` — Redis persistence files
- `uploads/` — User-uploaded documents

## API Endpoints (Highlights)

- `/new_session` — Start a new user session
- `/session/query/{session_id}` — Query the system within a session
- `/session/load_chat/{session_id}` — Retrieve chat history
- `/session/get_similar/{session_id}` — Search for similar cases
- `/session/analyze/{session_id}` — Analyze uploaded documents
- `/signup`, `/signin`, `/reset_password` — User authentication endpoints

## Dependencies

See `requirements.txt` for the full list. Key dependencies include:

- `fastapi`
- `uvicorn`
- `pymongo`
- `redis`
- `cryptography`
- `PyJWT`
- `python-dotenv`
- `pdfplumber`, `PyPDF2`, or similar (for PDF processing)

## Getting Started

1. **Clone the repository**
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Create a `.env` file with your MongoDB URI, Redis config, and JWT secret key.
4. **Run the server:**
   ```
   uvicorn main:app --reload
   ```
5. **(Optional) Use Docker Compose:**
   ```
   docker-compose up --build
   ```

## License

This project is for educational and research purposes. Please check the repository for license details.
