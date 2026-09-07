import os
import json
import pymupdf as fitz
import csv
import sys

fitz.TOOLS.mupdf_display_errors(False)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TESTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "evaluation")

def count_words(text):
    return len(text.split())

def main():
    total_words = 0
    file_word_counts = {}
    northbridge_count = 0
    pdf_pages = {}
    pdf_extractable = True
    
    for filename in os.listdir(DATA_DIR):
        filepath = os.path.join(DATA_DIR, filename)
        if filename.endswith(".pdf"):
            doc = fitz.open(filepath)
            text = ""
            pdf_pages[filename] = len(doc)
            for i, page in enumerate(doc):
                page_text = page.get_text()
                text += page_text
                
                if len(page_text.strip()) == 0:
                    print(f"ERROR: PDF {filename} page {i+1} yielded no text")
                    pdf_extractable = False
                    
            northbridge_count += text.lower().count("northbridge")
            words = count_words(text)
            total_words += words
            file_word_counts[filename] = words
            
        elif filename.endswith(".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                northbridge_count += text.lower().count("northbridge")
                words = count_words(text)
                total_words += words
                file_word_counts[filename] = words
                
        elif filename.endswith(".csv"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                northbridge_count += text.lower().count("northbridge")
                words = count_words(text)
                total_words += words
                file_word_counts[filename] = words

    print("=== CORPUS CONTENT REPORT ===")
    for f, c in file_word_counts.items():
        if f.endswith(".pdf"):
            print(f"{f}: {c} words | {pdf_pages[f]} pages")
        else:
            print(f"{f}: {c} words")
            
    print("-" * 30)
    print(f"TOTAL CORPUS WORDS: {total_words}")
    print(f"ALL PDFs FULLY EXTRACTABLE: {pdf_extractable}")
    print(f"ACCIDENTAL 'NORTHBRIDGE' REFERENCES: {northbridge_count}")
        
    print("\n=== CONTRADICTIONS CHECK ===")
    registry_path = os.path.join(DATA_DIR, "contradictions.json")
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Registered Contradictions: {len(data)}")
            for c in data:
                print(f" - [{c['contradiction_id']}] {c['topic'].upper()}")
                print(f"   Source A ({c['source_A']}): {c['clause_A']}")
                print(f"   Source B ({c['source_B']}): {c['clause_B']}\n")
    else:
        print("ERROR: Contradictions registry not found.")
        
    print("=== UNANSWERABLE QUESTIONS CHECK ===")
    unanswerable_path = os.path.join(TESTS_DIR, "unanswerable_questions.json")
    if os.path.exists(unanswerable_path):
        with open(unanswerable_path, "r", encoding="utf-8") as f:
            q_data = json.load(f)
            print(f"Total Unanswerable Questions: {len(q_data)}")
    else:
        print("ERROR: Unanswerable Questions not found.")
        
if __name__ == "__main__":
    main()
