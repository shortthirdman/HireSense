from django import forms
from .models import Resume

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['name', 'email', 'resume_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
        self.fields['resume_file'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf'
        })

    def clean_resume_file(self):
        resume_file = self.cleaned_data.get('resume_file')
        if resume_file:
            if not resume_file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if resume_file.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError('File size must be under 2MB.')
        return resume_file