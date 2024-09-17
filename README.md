# AtaxAId

AtaxAId is an intelligent system designed to assist clinicians by extracting and translating relevant clinical terms from medical reports into standardized Human Phenotype Ontology (HPO) terms.

# Installation

```
conda env create -f environment.yml
conda activate ataxaid
pip install -r requirements.txt
python -c "import nltk;nltk.download('punkt_tab');"
```

# Usage

Launch the web server with `python src/webapp.py`. Navigate to [http://localhost:3458/](http://localhost:3458/) to use the app.

# Citing the paper
Pending reference