# CivicLens AI

## Team Members

1. **Pathan Huzaifkhan** - BT24S05F006
2. **Shivam Atram** - BT24S05F009

**Academic Year:** 2026-27  
**Institute:** Government College of Engineering, Chhatrapati Sambhaji Nagar

## Project Title

**CivicLens AI - Government Information Assistant with Scheme Discovery, PDF Q&A and OCR**

## Problem Statement

Students and citizens often find it difficult to identify suitable government schemes, understand eligibility-related information, and interpret documents such as EWS, hostel, income, caste, and domicile certificates. Information is distributed across portals, notifications, and scanned PDF documents.

## Objectives

- Provide a searchable government-scheme explorer.
- Include MahaDBT education, agriculture, welfare, assistance, labour, and skill-related catalog entries.
- Suggest potential scheme matches from user profile preferences.
- Allow users to ask questions about uploaded PDF documents.
- Use OCR for scanned or image-only PDFs.
- Return page-specific evidence and responsible-use guidance.

## Proposed Solution

CivicLens AI is a React and Flask web application. It combines scheme search, profile-based discovery, a civic-information assistant, retrieval-augmented responses, PDF text extraction, and Tesseract OCR. The system supports English, Hindi, and Marathi interfaces.

The application is informational only. It does not make official eligibility decisions, verify document authenticity, approve applications, or submit applications to government portals.

## Technologies Used

- Frontend: React, Vite, React Router, CSS, Lucide React
- Backend: Python, Flask, Flask-CORS
- Retrieval: scikit-learn TF-IDF and cosine similarity
- PDF processing: PyMuPDF
- OCR: Tesseract OCR, pytesseract, Pillow
- Optional Generative AI: OpenAI-compatible chat-completion provider
- Testing: Pytest, Vite production build, browser smoke testing

## System Workflow

1. The user searches schemes, opens the guided discovery form, or uploads a PDF.
2. The Flask API validates the request and loads the relevant knowledge base.
3. TF-IDF retrieval ranks relevant scheme or document passages.
4. Scanned PDF pages are rendered and processed using Tesseract OCR.
5. The optional language model generates a grounded answer when configured.
6. Without an API key, the application returns an evidence-only answer.
7. The response includes page-specific passages, limitations, and verification guidance.

## Main Features

- Government and MahaDBT scheme directory
- Guided profile-based scheme discovery
- AI assistant for scheme and civic-information questions
- Text-based and scanned PDF question answering
- EWS, hostel, income, caste, scholarship, and related document hints
- Page-numbered evidence
- English, Hindi, and Marathi interface support
- Temporary PDF processing and cleanup
- Responsible-use safeguards

## Installation and Running

### Backend

```powershell
cd Source-Code\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Tesseract OCR must also be installed on Windows for scanned PDFs:

```powershell
winget install --id tesseract-ocr.tesseract --exact
```

### Frontend

```powershell
cd Source-Code\frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Results and Validation

- 89 scheme records available in the project catalog
- Three interface languages
- OCR verified using Tesseract 5.5.3
- 15 backend tests passed
- Frontend production build completed successfully
- PDF answers include supporting page passages

## Repository Contents

- `Source-Code/` - React frontend and Flask backend
- `PPT/` - Project presentation
- `Screenshots/` - Application screenshots
- `Demo/` - Demonstration and setup notes

## Team Contributions

### Pathan Huzaifkhan - BT24S05F006

- Project planning and requirement analysis
- Backend API and PDF/OCR workflow
- RAG retrieval and scheme recommendation logic
- Testing and documentation

### Shivam Atram - BT24S05F009

- Frontend pages and responsive interface
- Scheme explorer and guided discovery UI
- AI assistant and PDF interaction screens
- Presentation, screenshots, and demonstration preparation

## Future Scope

- Verified and automatically updated scheme notifications
- Hindi and Marathi OCR language packs
- Improved OCR for tables, dates, stamps, and handwritten fields
- Saved schemes and exportable application checklists
- Voice input, accessibility improvements, and mobile support

## References

- MahaDBT: https://mahadbt.maharashtra.gov.in/
- Aaple Sarkar: https://aaplesarkar.mahaonline.gov.in/
- Flask: https://flask.palletsprojects.com/
- React: https://react.dev/
- PyMuPDF: https://pymupdf.readthedocs.io/
- scikit-learn: https://scikit-learn.org/
- Tesseract OCR: https://tesseract-ocr.github.io/

## Demo Link

For local demonstration:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:5000/api/health`
- Chat with PDF: `http://localhost:5173/chat-pdf`
