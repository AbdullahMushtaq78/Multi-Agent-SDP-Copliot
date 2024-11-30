import nltk
import textstat
import spacy
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter

# Ensure necessary resources are downloaded
nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")

# Lexical Cohesion Metric
def lexical_cohesion(text):
    tokens = word_tokenize(text.lower())
    word_freq = Counter(tokens)
    return sum(1 for count in word_freq.values() if count > 1) / len(word_freq)

# Syntactic Complexity
def syntactic_complexity(text):
    sentences = sent_tokenize(text)
    avg_sentence_length = sum(len(word_tokenize(sent)) for sent in sentences) / len(sentences)
    clause_density = sum(1 for sent in sentences for token in nlp(sent) if token.dep_ in {"ccomp", "advcl"}) / len(sentences)
    return avg_sentence_length, clause_density

# Readability Scores
def readability_scores(text):
    return textstat.flesch_kincaid_grade(text)

# Run Metrics on all files
def evaluate_documents_nlp(Project_Details):
    # Calculating metrics
    lexical_score = lexical_cohesion(Project_Details)
    avg_sentence_length, clause_density = syntactic_complexity(Project_Details)
    flesch_kincaid = readability_scores(Project_Details)
    
    # Storing and returning the results
    return {
        "Lexical Cohesion": round(lexical_score, 2),  # Round to 2 decimal places
        "Average Sentence Length": round(avg_sentence_length, 2),  # Round to 2 decimal places
        "Clause Density": round(clause_density, 2)*10,  # Round to 2 decimal places
        "Flesch-Kincaid": int(flesch_kincaid),  # Convert to integer
    }



