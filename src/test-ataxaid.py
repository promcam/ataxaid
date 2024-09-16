# Import main library
import os
import sys
PROJ_DIR = os.path.realpath(os.path.dirname(os.path.abspath('')))
sys.path.append(os.path.join(PROJ_DIR,'src'))
import ataxaid

FILE_PATH = PROJ_DIR+ '/AtaxAId/data/informe_ejemplo_en.txt'
print(f'Extracting entities from {FILE_PATH}...')
entities, _ = ataxaid.extract_entities_from_file(FILE_PATH, ner_type='en_ner_bc5cdr_md')

# print('Las entidades extraídas por en_ner_bc5cdr_md con negaciones son:')
# for element in entities:
#     negated = "NEGATED" if element._.negex else ""
#     print(f'{element.text:32s} {element.label_} {negated}')

results = []

processed = {} # Keep track of processed entities to avoid duplicates
for entity in entities:
    if entity in processed: # Skip entities that have already been processed
        continue
    processed[entity] = True
    matches = ataxaid.get_HPO_matches(entity)

    if len(matches) > 0:
        #print(f'Encontrados {len(matches)} matches para "{entity.text}"')
        result = {'term_name': entity.text,\
                'hpo_name': matches[0].HPO.name,\
                'hpo_code': matches[0].HPO.id,\
                'present': entity._.negex}

        #for m in matches:
        #    print(f'\t{m.HPO.id} - {m.HPO.name} ({m.query} vs. {m.matching_HPO_term} - dist={m.distance})')
        results.append(result)
    else:
        print(f'No se han detectado términos HPO para "{entity.text}"')
