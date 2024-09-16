# Import main library
import os
import sys
import json

PROJ_DIR = os.path.realpath(os.path.dirname(os.path.abspath('')))
sys.path.append(os.path.join(PROJ_DIR,'src'))
import ataxaid

# import logging
# logger = logging.getLogger('ataxaid')
# logging.basicConfig(filename='logs/example.log', encoding='utf-8', level=logging.INFO)

TXT_PATH = '/Users/paula/Library/CloudStorage/OneDrive-UniversidadedaCoruña/TESIS/PAPERS/paper1/TXT_informes_revisados'
JSON_PATH = '/Users/paula/Library/CloudStorage/OneDrive-UniversidadedaCoruña/TESIS/PAPERS/paper1/paper1revisado3.json'

# # OPCIÓN 1
#METHOD_NAME = 'ataxaid-en_ner_bc5cdr_md'
#NER_TYPES = ['en_ner_bc5cdr_md']

# # OPCIÓN 2
# METHOD_NAME = 'ataxaid-en_ner_bionlp13cg_md'
# NER_TYPES = ['en_ner_bionlp13cg_md']

# # OPCIÓN 3
#METHOD_NAME = 'ataxaid-en_core_sci_scibert'
#NER_TYPES = ['en_core_sci_scibert']

# OPCIÓN 4
METHOD_NAME = 'ataxaid-bc5cdr_md+scibert'
NER_TYPES = ['en_ner_bc5cdr_md', 'en_core_sci_scibert']

WITH_OLLAMA_FILTER = True
#WITH_OLLAMA_FILTER = False

if WITH_OLLAMA_FILTER:
    import ollama_filter

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

for file in os.listdir(TXT_PATH):
    if file.endswith('.txt'):
        full_path = os.path.join(TXT_PATH, file)
        print(full_path)

        entities = []
        for ner in NER_TYPES:
            print(f'Extracting entities from {file} with {ner}...')
            partial_entities, _ = ataxaid.extract_entities_from_file(full_path, ner)
            entities += partial_entities
        
        if WITH_OLLAMA_FILTER:
            entity_dict = {elem.text:elem for elem in entities}
            filtered_terms = ollama_filter.ensemble_filter_list(list(map(lambda x: x.text, entities)))
            entities = list(map(lambda x: entity_dict[x], filtered_terms))
            print(f'Ollama filtered out {len(entity_dict)-len(entities)} terms')

        print(f'Las entidades extraídas son:')
        for element in entities:
            negated = "NEGATED" if element._.negex else ""
            print(f'{element.text:32s} {element.label_} {negated}')

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

        report_name = full_path.split('/')[-1][:-4]
        print(report_name)
        # Save results to dictionary
        data['reports'][report_name]['methods'][METHOD_NAME + ('_filtered' if WITH_OLLAMA_FILTER else '')] = results
# Save updated dictionary to JSON
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)