from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for

import psycopg2
import psycopg2.extras

url = "host='localhost' dbname='postgres' options='-c search_path=189632_simone' user='postgres' password='96631212'"

app = Flask(__name__)

#INDICE
@app.route('/')
def index():
    return render_template('index.html')

#COMANDA

@app.route('/lista_comande', methods=['GET'])
def lista_comande():
    c = elenco_comande()
    return render_template('lista_comande.html', comande=c)

# richiamata nella funzione index
def elenco_comande():
    connection = psycopg2.connect(url)#connetto databasse
    cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)#creo cursore

    cursor.execute("select * from Comande order by data_ora desc")
    comande=[]
    for row in cursor:
        comanda={
        "id_comanda":row["id_comanda"],
        "data_ora":row["data_ora"],
        "id_tavolo":row["id_tavolo"],
        "prezzo_totale":row["prezzo_totale"],
        "id_dipendente":row["id_dipendente"]
        }
        comande.append(comanda)

    connection.commit()#salva modifiche database
    cursor.close()
    connection.close()

    return comande

@app.route('/crea_comanda', methods=['GET', 'POST'])#posso creare modulo e ricevere dati
def crea_comanda():
    if request.method == 'POST':#RICEVO DATI
        try:
            connection = psycopg2.connect(url)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            id_dipendente = request.form.get('id_dipendente')#chiedo id dipendente
            numero_tavolo = request.form.get('numero_tavolo')#chiedo num tav
            
            cursor.execute("""
                INSERT INTO Comande (id_dipendente,Data_ora, id_tavolo, prezzo_totale) 
                VALUES (%s,CURRENT_TIMESTAMP, %s, 0) RETURNING id_comanda
            """, (id_dipendente,numero_tavolo,))#quando inserisco i valori returning restituisce il valore appena generato di id_comanda
            id_comanda = cursor.fetchone()['id_comanda']#assegno valore id_comanda
            
            #inizializzo prezzo
            total_price = 0
            menu_items = {
                'classic_burger_qty': 'Classic Burger',
                'veggie_dream_qty': 'Veggie Dream',
                'classic_dog_qty': 'Classic Dog',
                'patatine_classiche_qty': 'Classiche'
            }
            
            # ciclo chiavi e valori dizionario
            for quantità, nome_portata in menu_items.items():
                qty = request.form.get(quantità)
                qty = int(qty) if qty else 0  # se è un numero lo metto come int oppure la pongo a 0

                if qty > 0:
                    # trovo prezzo e se esiste lo assegno oppure do 0
                    cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (nome_portata,))
                    prezzo_row = cursor.fetchone()
                    prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                    
                    # creo una nuova riga in contenuto comanda
                    cursor.execute("""
                        INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                        VALUES (%s, %s, %s)
                    """, (id_comanda, nome_portata, qty))
                    
                    total_price += prezzo * qty
            
            # dizionario birre
            beer_mappings = {
                'pilsner_quantita': {
                    '33cl': 'Pilsner Light 33cl', 
                    '50cl': 'Pilsner Light 50cl',
                    'qty_key': 'pilsner_light_qty'
                },
                'stout_quantita': {
                    '33cl': 'Stout Dream 33cl', 
                    '50cl': 'Stout Dream 50cl',
                    'qty_key': 'stout_dream_qty'
                },
                'weiss_quantita': {
                    '33cl': 'Weiss Sun 33cl', 
                    '50cl': 'Weiss Sun 50cl',
                    'qty_key': 'weiss_sun_qty'
                }
            }
            
            # itero le birre
            for quantità_birra, tipo_birra in beer_mappings.items():
                selected_size = request.form.get(quantità_birra)
                beer_qty = request.form.get(tipo_birra['qty_key'])  
                beer_qty = int(beer_qty) if beer_qty else 0  # se è un numero lo metto come int oppure la pongo a 0
                
                if selected_size and beer_qty > 0:
                    beer_name = tipo_birra[selected_size]
                    
                    # Get beer price
                    cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (beer_name,))
                    prezzo_row = cursor.fetchone()
                    prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                    
                    # Insert into Contenuto_Comanda
                    cursor.execute("""
                        INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                        VALUES (%s, %s, %s)
                    """, (id_comanda, beer_name, beer_qty))
                    
                    total_price += prezzo * beer_qty
            
            # Soft drinks processing
            drink_mappings = {
                'coca_cola_quantita': {
                    '33cl': 'Coca-Cola 33cl', 
                    '50cl': 'Coca-Cola 50cl',
                    'qty_key': 'coca_cola_qty'
                },
                'fanta_quantita': {
                    '33cl': 'Fanta 33cl', 
                    '50cl': 'Fanta 50cl',
                    'qty_key': 'fanta_qty'
                }
            }
            
            # Process soft drinks
            for drink_form_key, drink_options in drink_mappings.items():
                selected_size = request.form.get(drink_form_key)
                drink_qty = request.form.get(drink_options['qty_key'])
                drink_qty = int(drink_qty) if drink_qty else 0  # Convert to int or set to 0 if None
                
                if selected_size and drink_qty > 0:
                    drink_name = drink_options[selected_size]
                    
                    # Get drink price
                    cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (drink_name,))
                    prezzo_row = cursor.fetchone()
                    prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                    
                    # Insert into Contenuto_Comanda
                    cursor.execute("""
                        INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                        VALUES (%s, %s, %s)
                    """, (id_comanda, drink_name, drink_qty))
                    
                    total_price += prezzo * drink_qty
            
            # Water processing
            water_items = {
                'acqua_naturale_qty': 'Acqua Naturale 33cl',
                'acqua_frizzante_qty': 'Acqua Frizzante 33cl'
            }
            
            # Process water items
            for water_form_key, water_name in water_items.items():
                water_qty = request.form.get(water_form_key)
                water_qty = int(water_qty) if water_qty else 0
                
                if water_qty > 0:
                    # Get water price
                    cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (water_name,))
                    prezzo_row = cursor.fetchone()
                    prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                    
                    # Insert into Contenuto_Comanda
                    cursor.execute("""
                        INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                        VALUES (%s, %s, %s)
                    """, (id_comanda, water_name, water_qty))
                    
                    total_price += prezzo * water_qty
            
            # Update total price in Comande
            cursor.execute("""
                UPDATE Comande 
                SET prezzo_totale = %s 
                WHERE id_comanda = %s
            """, (total_price, id_comanda))

            
            # Close cursor and connection
            connection.commit()
            cursor.close()
            connection.close()
            c = elenco_comande()
            return render_template('lista_comande.html', comande=c)

        except Exception as e:
            print(f"Errore nella creazione della comanda: {str(e)}")
            return f"Errore: {str(e)}"

    return render_template('crea_comanda.html')


