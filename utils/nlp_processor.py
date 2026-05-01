import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("[nlp_processor] ERROR: spaCy model not found.")
    print("Run: python -m spacy download en_core_web_sm")
    nlp = None

def process_text(transcript: str) -> list[str]:
    """
    Tokenizes transcript, removes stop words and punctuation,
    returns lemmatized lowercase string list.
    """
    if not transcript or not transcript.strip():
        print("[nlp_processor] WARNING: empty transcript received")
        return []

    if nlp is None:
        # Fallback: naive whitespace split if spaCy unavailable
        tokens = [w.lower().strip(".,!?;:\"'") for w in transcript.split()]
        tokens = [t for t in tokens if len(t) > 1]
        print("[nlp_processor] FALLBACK tokens:", tokens)
        return tokens

    doc = nlp(transcript)
    tokens = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.lemma_.strip()) > 0
    ]
    print("[nlp_processor] Processed tokens:", tokens)
    return tokens
