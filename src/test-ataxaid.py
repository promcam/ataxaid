# Import main library
import os
import sys
PROJ_DIR = os.path.realpath(os.path.dirname(os.path.abspath('')))
sys.path.append(os.path.join(PROJ_DIR,'src'))
import ataxaid

FILE_PATH = '../data/informe_ejemplo_en.txt'
print(f'Extracting entities from {FILE_PATH}...')
entities = ataxaid.extract_entities_from_file(FILE_PATH)

print('Las entidades extraídas por en_ner_bc5cdr_md con negaciones son:')
for element in entities:
    negated = "NEGATED" if element._.negex else ""
    print(f'{element.text:32s} {element.label_} {negated}')