@app.route('/dettagli', methods=['POST'])
def dettagli():
    id_comanda = request.form['id_comanda']

    # passo id_comanda a dettagli_comanda
    portate = dettagli_comanda(id_comanda)

    
    return render_template("contenuto_comanda.html", portate=portate)

def dettagli_comanda(id_comanda):
    connection = psycopg2.connect(url)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Corrected: properly parameterized query
    cursor.execute("SELECT id_comanda, nome_portata, quantità FROM Contenuto_Comanda WHERE id_comanda = %s", (id_comanda,))
    
    # Corrected: initialize portate list before the loop
    portate = []
    
    # Corrected: fetch all rows and add to portate list
    for row in cursor:
        portata = {
            "id_comanda": row["id_comanda"],
            "nome_portata": row["nome_portata"],
            "quantità": row["quantità"]
        }
        portate.append(portata)

    connection.commit()
    cursor.close()
    connection.close()

    return portate
    
@app.route('/modifica_comanda/<int:id_comanda>', methods=['GET'])
def modifica_comanda(id_comanda):
    try:
        connection = psycopg2.connect(url)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # ritorna colonne comanda
        cursor.execute("""
            SELECT c.id_comanda, c.id_tavolo, c.data_ora, c.prezzo_totale, c.id_dipendente,
                   cc.nome_portata, cc.quantità
            FROM Comande c
            LEFT JOIN Contenuto_Comanda cc ON c.id_comanda = cc.id_comanda
            WHERE c.id_comanda = %s
        """, (id_comanda,))
        
        # controllo se esiste la comanda
        risultati = cursor.fetchall()
        if not risultati:
            cursor.close()
            connection.close()
            return "Comanda non trovata", 404
        
    
        ordine = {
            'id_comanda': risultati[0]['id_comanda'],
            'id_tavolo': risultati[0]['id_tavolo'],
            'data_ora': risultati[0]['data_ora'],
            'prezzo_totale': risultati[0]['prezzo_totale'],
            'id_dipendente': risultati[0]['id_dipendente'],
            
            'portate': {}
        }#estraggo i termini"fissi" da comanda
        
        
        for riga in risultati:
            if riga['nome_portata']:
                ordine['portate'][riga['nome_portata']] = riga['quantità']
        
        cursor.close()
        connection.close()
        
        return render_template('modifica_comanda.html', ordine=ordine)
    
    except Exception as e:
        print(f"Errore nella modifica della comanda: {str(e)}")
        return f"Errore: {str(e)}", 500

