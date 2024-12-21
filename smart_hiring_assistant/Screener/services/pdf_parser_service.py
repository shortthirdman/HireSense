from pdfminer.high_level import extract_text
import os

class PDFParserService:
    @staticmethod
    def extract_text_from_pdf(pdf_path):
        try:
            text = extract_text(pdf_path)
            if not text:
                raise Exception("Failed to extract text from PDF")
            # Clean the extracted text 
            text = ' '.join(text.split())
            return text[:15000]  # Limit to 15000 characters
        except Exception as e:
            print(f"PDF extraction failed: {str(e)}")
            return 'Failed to extract text from resume.'