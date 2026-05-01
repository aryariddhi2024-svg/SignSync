@echo off
echo Installing SignSync dependencies...

REM Install Python packages
pip install -r requirements.txt

REM Download spaCy model
python -m spacy download en_core_web_sm

echo Installation complete!
echo Now run: python -m streamlit run app.py