@app.route('/aggiorna_comanda', methods=['POST'])
def aggiorna_comanda():
    try:
        
        connection = psycopg2.connect(url)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        id_comanda = request.form.get('id_comanda')#recupero la quantità dal form
        numero_tavolo = request.form.get('numero_tavolo')
        
        #processi piatti del menu
        menu_items = {
            'classic_burger_qty': 'Classic Burger',
            'veggie_dream_qty': 'Veggie Dream',
            'classic_dog_qty': 'Classic Dog',
            'patatine_classiche_qty': 'Classiche'
        }
        
        #inizializzo prezzo
        total_price = 0
        
        # inizializzo la comanda
        cursor.execute("DELETE FROM Contenuto_Comanda WHERE id_comanda = %s", (id_comanda,))
        
        
        for form_key, portata_name in menu_items.items():
            qty = request.form.get(form_key)
            qty = int(qty) if qty else 0
            
            if qty > 0:
                # Get portata price
                cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (portata_name,))
                prezzo_row = cursor.fetchone()
                prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                
                # Insert into Contenuto_Comanda
                cursor.execute("""
                    INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                    VALUES (%s, %s, %s)
                """, (id_comanda, portata_name, qty))
                
                total_price += prezzo * qty
        
        # Beer processing (similar to previous implementation)
        beer_mappings = {
            'pilsner_quantita': {
                '33cl': 'Pilsner Light 33cl', 
                '50cl': 'Pilsner Light 50cl',
                'qty_key': 'pilsner_light_qty'
            },
            'stout_quantita': {
                '33cl': 'Stout Dream 33cl', 
                '50cl': 'Stout Dream 50cl',
                'qty_key': 'stout_dream_qty'
            },
            'weiss_quantita': {
                '33cl': 'Weiss Sun 33cl', 
                '50cl': 'Weiss Sun 50cl',
                'qty_key': 'weiss_sun_qty'
            }
        }
        
        # itnero le birre
        for quantità_birra, tipo_birra in beer_mappings.items():
            selected_size = request.form.get(quantità_birra)
            beer_qty = request.form.get(tipo_birra['qty_key'])  #recupero quantità
            beer_qty = int(beer_qty) if beer_qty else 0
            
            if selected_size and beer_qty > 0:
                beer_name = tipo_birra[selected_size]
                
                # ottengo prezzo birra e lo assegno
                cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (beer_name,))
                prezzo_row = cursor.fetchone()
                prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                
                # creo nuova iìriga in contenuto_comanda
                cursor.execute("""
                    INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                    VALUES (%s, %s, %s)
                """, (id_comanda, beer_name, beer_qty))
                
                total_price += prezzo * beer_qty
        
        # Soft drinks processing
        drink_mappings = {
            'coca_cola_quantita': {
                '33cl': 'Coca-Cola 33cl', 
                '50cl': 'Coca-Cola 50cl',
                'qty_key': 'coca_cola_qty'
            },
            'fanta_quantita': {
                '33cl': 'Fanta 33cl', 
                '50cl': 'Fanta 50cl',
                'qty_key': 'fanta_qty'
            }
        }
        
        for drink_form_key, drink_options in drink_mappings.items():
            selected_size = request.form.get(drink_form_key)
            drink_qty = request.form.get(drink_options['qty_key'])
            drink_qty = int(drink_qty) if drink_qty else 0
            
            if selected_size and drink_qty > 0:
                drink_name = drink_options[selected_size]
                
                cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (drink_name,))
                prezzo_row = cursor.fetchone()
                prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                
                cursor.execute("""
                    INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                    VALUES (%s, %s, %s)
                """, (id_comanda, drink_name, drink_qty))
                
                total_price += prezzo * drink_qty
        
        water_items = {
            'acqua_naturale_qty': 'Acqua Naturale 33cl',
            'acqua_frizzante_qty': 'Acqua Frizzante 33cl'
        }
        
        for water_form_key, water_name in water_items.items():
            water_qty = request.form.get(water_form_key)#recupero quantità usando la chiave
            water_qty = int(water_qty) if water_qty else 0
            
            if water_qty > 0:
                
                cursor.execute("SELECT prezzo FROM Portata WHERE nome_portata = %s", (water_name,))
                prezzo_row = cursor.fetchone()
                prezzo = prezzo_row['prezzo'] if prezzo_row else 0
                
                cursor.execute("""
                    INSERT INTO Contenuto_Comanda (id_comanda, nome_portata, quantità) 
                    VALUES (%s, %s, %s)
                """, (id_comanda, water_name, water_qty))
                
                total_price += prezzo * water_qty
        
        # setto il prezzo totale della comanda
        cursor.execute("""
            UPDATE Comande 
            SET prezzo_totale = %s 
            WHERE id_comanda = %s
        """, (total_price, id_comanda))
        
        
        connection.commit()
        cursor.close()
        connection.close()
        c = elenco_comande()
        return render_template('lista_comande.html', comande=c)

    except Exception as e:#e contiene l'errore
        print(f"Errore nell'aggiornamento della comanda: {str(e)}")
        return f"Errore: {str(e)}", 500

