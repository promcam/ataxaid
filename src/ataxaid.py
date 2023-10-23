from pathlib import Path # Used for reading file to string
import re
import spacy
from negspacy.negation import Negex
from spacy.tokens import Span, Token
import logging
from typing import Callable, Any
from collections import namedtuple
from collections.abc import Iterable
import nltk
from nltk.stem import PorterStemmer

import os
PROJ_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

HPOMatch = namedtuple('HPOMatch', ['query', 'HPO', 'matching_HPO_term', 'distance'])

def remove_contractions(phrase):
    phrase = re.sub(r"won\'t", "will not", phrase)
    phrase = re.sub(r"can\'t", "can not", phrase)
    phrase = re.sub(r"n\'t", " not", phrase)
    phrase = re.sub(r"\'re", " are", phrase)
    phrase = re.sub(r"\'s", " is", phrase)
    phrase = re.sub(r"\'d", " would", phrase)
    phrase = re.sub(r"\'ll", " will", phrase)
    phrase = re.sub(r"\'t", " not", phrase)
    phrase = re.sub(r"\'ve", " have", phrase)
    phrase = re.sub(r"\'m", " am", phrase)
    return phrase

def extract_entities_from_file(path:str) -> list[Span]:
    text = Path(path).read_text()
    return extract_entities(text)

nlp_model = None # Global variable to retain between calls and avoid loading the model everytime

def extract_entities(text:str) -> list[Span]:
    text = remove_contractions(text)

    # Load spaCy model
    global nlp_model
    if nlp_model is None:
        logging.debug('Loading en_ner_bc5cdr_md...')
        nlp_model = spacy.load("en_ner_bc5cdr_md")
        nlp_model.add_pipe("negex", config={"ent_types":["DISEASE"]})

    spacy_doc = nlp_model(text)
    return list(spacy_doc.ents)

def _get_combinations(token_list:list[Token]) -> list[str]:
    '''
    Given a list of tokens, returns all possible combinations in which each token may or may not be
    present (order between tokens is always preserved)
    '''
    if len(token_list) == 0:
        return []
    if len(token_list) == 1:
        return ['', token_list[0].text]
    combinations_remainder = _get_combinations(token_list[1:])
    combinations = []
    for c in combinations_remainder: # For each combination of words from the second on...
        combinations.append((token_list[0].text + ' ' + c).strip()) # ..add a combination with the first word...
        combinations.append(c) # ...and one without it
    return combinations

def _get_alternative_names(token_span:Span) -> list[str]:
    '''
    Returns a list with alternative names to refer to the text contained in the token span
    Noun phrases are identified and each noun is considered with all possible combination of the (non-stopword) words before it
    '''
    token_list = list(iter(token_span))
    
    if len(token_list) == 1: # A single token is returned by itself
        return [token_span.text]
    
    noun_phrases = [] # Para cada sustantivo, guardamos las palabras que tiene antes
    current_phrase = []
    for t in token_list:
        if t.tag_.startswith('NN'): # t is a noun, so we add a new noun phrase
            noun_phrases.append((t, current_phrase))
        else:
            current_phrase.append(t)

    alternatives = [token_span.text] # The whole span is always an alternative
    for noun, words in noun_phrases:
        no_stopwords = list(filter(lambda x: not x.is_stop, words))
        accomp_words = _get_combinations(no_stopwords)
        #print(f'Acompañamientos para {sin_stop}: {acompañamientos}')
        for a in accomp_words:
            alternative = (a + ' ' + noun.text).strip()
            if alternative != token_span.text: # Avoid adding one for the whole span, which was added earlier
                alternatives.append(alternative)
        else: # This noun doesn't have any words before it
            if noun.text not in alternatives:
                alternatives.append(noun.text)
    return alternatives

porter = None # Global variable to retain between calls and avoid loading the stemmer everytime
def _stem_phrase(phrase:str) -> str:
    global porter
    if porter is None:
        logging.debug('Loading PorterStemmer...')
        porter = PorterStemmer()
    token_words= nltk.word_tokenize(phrase)
    stem_sentence=[]
    for word in token_words:
        stem_sentence.append(porter.stem(word))
        stem_sentence.append(" ")
    return "".join(stem_sentence).strip()

