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
        tokens = []
        for word in transcript.split():
            token = word.lower().strip(".,!?;:\"'")
            if not token:
                continue
            if len(token) == 1 and token.isalpha():
                tokens.append(token)
            elif len(token) > 1:
                tokens.append(token)
        print("[nlp_processor] FALLBACK tokens:", tokens)
        return tokens

    doc = nlp(transcript)
    tokens = []
    for token in doc:
        text = token.text.strip().lower()
        if not text:
            continue
        if len(text) == 1 and text.isalpha():
            tokens.append(text)
        elif not token.is_punct and not token.is_space:
            tokens.append(token.lemma_.lower())
    print("[nlp_processor] Processed tokens:", tokens)
    return tokens