@app.route('/elimina', methods=['POST'])
def elimina_comanda():
    id_comanda = request.form['id_comanda']

    elimina(id_comanda)

    return lista_comande()

def elimina(id_comanda):
    connection = psycopg2.connect(url)
    cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    cursor.execute("DELETE FROM Contenuto_Comanda WHERE id_comanda = %s", (id_comanda,))
    cursor.execute("DELETE FROM Comande WHERE id_comanda = %s", (id_comanda,))

    connection.commit()
    cursor.close()
    connection.close()

#PRENOTAZIONI
    
@app.route('/lista_prenotazioni', methods=['GET'])
def lista_prenotazioni():
    p = elenco_prenotazioni()
    return render_template('lista_prenotazioni.html', prenotazioni=p)

# richiamata nella funzione index
def elenco_prenotazioni():
    connection = psycopg2.connect(url)
    cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    cursor.execute("select * from prenotazioni order by data_ora desc")
    prenotazioni=[]
    for row in cursor:
        prenotazione={
        "id_prenotazione":row["id_prenotazione"],
        "data_ora":row["data_ora"],
        "id_tavolo":row["id_tavolo"],
        "numero_persone":row["numero_persone"],
        "id_dipendente":row["id_dipendente"]
        }
        prenotazioni.append(prenotazione)

    connection.commit()
    cursor.close()
    connection.close()

    return prenotazioni

