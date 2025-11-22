# Overview

This is an AI-powered resume modification tool built with Streamlit. The application allows users to upload PDF resumes, extracts text content from them using pdfplumber, and leverages OpenAI's gpt-4o-mini model to provide AI-assisted resume editing and improvement suggestions tailored to specific job descriptions (JD). The tool features a dual-column interface design for input and output areas.

## Current Status (Last Updated: 2025-11-22)
✅ **MVP Complete** - All core features implemented and tested:
- PDF file upload with pdfplumber text extraction
- Two-column layout (left: input, right: output)
- Job description (JD) text input
- OpenAI gpt-4o-mini integration for resume analysis
- AI-generated resume modification suggestions in Markdown format
- Comprehensive error handling for missing files, empty PDFs, and invalid inputs

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web framework
- **Layout**: Wide layout with dual-column design (left for input, right for output)
- **UI Components**: File uploader, text areas, expandable sections for content preview
- **Rationale**: Streamlit was chosen for its simplicity in creating data-driven web applications with minimal frontend code, enabling rapid prototyping and deployment

## Backend Architecture
- **Processing Flow**: 
  1. PDF upload handling
  2. Text extraction from PDF
  3. AI-powered text processing via OpenAI API
  4. Results presentation
- **PDF Processing**: pdfplumber library for reliable text extraction from PDF documents
- **Rationale**: Server-side processing in Python allows for seamless integration with AI services and PDF manipulation libraries

## Authentication & Security
- **API Key Management**: OpenAI API key stored in environment variables (`OPENAI_API_KEY`)
- **Rationale**: Environment variables prevent hardcoding sensitive credentials and support different keys across development/production environments

## Design Patterns
- **Single-page application**: All functionality contained in one Streamlit app
- **Stateless processing**: Each upload triggers fresh processing without persistent state
- **Pros**: Simple to understand and maintain, fast iteration
- **Cons**: Limited scalability for multiple concurrent users, no session persistence

# External Dependencies

## Third-Party Libraries
- **Streamlit**: Web application framework for creating the user interface
- **pdfplumber**: PDF text extraction library for parsing uploaded resume files
- **OpenAI Python SDK**: Client library for interacting with OpenAI's language models

## External Services
- **OpenAI API**: Provides AI capabilities for resume analysis and modification suggestions
  - Requires valid API key for authentication
  - Used for natural language processing tasks

## Configuration Requirements
- **Environment Variables**:
  - `OPENAI_API_KEY`: Required for OpenAI API authentication

## File Processing
- **Supported Format**: PDF files only
- **Processing**: Page-by-page text extraction with concatenation