# Data15Group3
Orchestration repo: https://github.com/samrere/samrere-Data15Group3-Orchestration  
Data Modeling repo: https://github.com/datagroup-dbt/datagroup-dbt  
RAG repo: https://github.com/samrere/Data15Group3-RAG  

## Standard
### Branching:  
[prefix]/[ticket-number]-[task-name]  
e.g.  
feat/CP-32-add-user-login-page  
fix/CP-35-fix-new-user-registratino-error  
### Commits:  
Make sure each pull request only have one commit,  
and commit message follow the below pattern:  
[prefix]:[task name]  
[task description]  
Resolve [ticket-number]  
e.g.  
```
feat: add user registration page

Added (static) user registration page:
- implemented registration form;
- implemented registration page as per ui;
- added unit tests for registration page and related components.

Resolve CP-32
```