@app.route('/crea_prenotazione', methods=['GET', 'POST'])
def crea_prenotazione():
    if request.method == 'POST':
        try:
            connection = psycopg2.connect(url)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            id_dipendente = (request.form.get('id_dipendente'))
            numero_persone = int(request.form.get('numero_persone'))
            data_ora = request.form.get('data_ora')
            tipo_zona = request.form.get('tipo', 'dentro')  # Default metto dentro
            
            # Verifico la disponibilità del tavolo nelle 2 ore precedenti e successive
            cursor.execute("""
                SELECT id_tavolo 
                FROM Tavolo 
                WHERE capienza >= %s 
                  AND tipo = %s
                  AND id_tavolo NOT IN (
                    SELECT id_tavolo 
                    FROM Prenotazioni 
                    WHERE data_ora BETWEEN 
                        timestamp %s - interval '2 hours' AND 
                        timestamp %s + interval '2 hours'
                  )
                LIMIT 1
            """, (numero_persone, tipo_zona, data_ora, data_ora))
            
            tavolo = cursor.fetchone()
            
            if not tavolo:
                # se non disponibile provo un altra zona
                alternate_zona = 'fuori' if tipo_zona == 'dentro' else 'dentro'
                cursor.execute("""
                    SELECT id_tavolo 
                    FROM Tavolo 
                    WHERE capienza >= %s 
                      AND tipo = %s
                      AND id_tavolo NOT IN (
                        SELECT id_tavolo 
                        FROM Prenotazioni 
                        WHERE data_ora BETWEEN 
                            timestamp %s - interval '2 hours' AND 
                            timestamp %s + interval '2 hours'
                      )
                    LIMIT 1
                """, (numero_persone, alternate_zona, data_ora, data_ora))
                
                tavolo = cursor.fetchone()
            
            if not tavolo:
                connection.close()
                return "Nessun tavolo disponibile per il numero di persone richiesto", 400
            
            # inserisco i dati
            cursor.execute("""
                INSERT INTO Prenotazioni ( data_ora, id_tavolo, numero_persone,id_dipendente) 
                VALUES (%s, %s, %s, %s)
                RETURNING id_prenotazione
            """, ( data_ora, tavolo['id_tavolo'], numero_persone,id_dipendente))
            
            # assegno id prenotazione
            id_prenotazione = cursor.fetchone()['id_prenotazione']
            
            # Commit changes
            connection.commit()
            cursor.close()
            connection.close()
            p = elenco_prenotazioni()
            return render_template('lista_prenotazioni.html', prenotazioni=p)
        
        except Exception as e:
            print(f"Errore nella creazione della prenotazione: {str(e)}")
            return f"Errore: {str(e)}", 500
    
    return render_template('crea_prenotazione.html')

@app.route('/modifica_prenotazione/<int:id_prenotazione>', methods=['GET', 'POST'])
def modifica_prenotazione(id_prenotazione):
    try:
        # Connessione al database
        connection = psycopg2.connect(url)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if request.method == 'POST':
            id_dipendente = (request.form.get('id_dipendente'))
            numero_persone = int(request.form.get('numero_persone'))
            data_ora = request.form.get('data_ora')
            tipo_zona = request.form.get('tipo_zona', 'dentro')
            
            # Trova la prenotazione corrente
            cursor.execute("""
                SELECT id_tavolo, numero_persone, data_ora 
                FROM Prenotazioni 
                WHERE id_prenotazione = %s
            """, (id_prenotazione,))
            prenotazione_attuale = cursor.fetchone()
            
            if not prenotazione_attuale:
                connection.close()
                return "Prenotazione non trovata", 404
            
            # Verifica la disponibilità di un tavolo
            cursor.execute("""
                SELECT id_tavolo 
                FROM Tavolo 
                WHERE capienza >= %s 
                  AND tipo = %s
                  AND id_tavolo NOT IN (
                    SELECT id_tavolo 
                    FROM Prenotazioni 
                    WHERE data_ora BETWEEN 
                        timestamp %s - interval '2 hours' AND 
                        timestamp %s + interval '2 hours'
                  )
                LIMIT 1
            """, (numero_persone, tipo_zona, data_ora, data_ora))
            
            tavolo = cursor.fetchone()
            
            if not tavolo:
                # Prova una zona alternativa
                alternate_zona = 'fuori' if tipo_zona == 'dentro' else 'dentro'
                cursor.execute("""
                    SELECT id_tavolo 
                    FROM Tavolo 
                    WHERE capienza >= %s 
                      AND tipo = %s
                      AND id_tavolo NOT IN (
                        SELECT id_tavolo 
                        FROM Prenotazioni 
                        WHERE data_ora BETWEEN 
                            timestamp %s - interval '2 hours' AND 
                            timestamp %s + interval '2 hours'
                      )
                    LIMIT 1
                """, (numero_persone, alternate_zona, data_ora, data_ora))
                
                tavolo = cursor.fetchone()
            
            if not tavolo:
                connection.close()
                return "Nessun tavolo disponibile per il numero di persone richiesto", 400
            
            # Aggiorna la prenotazione
            cursor.execute("""
                UPDATE Prenotazioni 
                SET data_ora = %s, 
                    id_tavolo = %s, 
                    numero_persone = %s,
                    id_dipendente = %s
                WHERE id_prenotazione = %s
            """, (data_ora, tavolo['id_tavolo'], numero_persone, id_dipendente, id_prenotazione))
            connection.commit()
            cursor.close()
            connection.close()
            
            # Carica le prenotazioni e visualizza la lista
            return redirect(url_for('lista_prenotazioni'))
        
        # inserisce i dati messi in passato
        cursor.execute("""
            SELECT p.id_prenotazione, p.data_ora, p.id_tavolo, 
                   p.numero_persone, t.tipo, t.capienza
            FROM Prenotazioni p
            JOIN Tavolo t ON p.id_tavolo = t.id_tavolo
            WHERE p.id_prenotazione = %s
        """, (id_prenotazione,))
        
        prenotazione = cursor.fetchone()
        
        if not prenotazione:
            connection.close()
            return "Prenotazione non trovata", 404
        
        connection.close()
        return render_template('modifica_prenotazione.html', prenotazione=prenotazione)
    
    except Exception as e:
        print(f"Errore nella modifica della prenotazione: {str(e)}")
        return f"Errore: {str(e)}", 500

    
