from random import shuffle
from ollama import Client
import logging
client = Client(host='http://localhost:11434')

#PROMPT='''I'm  going to give you a list of pipe-separated terms and I want you to remove from it all terms that are not medical symptoms or medical conditions. Don't ever alter a term in any way. Don't merge separate terms. Please answer with only the reduced list with elements separated by pipes. Use START_LIST and END_LIST to mark the beginning and end of the list.\n'''
PROMPT='''I'm  going to give you a list of pipe-separated terms and I want you to remove from it all terms that are not medical symptoms or medical conditions. Leave only symptoms or conditions, please. This is of the utmost importance. Please answer with only the reduced list with elements separated by pipes. Use START_LIST and END_LIST to mark the beginning and end of the list.\n'''

def ensemble_filter_list(original_list, chunk_size = 10, retries = 3, num_experts = 5):
    result_counts = {}

    for i in range(num_experts):
        filtered_list = filter_list(original_list, chunk_size, retries)
        for elem in filtered_list:
            result_counts[elem] = result_counts.get(elem, 0) + 1
    return [x for x in result_counts if result_counts[x] > num_experts/2]


def filter_list(original_list, chunk_size = 10, retries = 3):
    # Shuffle the list to avoid merging of contiguous terms, which Llama3 tends to do
    term_list = original_list[:] # Copy, as to no modify the original list
    shuffle(term_list)

    filtered_list = []

    for i in range(0, len(term_list), chunk_size):
        # Slice the list to get the current chunk
        terms = term_list[i:i + chunk_size]

        chunk_list = None
        tries = 0

        while chunk_list is None:
            tries += 1
            if tries > retries:
                raise Exception(f'After {retries} retries, Llama3 keeps sending malformed responses')
            try:
                logging.info('Connecting to Ollama...')
                complete_prompt = PROMPT+'|'.join(terms)
                logging.debug('Asked Llama3: ' + complete_prompt)
                response = client.chat(model='llama3', messages=[
                                        {
                                            'role': 'user',
                                            'content': complete_prompt,
                                        },
                                        ])
                logging.info('Ollama responded!')
                text_response = response['message']['content']
                logging.debug('Llama3 answered: ' + text_response)

                if 'START_LIST' not in text_response:
                    raise Exception(f'START_LIST token missing from "{text_response}"')
                if 'END_LIST' not in text_response:
                    raise Exception(f'END_LIST token missing from "{text_response}"')
                chunk_list_raw = text_response[text_response.index('START_LIST')+len('START_LIST'):text_response.index('END_LIST')].strip().split('|')
                chunk_list_raw = list(map(lambda x: x.strip(), chunk_list_raw))
                chunk_list = []
                for f in chunk_list_raw:
                    if f not in terms:
                        logging.info(f'Llama3 returned {f}, which was not in the original list ({terms})')
                    else:
                        chunk_list.append(f)
            except Exception as e:
                logging.warning(f'In attempt #{tries}, an error occurred: {e}')
                chunk_list = None

        if len(chunk_list) > 1 or (len(chunk_list) == 1 and chunk_list[0]!=''):
            filtered_list += chunk_list

    return filtered_list

if __name__=='__main__':
    test_list = 'years;scaffold;consciousness;headache;Neurological examination;right homonymous hemianopia;Computed tomography;brain;left occipital;bleeding;discharged;days;weeks;lost appetite;gait disturbances;hearing deficits;disorientation;Neurological examination;bilateral sensorineural hearing;visual deficits;meningism;fever;bilateral ataxic fingernose;heelshin test;ataxic gait;negative Romberg test;dementia;forgetfulness;nonattention;apathy;motor deficits;fig 1A;magnetic resonance imaging;MRI;fig 1B;right occipital bleeding;rim;haemosiderin;superficial central nervous system;Cerebral angiography;Cerebrospinal fluid;CSF;haemosiderophages;free haemoglobin;increased;erythrocytes;42600/l;leucocytes;protein 330 mg/dl (normal;decreased glucose;Routine;complete blood count (;CBC;electrolytes;liver;kidney;parameters;Pathogens;CSF;vasculitis;screening;antinuclear antibody;ANA;antineutrophil cytoplasmic antibody;ANCA;negative;Coagulation studies;partial thromboplastin time;PTT;international normalised ratio;INR;antithrombin (AT) III, protein C;S;factor VIII;activated protein C;anticardiolipin antibodies;patient;treated with;antihypertensives;corticosteroids;vitamins C;E;desferrioxamine;third cerebral bleeding;left parietal;caused his death;Autopsy;subarachnoid haemorrhage;brain herniation;metastases;undifferentiated carcinoma;left occipital;right parietooccipital;whole body;Superficial;CNS siderosis;chronic bleeding;subarachnoid space;combination;ataxia;hypoacusis;dementia;head trauma;diagnostic value;superficial;CNS siderosis'.split(';')

    filtered_list = ensemble_filter_list(test_list)

    print('Filtered list:')
    for elem in filtered_list:
        print(f'\t{elem}')
    print('\nLeft out:')
    for elem in test_list:
        if elem not in filtered_list:
            print(f'\t{elem}')