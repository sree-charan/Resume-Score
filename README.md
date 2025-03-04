# Resume Analysis and Scoring System

A web application that analyzes and scores resumes against job descriptions using Natural Language Processing techniques. This tool helps recruiters and hiring managers quickly identify the best candidates for a position based on skills, experience, and education match.

## Features

- **Resume Parsing**: Extract key information from resumes (PDF, DOCX, TXT)
- **Intelligent Analysis**: Match resumes against job descriptions
- **Automated Scoring**: Score resumes based on various factors like skills match, experience, education, etc.
- **Bulk Upload**: Process multiple resumes at once
- **Dashboard**: View analysis results with sortable tables and different visualization options
- **Export Results**: Export analysis results to CSV format

## Installation

### Prerequisites

- Python 3.8+ 
- pip (Python package manager)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/resume-analysis-system.git
   cd resume-analysis-system
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python run.py
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```

2. Access the web interface in your browser at:
   ```
   http://localhost:5000
   ```

3. Create job descriptions or upload resumes for analysis.

## Project Structure

```
├── app/
│   ├── models/          # Database models
│   ├── static/          # Static assets (CSS, JavaScript)
│   ├── templates/       # HTML templates
│   ├── uploads/         # Uploaded files storage
│   └── utils/           # Utility modules
├── config.py            # Application configuration
└── run.py               # Application entry point
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy, NLTK, scikit-learn
- **Frontend**: Bootstrap, JavaScript, HTML/CSS
- **Document Processing**: PyPDF2, python-docx
- **NLP**: NLTK for natural language processing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- NLTK community for natural language processing tools
- Flask team for the web framework
- Bootstrap team for the frontend framework
=======