stopwords = None # Global variable to retain between calls and avoid loading the stopword list everytime
def _hamming_distance(original:str, find:str, partial_match_value:float = 0.51) -> float:
    original = original.lower()
    find = find.lower()
    
    # Remove stopwords
    global stopwords
    if stopwords is None: # If it's not already loaded, load stopword list from file
        logging.debug('Loading stopwords...')
        stopwords = []
        with open(os.path.join(PROJ_DIR,'assets','stopwords.txt'),'r') as fIn:
            stopwords = fIn.readlines()
        stopwords = list(map(lambda x:x.strip(), stopwords))
    original = " ".join(filter(lambda x: x.strip() not in stopwords, original.split(' ')))
    find = " ".join(filter(lambda x: x.strip() not in stopwords, find.split(' ')))
    
    # Stemming
    original_stemmed = _stem_phrase(original)
    find_stemmed = _stem_phrase(find)
    
    # Workaround because the stemmer does not stem 'ataxia' correctly
    original_stemmed = original_stemmed.replace('ataxia', 'atax')
    find_stemmed = find_stemmed.replace('ataxia', 'atax')
    
    original_stems = original_stemmed.split(" ")
    find_stems = find_stemmed.split(" ")

    # Separamos original y find en palabras
    original = re.sub(r'[^a-z0-9\-]+',' ', original).split(' ')
    find = re.sub(r'[^a-z0-9\-]+',' ', find).split(' ')
    
    # Remove non alphanum chars
    #original_stems = list(filter(lambda x: re.search(r'[a-zA-Z0-9]', x), original_stems)) # Con que haya quedado un alfanumérico nos vale
    #find_stems = list(filter(lambda x: re.search(r'[a-zA-Z0-9]', x), find_stems)) # Con que haya quedado un alfanumérico nos vale

    if len(find_stems) == 0:
        return 0
    
    matches = 0
    num_original = len(original_stems)
    num_find = len(find_stems)

    # TODO CHECK THIS LOOP!!
    for w_, wf_ in zip(find_stems, find): # Indulgent comparison that allows partial matches
        if w_ in original_stems:
            matches += 1
        elif w_ in original or wf_ in original:
            # Añadido para hacer más permisiva la comparación para intentar subsanar errores del stemmer
            matches += partial_match_value

    # Compute Hamming distance: # chars to be added/removed + #chars to be changed
    return abs(num_original - num_find) + min(num_original, num_find) - matches

def _get_mins(iterable:Iterable[Any], key:Callable[[Any], float]) ->  list[Any]:
    '''
    Works as min(), but it will return a list with all the elements having the min value
    '''
    min_key = float('inf')
    result = []
    for elem in iterable:
        k = key(elem)
        if k > min_key:
            continue
        elif k < min_key:
            min_key = k
            result = [elem]
        else: # k == menor_clave
            result.append(elem)
    return result


