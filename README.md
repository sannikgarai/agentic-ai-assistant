# Agentic AI Assistant

An autonomous, multilingual, multimodal AI assistant designed to help
users understand government schemes, verify documents, retrieve
information from government PDFs, and prepare applications.

---

## Features

- Multilingual conversational AI
- Text-based interaction
- Voice input
- Speech-to-text
- Text-to-speech
- Government document RAG
- PDF processing
- OCR
- Document field extraction
- Document verification
- Eligibility checking
- Agent-based task planning
- Task decomposition
- Conversation history
- Application preparation
- Browser automation
- User approval before final submission
- Supabase authentication
- Supabase PostgreSQL
- Supabase Storage
- FAISS vector search
- Gemini LLM

---

# Project Architecture

```text
User
 │
 ▼
React + Vite
 │
 ▼
FastAPI
 │
 ├── Gemini LLM
 │
 ├── Agent
 │   ├── Planner
 │   ├── Task Decomposer
 │   ├── Workflow
 │   └── Supervisor
 │
 ├── RAG
 │   ├── PDF Loader
 │   ├── Text Extractor
 │   ├── Cleaner
 │   ├── Chunker
 │   ├── Embeddings
 │   ├── FAISS
 │   └── Retriever
 │
 ├── Documents
 │   ├── Parser
 │   ├── Classifier
 │   ├── Extractor
 │   └── OCR
 │
 ├── Verification
 │   ├── Field Matching
 │   ├── Mismatch Detection
 │   └── Eligibility Checking
 │
 ├── Voice
 │   ├── Speech-to-Text
 │   ├── Text-to-Speech
 │   ├── Language Detection
 │   └── Translation
 │
 └── Automation
     ├── Browser
     ├── Form Filler
     ├── Portal
     ├── Upload Handler
     ├── Submission
     └── Approval