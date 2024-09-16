import os
import sys
import spacy

PROJ_DIR = os.path.realpath(os.path.dirname(os.path.abspath('')))
sys.path.append(os.path.join(PROJ_DIR,'src'))
import ataxaid

ataxaid.NER_TYPE = 'en_core_sci_scibert'

full_path = '/Users/paula/Library/CloudStorage/OneDrive-UniversidadedaCoruña/TESIS/PAPERS/paper1/TXT_informes_revisados/1.txt'
print(full_path)

print(f'Extracting entities from {full_path}...')
entities, _ = ataxaid.extract_entities_from_file(full_path)

nlp_model = spacy.load("en_ner_bionlp13cg_md")

print(f'Las entidades extraídas por {ataxaid.NER_TYPE} con negaciones son:')
for element in entities:
    negated = "NEGATED" if element._.negex else ""
    doc = nlp_model(element.text)
    other_tag = ''
    if len(doc.ents) > 0:
        other_tag = doc.ents[0].label_ + ('+' if len(doc.ents)>1 else '')
    print(f'{element.text:32s} {element.label_} {other_tag} {negated}')

print(";".join(map(lambda x: x.text, entities)))

report_name = full_path.split('/')[-1][:-4]
print(report_name)
