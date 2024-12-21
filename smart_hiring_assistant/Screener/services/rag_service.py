class RAGService:
    def __init__(self, openai_service):
        self.openai_service = openai_service
        self.job_requirements = """
        Education: Bachelor's or Master's degree in computer science, engineering, mathematics, or related fields; coursework in machine learning or data science is preferred.
        Programming: 2+ years of experience with Python, R, or similar languages; proficiency in TensorFlow, PyTorch, or other ML frameworks.
        Machine Learning: 2+ years of practical experience with ML algorithms, model deployment, and optimization.
        Software Engineering: Familiarity with Git, Agile methodologies, and collaborative tools; experience in software development teams for at least 2-3 years.
        Problem-Solving: Strong analytical skills, with a track record of solving complex problems using machine learning techniques.
        Communication: Effective communicator across technical and non-technical audiences; experience working in cross-functional teams.
        Portfolio: Demonstrated projects in machine learning through work experience, academic research, or personal projects; contributions to open-source projects or participation in hackathons.
        """
    def process_resume(self, resume_text):
        try:
            context = self._combine_context(resume_text)
            assessment_response = self._generate_assessment(context)
            # Parse the assessment focusing only on the final decision
            if "OVERALL_DECISION:" not in assessment_response:
                return {
                    'detailed_assessment': "Error: Assessment response missing required format",
                    'meets_requirements': False,
                    'raw_response': assessment_response
                }
            # Split at OVERALL_DECISION: and take only the parts we need
            parts = assessment_response.split("OVERALL_DECISION:")
            if len(parts) != 2:
                return {
                    'detailed_assessment': "Error: Invalid assessment format",
                    'meets_requirements': False,
                    'raw_response': assessment_response
                }
            detailed_assessment = parts[0].strip()
            final_decision = parts[1].strip().lower()
            # Only check for exact match of 'qualified' in the final decision
            is_qualified = final_decision.strip() == 'qualified'
            return {
                'detailed_assessment': detailed_assessment,
                'meets_requirements': is_qualified,
                'raw_response': assessment_response
            }
        except Exception as e:
            print(f"RAG processing failed: {str(e)}")
            return {
                'detailed_assessment': 'Unable to complete resume assessment due to an error.',
                'meets_requirements': False,
                'raw_response': str(e)
            }
    def _combine_context(self, resume_text):
        context = f"""
        Job Requirements Analysis Guidelines:
        - Requirements listed are minimum qualifications
        - Candidates exceeding minimum requirements should be considered qualified
        - Related skills and experience should be considered equivalent
        - More years of experience than required is a positive factor
        - Different but relevant degree fields are acceptable
        - Consider the overall strength of the candidate
        Job Requirements:
        {self.job_requirements}
        Applicant's Resume:
        {resume_text}
        """
        return context
    def _generate_assessment(self, context):
        messages = [
            {
                'role': 'system',
                'content': '''You are an experienced technical recruiter evaluating candidates for a machine learning engineer position.
                Your goal is to identify qualified candidates who meet or exceed the minimum requirements, including those with equivalent or superior qualifications.
                Assessment Guidelines:
                1. Consider both direct matches and relevant equivalent qualifications
                2. More experience than required is a positive factor
                3. Related degrees and skills should be evaluated favorably
                4. Look for potential and demonstrated capability, not just exact matches
                5. Consider the candidate holistically
                Format your response as follows:
                1. Start with a detailed analysis of each requirement:
                   - Education assessment
                   - Programming experience assessment
                   - Machine learning experience assessment
                   - Software engineering experience assessment
                   - Problem-solving skills assessment
                   - Communication skills assessment
                   - Portfolio assessment
                2. Provide a summary of strengths and weaknesses
                3. End your response with exactly one of these two lines:
                   OVERALL_DECISION: qualified
                   or
                   OVERALL_DECISION: not_qualified
                A candidate should be marked as qualified if they:
                - Meet or exceed the core technical requirements (even with equivalent experience)
                - Show strong potential in required areas
                - Have demonstrated relevant skills, even if through different technologies or roles'''
            },
            {
                'role': 'user',
                'content': f"""{context}
                Please evaluate this candidate considering both direct matches and equivalent qualifications.
                For each requirement:
                1. State if it is met, exceeded, or partially met
                2. List relevant evidence from the resume
                3. Consider equivalent experience or qualifications
                4. Note any exceptional strengths
                End with exactly:
                OVERALL_DECISION: qualified
                or
                OVERALL_DECISION: not_qualified
                """
            }
        ]
        response = self.openai_service.generate_chat_completion(messages)
        return response.choices[0].message.content