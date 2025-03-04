import os
from app.app import app
import nltk
from app.__init__ import init_app_directories

# Download necessary NLTK data packages
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

if __name__ == '__main__':
    # Initialize application directories
    init_app_directories()
    
    print("Starting the Resume Analysis System...")
    print("Access the application at: http://127.0.0.1:5000")
    
    # Run the application
    app.run(debug=True, host='127.0.0.1', port=5000)