@app.route('/elimina_preonazione', methods=['POST'])
def elimina_prenotazione():
    id_prenotazione = request.form['id_prenotazione']
    elimina_p(id_prenotazione)
    return lista_prenotazioni()

def elimina_p(id_prenotazione):
    connection = psycopg2.connect(url)
    cursor = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cursor.execute("DELETE FROM prenotazioni WHERE id_prenotazione = %s", (id_prenotazione,))
    connection.commit()
    cursor.close()
    connection.close()
    
def get_magazzino():
    connection = psycopg2.connect(url)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT nome_ingrediente, quantità_stock, id_magazzino FROM Stock")
    magazzino = cursor.fetchall()
    cursor.close()
    connection.close()
    return magazzino

@app.route('/magazzino', methods=['GET', 'POST'])
def gestione_magazzino():
    if request.method == 'POST':
        # Gestione dell'aggiunta di un nuovo ingrediente
        nuovo_ingrediente = request.form['nome_ingrediente']
        nuova_quantita = float(request.form['quantita'])
        id_magazzino = request.form['id_magazzino']
        aggiungi_ingrediente(nuovo_ingrediente, nuova_quantita, id_magazzino)
        # Aggiorna la lista degli ingredienti
        magazzino = get_magazzino()
        return render_template('magazzino.html', magazzino=magazzino)
    else:
        # Mostra la pagina di gestione del magazzino
        magazzino = get_magazzino()
        return render_template('magazzino.html', magazzino=magazzino)
def aggiungi_ingrediente(nome_ingrediente, quantita, id_magazzino):
    connection = psycopg2.connect(url)
    cursor = connection.cursor()
    try:
        
        cursor.execute("""
            UPDATE Stock 
            SET quantità_stock = quantità_stock + %s 
            WHERE nome_ingrediente = %s AND id_magazzino = %s
        """, (quantita, nome_ingrediente, id_magazzino))
        
        
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO Stock (nome_ingrediente, quantità_stock, id_magazzino) 
                VALUES (%s, %s, %s)
            """, (nome_ingrediente, quantita, id_magazzino))
        
        connection.commit()
    except Exception as e:
        connection.rollback()
        print(f"Errore nell'aggiunta dell'ingrediente: {e}")
    finally:
        cursor.close()
        connection.close()
if __name__ == '__main__':
    app.run()
