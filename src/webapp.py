from flask import Flask, render_template, request, redirect
# Import main library
import os
import sys
PROJ_DIR = os.path.realpath(os.path.dirname(os.path.abspath('')))
sys.path.append(os.path.join(PROJ_DIR,'src'))
import ataxaid

app = Flask(__name__, template_folder='../assets/templates')


@app.route('/gaitas', methods=['GET', 'POST'])
def gaitas():
    username = None
    if 'username' in request.form:
        username = request.form['username']
    #print(username)

    pokemons =["Pikachu", "Charizard", "Squirtle", "Jigglypuff", "Bulbasaur", "Gengar", "Charmander", "Mew", "Lugia", "Gyarados"] 

    if username is not None:
        return render_template('gaitas.html', usuario=username, pokemons=pokemons, num_pokemons=len(pokemons))
    else:
        return render_template('formulario.html', usuario=username)
    
@app.route('/', methods=['GET'])
def principal():
    return render_template('formulario.html')

@app.route('/resultados', methods=['POST'])
def resultados():
    informe = None
    if 'informe_escrito' in request.form:
        informe = request.form['informe_escrito'].strip()
    if informe is None or informe == '':
        return redirect("/?error=1", code=302)
    
    informe = ataxaid.remove_contractions(informe)

    entities = ataxaid.extract_entities(informe)
    #entities_str = []
    elementos_informe:list[tuple[str, str, str, str]] = []
    last_printed_char = 0
    for i,element in enumerate(entities):
        negated = "NEGATED" if element._.negex else ""
        element_str = f'{element.text} {element.label_} {negated}'
        #entities_str.append(element_str)
        elementos_informe.append((informe[last_printed_char:element.start_char], None, None, None))
        elementos_informe.append((element.text, f'{i} - {element_str}', element.label_.lower(), negated))
        last_printed_char = element.end_char
    elementos_informe.append((informe[last_printed_char:], None, None, None))


    processed = {} # Keep track of processed entities to avoid duplicates
    all_matches:list[ataxaid.HPOMatch] = []
    unmatched:list[str] = []
    listado = []
    for entity in entities:
        if entity in processed: # Skip entities that have already been processed
            continue
        processed[element.text] = True
        #print(f'Buscando "{entity.text}" en HPO...')
        matches = ataxaid.get_HPO_matches(entity)
        
        if len(matches) > 0:
            #for m in matches:
            m = matches[0]
            listado.append((entity,m.HPO.name,m.HPO.id))
        elif entity.label_ == 'DISEASE':
            listado.append((entity, '--NO MATCH--', '--NO MATCH--'))
    return render_template('resultados.html', subrayado_lista=elementos_informe, num_subrayados_lista=len(elementos_informe), listado=listado, num_listado=len(listado))

if __name__ == "__main__":
    app.run(port=3458)
