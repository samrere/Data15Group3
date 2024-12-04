from typing import Optional
import pypdf
import re


class ResumerParser:
    def process_resume(self, file_path: str) -> str:
        """Process uploaded resume and extract text"""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()

                # Basic text cleaning
                text = re.sub(r"\s+", " ", text)
                text = text.strip()

                return text
        except Exception as e:
            raise Exception(f"Error processing resume: {str(e)}")
