ANALYSIS_PROMPT = """
Analyse the following resume and job matches

Resume:
{resume_text}

Relevant jobs:
{relevant_jobs}

User questions:
{question}

Please provde:
1. Analysis of match between resume and jobs
2. Specific suggestions for resume improvement for each job
3. Key points to emphasise in cover letter for each job
4. Any other relevant career advice

Focus on the user's specific question while incorporating these elements
"""