Ontology = None # Global variable to retain between calls and avoid loading and initializing the ontology everytime it's needed
def _search_HPO(query:str, string_to_match:str, distance_measurer:Callable[[str, str], float] = _hamming_distance) -> list[HPOMatch]:
    '''
    Given a query term, finds the best (according to distance_measurer) HPO matches resulting from matching HPO terms with it
    '''
    global Ontology
    if Ontology is None:
        logging.info('Loading Ontology...')
        from pyhpo import Ontology

        # initilize the Ontology ()
        _ = Ontology()

    best_matches:list[HPOMatch] = [] # All of the best matches will be returned (there may be more than one at the same distance)

    stemmed_query = _stem_phrase(query)
    results = Ontology.search(stemmed_query)
    results = list(results)
    
    if len(results) == 0 and stemmed_query not in query: # If there's no results maybe the stemmer screwed up. Try without it.
        results = Ontology.search(query)
        results = list(results)
    
    if len(results) > 0:
        logging.info(f'{len(results)} results for "{query}"({stemmed_query})')
        all_matches:list[str] = []
        for i,r in enumerate(results):
            # possible_names will store all possible ways to refer to the HPO term from search result r
            possible_names = r.synonym + [r.name]

            # Measure how well query matches each of the possible_names
            all_matches += list(map(lambda x: HPOMatch(query, r, x, distance_measurer(string_to_match, x)), possible_names))
            if logging.getLogger().isEnabledFor(logging.INFO):
                for m in all_matches:
                    logging.info(f'\t{m.HPO.id} - {m.HPO.name} ({string_to_match} vs. {m.matching_HPO_term} - dist={m.distance})')
        # Get the best match for this search result according to the computed distances
        best_matches = _get_mins(all_matches, key=lambda x: x.distance)
        
        min_distance = best_matches[0].distance
        if logging.getLogger().isEnabledFor(logging.INFO):
            all_matches.sort(key=lambda x:-x.distance)
            for match in all_matches:
                print(f'\t\t\t{match.matching_HPO_term} ({match.distance})')

        logging.info(f'Got {" | ".join(map(lambda x: f"{x.HPO.id} ({x.matching_HPO_term})",best_matches))} for "{query}"({stemmed_query}) {min_distance}')
    else:
        logging.info(f'No results for "{query}"({stemmed_query})')
    return best_matches

def get_HPO_matches(entity:Span) -> list[HPOMatch]:
    '''
    Given an entity, returns a list of HPOMatches
    '''
    all_matches:list[HPOMatch] = []
    if entity.label_=='DISEASE': # Only process diseases, ignore rest 
        # Get all alternative ways of referring to entity
        alternative_names = _get_alternative_names(entity)
        
        logging.info(f'Found the following names for {entity.text}:')
        if logging.getLogger().isEnabledFor(logging.INFO):
            for alt in alternative_names:
                logging.info(f'\t{alt}')

        entity_matches:list[HPOMatch] = []
        # For each alternative name, get add all HPO matches to the overall matches list
        for alt in alternative_names:
            entity_matches += _search_HPO(alt, entity.text)
        best_entity_matches = _get_mins(entity_matches, lambda x: x.distance)

        if len(best_entity_matches) > 0:
            if len(best_entity_matches) > 1: # There's several matches with the same distance -> take the longest
                logging.info(f'Found these options for {entity.text} with distance {best_entity_matches[0].distance}:')
                if logging.getLogger().isEnabledFor(logging.INFO):
                    for match in best_entity_matches:
                        print(f'\t{match.HPO.id} ({match.matching_HPO_term}) para "{match.query}"')
                # Select the longest ones
                best_entity_matches = _get_mins(best_entity_matches, lambda x: len(x.matching_HPO_term))
                logging.warning(f'More than one HPOMatch for {entity.text}')
            all_matches += best_entity_matches
    # TODO - Remove duplicates
    return all_matches

if __name__ == '__main__':
    #logging.getLogger().setLevel(logging.INFO)
    #logging.basicConfig(level=logging.INFO, filename=os.path.join(PROJ_DIR, 'logs', 'test-log.txt'),filemode="w")
    FILE_PATH = './data/informe_ejemplo_en.txt'
    print(f'Extracting entities from {FILE_PATH}...')
    entities = extract_entities_from_file(FILE_PATH)

    print('Las entidades extraídas por en_ner_bc5cdr_md con negaciones son:')
    for element in entities:
        negated = "NEGATED" if element._.negex else ""
        print(f'{element.text:32s} {element.label_} {negated}')

    processed = {} # Keep track of processed entities to avoid duplicates
    all_matches:list[HPOMatch] = []
    unmatched:list[str] = []
    for entity in entities:
        if entity in processed: # Skip entities that have already been processed
            continue
        processed[element.text] = True
        matches = get_HPO_matches(entity)

        if len(matches) > 0:
            print(f'Encontrados {len(matches)} matches para "{entity.text}"')
            for m in matches:
                print(f'\t{m.HPO.id} - {m.HPO.name} ({m.query} vs. {m.matching_HPO_term} - dist={m.distance})')
        else:
            print(f'No se han detectado términos HPO para "{entity.text}"')
