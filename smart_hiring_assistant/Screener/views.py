from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.

from .forms import ResumeUploadForm
from .services.openai_service import OpenAIService
from .services.rag_service import RAGService
from .services.sendgrid_service import SendGridService
from django.conf import settings
import logging
from pdfminer.high_level import extract_text
import re
import os
from datetime import datetime

# Configure log and load recruiter email
logger = logging.getLogger(__name__)
RECRUITER_EMAIL = os.getenv('RECRUITER_EMAIL')

def upload_resume(request):
    """Handle resume upload and processing with enhanced evaluation capabilities."""
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Here you save the form instance
                resume = form.save()
                logger.info(f"Resume uploaded successfully for {resume.name}")
                # Initialize all the services
                try:
                    openai_service = OpenAIService()
                    rag_service = RAGService(openai_service)
                    sendgrid_service = SendGridService()
                except Exception as e:
                    logger.error(f"Failed to initialize services: {str(e)}")
                    messages.error(request, 'Service initialization failed. Please contact support.')
                    return redirect('Screener:upload_resume')
                #Must process the resume
                applicant_data = {
                    'name': resume.name,
                    'email': resume.email,
                    'resume_path': resume.resume_file.path,
                    'position_applied': resume.position_applied if hasattr(resume, 'position_applied') else 'ML Engineer'
                }
                assessment_result = screen_resume(applicant_data, rag_service, sendgrid_service)
                if assessment_result.get('success', False):
                    if assessment_result.get('meets_requirements', False):
                        message = ('Thank you for applying! Your qualifications look promising, '
                                 'and our recruitment team will be in touch shortly.')
                    else:
                        message = ('Thank you for your interest. We have carefully reviewed your application '
                                 'and will keep your resume on file for future opportunities.')
                    messages.success(request, message)
                else:
                    message = ('We encountered an issue processing your application. '
                             'Our team has been notified and will review it manually.')
                    messages.warning(request, message)
                # Store assessment details for future reference
                try:
                    store_assessment_results(resume, assessment_result)
                except Exception as e:
                    logger.error(f"Failed to store assessment results: {str(e)}")
                return redirect('Screener:upload_resume')
            except Exception as e:
                logger.error(f'Resume upload failed: {str(e)}')
                messages.error(request, 'Failed to process resume. Please try again later.')
                return redirect('Screener:upload_resume')
    else:
        form = ResumeUploadForm()
    return render(request, 'Screener/upload.html', {'form': form})


def screen_resume(applicant_data, rag_service, sendgrid_service):
    """
    Screen a resume with enhanced evaluation capabilities.
    Returns a dict with success status, detailed assessment, and scoring information.
    """
    try:
        # Extract text from PDF with on cleaning
        resume_text = extract_text_from_pdf(applicant_data['resume_path'])
        if not resume_text:
            logger.error("PDF extraction failed - empty text returned")
            return {
                'success': False,
                'error': 'Failed to extract text from resume',
                'assessment': None
            }
        # Process resume using RAG service
        assessment_result = rag_service.process_resume(resume_text)
        if not isinstance(assessment_result, dict):
            logger.error("RAG service returned invalid response format")
            return {
                'success': False,
                'error': 'Invalid assessment format',
                'assessment': None
            }
        # Logging with assessment
        qualification_status = "qualified" if assessment_result['meets_requirements'] else "not qualified"
        logger.info(f"Applicant {applicant_data['name']} assessed as {qualification_status} with detailed evaluation")
        try:
            if assessment_result['meets_requirements']:
                # Email for successful applicants with detailed assessment
                email_sent = sendgrid_service.forward_successful_applicant(
                    RECRUITER_EMAIL,
                    applicant_data,
                    format_detailed_assessment(assessment_result['detailed_assessment'])
                )
                if not email_sent:
                    logger.error(f"Failed to send recruiter email for {applicant_data['name']}")
            else:
                # Send the rejection email 
                email_sent = sendgrid_service.send_rejection_email(
                    applicant_data['email'],
                    applicant_data['name']
                )
                if not email_sent:
                    logger.error(f"Failed to send rejection email to {applicant_data['name']}")
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            # Continue to process even if email fails
        return {
            'success': True,
            'assessment': assessment_result['detailed_assessment'],
            'meets_requirements': assessment_result['meets_requirements'],
            'raw_response': assessment_result.get('raw_response', ''),
            'error': None
        }
    except Exception as e:
        logger.error(f'Resume screening error: {str(e)}')
        return {
            'success': False,
            'error': str(e),
            'assessment': None
        }


def extract_text_from_pdf(path):
    """
    Extract and clean text from a PDF file with enhanced cleaning capabilities.
    Returns cleaned text or raises an exception if extraction fails.
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF file not found at path: {path}")
        # Extract text from PDF
        text = extract_text(path)
        if not text:
            raise Exception("No text extracted from PDF")
        # Text cleaning
        # Remove extra whitespace and normalize spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove non-ASCII characters but preserve common special characters
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        # Normalize bullet points and special characters
        text = re.sub(r'[•●■◆▪]', '- ', text)
        # Fix common OCR issues
        text = text.replace('|', 'I')  # Common OCR mistake
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between camelCase
        # Remove duplicate dash indicators
        text = re.sub(r'-\s*-\s*-', '-', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Verify meaningful content
        if len(text.split()) < 10:
            raise Exception("Extracted text appears to be too short to be a valid resume")
        # Limit to 15000 characters to avoid token limits
        return text[:15000]
    except Exception as e:
        logger.error(f'PDF extraction failed for {path}: {str(e)}')
        raise Exception(f"Failed to extract text from resume: {str(e)}")


def format_detailed_assessment(assessment):
    """Format the detailed assessment for email communication."""
    try:
        formatted_text = assessment.replace('\n\n', '\n').strip()
        # Add HTML formatting for better readability
        formatted_text = f"<div style='font-family: Arial, sans-serif;'>{formatted_text}</div>"
        return formatted_text
    except Exception as e:
        logger.error(f"Failed to format assessment: {str(e)}")
        return assessment