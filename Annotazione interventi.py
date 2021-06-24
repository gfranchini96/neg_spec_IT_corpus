#!/usr/bin/env python
# coding: utf-8

# In[1]:


import copy
import re
import xml.etree.ElementTree as ET
import stanza
from diaparser.parsers import Parser
parser = Parser.load('it_isdt.dbmdz-electra-xxl')


# In[2]:


nlp = stanza.Pipeline(lang='it', processors ='tokenize')


# In[3]:


numero_legislatura = str(18)
numero_seduta = str(1)
tree = ET.parse('Resoconti/legislatura_{}/seduta_{}.xml'.format(numero_legislatura, numero_seduta))
seduta = tree.getroot()
seduta_da_analizzare = False
if len(list(seduta.iter("intervento"))) > 0:
    seduta_da_analizzare = True


# In[4]:


def scrittura_file(frase, token_counter, indici_da_saltare, cue, scope):
    with open(percorso_file, 'a', encoding='utf-8') as file:
        file.write(frase[0] + '\n' + frase[1] + '\n')
        for riga in frase[2:]:
            file.write(riga)
            if riga[0] != '#': # aggiunto per le frasi più lunghe di 490 parole sintattiche, che contengono righe di commento anche in mezzo alla lista (non solo nelle prime due posizioni)
                if len(indici_da_saltare) > 0:
                    numero_token_in_frase = riga.split('\t')[0]
                    da_annotare = True
                    if '-' in numero_token_in_frase:
                        file.write('\t_\t_\t_\n')
                        da_annotare = False
                    else:
                        numero_token_in_frase = int(numero_token_in_frase)
                        for coppia_indici in indici_da_saltare:
                            if numero_token_in_frase >= coppia_indici[0] and numero_token_in_frase <= coppia_indici[1]:
                                file.write("\t{}\tDESCR.\tDESCR.\n".format(token_counter))
                                da_annotare = False
                                token_counter += 1
                            break
                    if da_annotare:
                        file.write("\t{}\t{}\t{}\n".format(token_counter, cue, scope))
                        token_counter += 1
                else:
                    if '-' in riga.split('\t')[0]:
                        file.write('\t_\t_\t_\n')
                    else:
                        file.write("\t{}\t{}\t{}\n".format(token_counter, cue, scope))
                        token_counter += 1
    return token_counter


# In[5]:


"""
'frase' è una lista di stringhe. La lista è la frase dell'intervento ottenuta con diaparser, in formato CONLL-X; 
le stringhe contenute sono invece le righe della frase stessa (ottenute usando come separatore della frase '\n')
"""
def annotazione_frase(token_counter, frase, lista_frasi):
    indici_da_saltare = []
    sequenza_descrittiva = {}
    for riga in [line for line in frase if line[0] != '#']: # penso basti togliere le altre righe con # da questo ciclo, tanto il matching con il testo Connl-u viene fatto sulla base dell'indicazione del token che è salvato fra le chiavi (non sulla base dell'indice dell'elemento o della chiave)
        sequenza_descrittiva[riga.split('\t')[0]] = riga.split('\t')[1]
    for match in re.finditer(r'(\(.*?\))', " ".join(sequenza_descrittiva.values())):
        print("È una sequenza descrittiva?[d/descr/no]")
        print(match[0])
        print()
        da_analizzare = input()
        input_errato = True
        while input_errato:
            if da_analizzare in ('d','D','descr.','descr','DESCR','DESCR.'):
                input_errato = False
                indice_chiave_iniziale = (" ".join(sequenza_descrittiva.values()))[:match.span()[0]+1].count(" ")
                indice_chiave_finale = (" ".join(sequenza_descrittiva.values()))[:match.span()[1]].count(" ")
                indici_da_saltare.append((int(list(sequenza_descrittiva.keys())[indice_chiave_iniziale]), int(list(sequenza_descrittiva.keys())[indice_chiave_finale])))
            elif da_analizzare in ('N','n','no','No','NO','nO'):
                input_errato = False
            else:
                print("Input errato. Riprova [d/descr/no]:")
                print(match)
                da_analizzare = input()
    print(frase[1][9:])
    da_analizzare = input("Vuoi analizzare questa frase?[sì/no/forse]")
    input_errato = True
    while input_errato is True:
        if da_analizzare in ('N','n','no','No','NO','nO',''):
            input_errato = False
            token_counter = scrittura_file(frase, token_counter, indici_da_saltare,'O','_')
            print("Hai risposto di no.")    
        elif da_analizzare in ('sì','si','Sì','s','S','SI'):
            input_errato = False
            token_counter = scrittura_file(frase, token_counter, indici_da_saltare,' ',' ')
            print("Hai risposto di sì.")
        elif da_analizzare in ('dubbio', 'dub', 'forse','?'):
            input_errato = False
            token_counter = scrittura_file(frase, token_counter, indici_da_saltare,'?','?')
            print("Hai risposto forse.")
        elif da_analizzare in ('descr.', 'DESCR.', 'd', 'descr', 'DESCR'):
            input_errato = False
            token_counter = scrittura_file(frase, token_counter, indici_da_saltare, 'DESCR.','DESCR.')
            print("Hai risposto 'descrizione'.")
        else:
            print("Input errato. Riprova.")
            print(frase[1][9:])
            da_analizzare = input("Vuoi analizzare questa frase?[sì/no/forse]")
    return token_counter


# In[58]:


def analisi_frasi(numero_frase, token_counter, intervento):
    global log ###
    log = {} ###
    log['counter_frasi'] = 0 ####
    testo_intervento = intervento.text
    diz_frasi = {}
    doc = nlp(testo_intervento)
    indice_finale_frase_precedente = 0
    for frase in doc.sentences:
        log['counter_frasi'] += 1 ####
        lista_parole = frase.words
        if len(lista_parole) >= 450:
            print("Trovato frase più lunga di 449 parole sintattiche (andrà ricontrollata l'analisi sintattica): \n\tNo. seduta: {}, \n\tId intervento: {},\n\tInizio frase:'{}'\n\tFine frase:'{}')".format(seduta.attrib['numero'], intervento.attrib['id'], frase.text[:15], frase.text[-15:]))
            indice_iniziale_frase = int(lista_parole[0].misc[lista_parole[0].misc.find("=")+1:lista_parole[0].misc.find("|")])
            indice_finale_frase = int(lista_parole[-1].misc[lista_parole[-1].misc.find("=")+1:lista_parole[-1].misc.find("|")])
            if indice_iniziale_frase != indice_finale_frase_precedente:
                if re.fullmatch(r'\s+',testo_intervento[indice_finale_frase_precedente:indice_iniziale_frase]) is None:
                    diz_frasi[indice_finale_frase_precedente] = testo_intervento[indice_finale_frase_precedente:indice_iniziale_frase]
            indice_finale_frase_precedente = int(lista_parole[-1].misc[lista_parole[-1].misc.rfind("=")+1:]) # cambiato da 'indice_finale_frase_precedente = len(frase.text)', inserito all'interno dell'if qui sopra
            frase_lunga = []
            numero_iterazioni = int(len(lista_parole)/450)
            if len(lista_parole)%450 != 0:
                numero_iterazioni += 1
            indice_parola_iniziale = 0
            log['numero blocchi previsto (frase {})'.format(log['counter_frasi'])] = numero_iterazioni
            log['lunghezza lista parole (frase {})'.format(log['counter_frasi'])] = len(lista_parole)
            for i in range(numero_iterazioni):
                indice_iniziale_blocco = int(lista_parole[indice_parola_iniziale].misc[lista_parole[indice_parola_iniziale].misc.find("=")+1:lista_parole[indice_parola_iniziale].misc.find("|")])
                if i < numero_iterazioni-1:
                    # indice_finale_blocco dev'essere escluso: è l'indice del primo carattere dopo la parola
                    indice_finale_blocco = int(lista_parole[indice_parola_iniziale+449].misc[lista_parole[indice_parola_iniziale+449].misc.rfind("=")+1:])
                    blocco_frase = testo_intervento[indice_iniziale_blocco:indice_finale_blocco]
                    indice_parola_iniziale += 450
                else:
                    blocco_frase = testo_intervento[indice_iniziale_blocco:indice_finale_frase]
                log['blocco frase no. {} (frase {}):'.format(i, log['counter_frasi'])] = blocco_frase ###
                frase_diaparser = [str(sentence).split('\n')[2:-1] for sentence in parser.predict(blocco_frase, text='it').sentences]
                if len(frase_diaparser) > 1:
                    print("Diaparser ha risplittato la frase ottenuta con Stanza. Procedo a riunirla.")
                    for frase in frase_diaparser[1:]:
                        frase_diaparser[0].extend(frase)
                    frase_diaparser = frase_diaparser[0]
                frase_diaparser.insert(0,'# sent_id = *.{}'.format(i+1))
                frase_diaparser.insert(1, "# text = " + blocco_frase)
                frase_lunga.append(frase_diaparser)
            diz_frasi[indice_iniziale_frase] = frase_lunga
            log['diz_frasi'] = diz_frasi ####
    if bool(diz_frasi) is True:
        indici_frasi_analizzate = sorted(diz_frasi.keys())
        for indice in indici_frasi_analizzate:
            if isinstance (diz_frasi[indice], str):
                blocco_testo_intervento = diz_frasi[indice]
                for counter, frase_diaparser in enumerate([str(sentence).split('\n')[:-1] for sentence in parser.predict(blocco_testo_intervento, text='it').sentences]):
                    diz_frasi[indice + counter] = frase_diaparser
                    log['diz_frasi'] = diz_frasi ####
        indici_frasi_analizzate = sorted(diz_frasi.keys())
        for indice in indici_frasi_analizzate:
            if isinstance (diz_frasi[indice], list):
                frase_completa = []
                for num_blocco, blocco_frase in enumerate(diz_frasi[indice]):
                    blocco_frase[0] = blocco_frase[0].replace('*',str(numero_frase))
                    if num_blocco !=0:
                        for num_riga,riga in enumerate(blocco_frase[2:]):
                            numero_precedente = riga.split('\t')[0]
                            if '-' in numero_precedente:
                                nuovo_numero = ""
                                numeri_precedenti = [match[0] for match in re.finditer(r'[0-9]+',numero_precedente)]
                                for cnt, match in enumerate(numeri_precedenti):
                                    nuovo_numero += str(int(match[0])+int(num_token_frase_precedente))
                                    if cnt < len(numeri_precedenti)-1:
                                        nuovo_numero += '-'
                            else:
                                nuovo_numero = str(int(numero_precedente)+num_token_frase_precedente)
                            blocco_frase[num_riga] = riga.replace(numero_precedente, nuovo_numero, 1)
                    num_token_frase_precedente = blocco_frase[-1].split('\t')[0]
                    if '-' in num_token_frase_precedente:
                        # il -1 è necessario perché il prossimo token (il primo della prossima frase) non è il token successivo, 
                        # ma il token della prima parola sintattica che compone l'ultimo (multi-word) token di questa frase 
                        # --> il numero non deve progredire
                        num_token_frase_precedente = int(num_token_frase_precedente[:num_token_frase_precedente.find('-')])-1 
                    frase_completa.extend(blocco_frase)
                # Probabilmente devi tener conto del fatto che ci sono 
                # righe (quelle con l'asterisco) che non devono essere trattate come le altre e non sono necessariamente le prime due
                token_counter = annotazione_frase(token_counter,frase_completa)
            else:
                numero_frase_annotato = re.search(r'[0-9]+', diz_frasi[indice][0])[0]
                diz_frasi[indice][0].replace(numero_frase_annotato, str(numero_frase))
                token_counter = annotazione_frase(token_counter, diz_frasi[indice])
            numero_frase += 1
    else:
        lista_frasi = [str(sentence).split('\n')[:-1] for sentence in parser.predict(testo_intervento, text='it').sentences]
        for frase in lista_frasi:
            token_counter = annotazione_frase(token_counter, frase, lista_frasi)
    # return token_counter


# In[59]:


def gestione_intervento(intervento):
    with open(percorso_file,'a', encoding='utf-8') as file:
        riga_iniziale = '# INTERVENTO NUMERO {}\n'.format(numero_intervento)
        file.write(riga_iniziale)
        file.write('# id="' + intervento.attrib['id'] + '"' + ' cognomeNome="' + intervento.attrib['cognomeNome'] + '"')
        if intervento.attrib['tipo'] == 'parlamentare':
            file.write(' partito="' + intervento.attrib['partito'] + '"\n')
        elif intervento.attrib['tipo'] in ('procedurale','extra_parlamentare'):
            file.write(' qualifica="' + intervento.attrib['qualifica'] + '"\n')
        else:
            file.write("\n")
    analisi_frasi(1, 1, intervento) # eliminato "token_counter =" perché non mi pare lo riusassi dopo


# In[60]:


if seduta_da_analizzare:
    percorso_file = 'Resoconti_annotati/legislatura_{}/{}.tsv'.format(numero_legislatura, numero_seduta)
    file_esiste = False
    try:
        with open(percorso_file, 'x', encoding='utf-8') as file:
            legenda = "ID\tFORM\tLEMMA\tCPOS\tPOS\tFEATS\tHEAD\tDEPREL\tPHEAD\tPDEPREL\tID_TOKEN_NELL_INTERVENTO\tCUE\tSCOPE\n"
            file.write(legenda)
    except FileExistsError:
        file_esiste = True
        finisce_con_titolo = False
        with open(percorso_file, 'r', encoding='utf-8') as file:
            riga = file.readline()
            ultima_riga = ""
            while(riga != ""):
                if '# INTERVENTO NUMERO' in riga:
                    num_int_finale = int(re.search(r'[0-9]+', riga)[0])
                    num_frase_finale = 0
                    intervento = list(seduta.iter("intervento"))[num_int_finale]
                elif '# text =' in riga:
                    intervento.text = intervento.text.replace(riga[riga.index('=')+2:],"")
                elif '# sent_id' in riga:
                    num_frase_finale = int(re.search(r'[0-9]+', riga)[0])
                ultima_riga = riga
                riga = file.readline()
        if '# Titolo' in ultima_riga:
            finisce_con_titolo = True
        elif '# ' in ultima_riga:
            token_counter = 1
        else:
            token_counter = int(ultima_riga.split("\t")[10])+1
        if finisce_con_titolo is False:
            numero_intervento = num_int_finale
            intervento.text = intervento.text.strip()
            analisi_frasi(num_frase_finale+1, token_counter, intervento) # eliminato "token_counter =" perché non mi pare lo riusassi dopo
    if file_esiste:
        numero_intervento = num_int_finale+1
        if finisce_con_titolo:
            el_iniziale = list(seduta.iter('intervento'))[num_int_finale+1]
            for counter, Element in enumerate(seduta.find('resoconto').iter()):
                if Element.tag == 'intervento' and Element.attrib['id'] == el_iniziale.attrib['id']:
                    num_el_iniziale = counter
                    break
        else:
            el_iniziale = list(seduta.iter('intervento'))[num_int_finale]
            for counter, Element in enumerate(seduta.find('resoconto').iter()):
                if Element.tag == 'intervento' and Element.attrib['id'] == el_iniziale.attrib['id']:
                    num_el_iniziale = counter + 1
                    break
        for Element in list(seduta.find('resoconto').iter())[num_el_iniziale:]:
            if Element.tag == 'intervento':
                gestione_intervento(Element)
                numero_intervento += 1
            elif Element.tag == 'dibattito':
                span_titolo = str(len(list(Element.iter('intervento'))))
                with open(percorso_file, 'a', encoding='utf-8') as file:
                    file.write("# Titolo per i prossimi {} interventi: ".format(span_titolo) + Element.find('titolo').text + "\n")
            elif Element.tag == 'fase':
                span_titolo = str(len(list(Element.iter('intervento'))))
                with open(percorso_file,'a', encoding='utf-8') as file:
                    file.write("# Titolo per i prossimi {} interventi: ".format(span_titolo) + Element.find('titolo').text + "\n")
    else:
        with open(percorso_file, 'a', encoding='utf-8') as file:
            file.write("#")
            for key, value in seduta.attrib.items():
                file.write(' ' + key + '="' + value +'"')
            file.write("\n")
        numero_intervento = 0
        for Element in list(seduta.find('resoconto').iter()):
            if Element.tag == 'intervento':
                gestione_intervento(Element)
                numero_intervento += 1
            elif Element.tag == 'dibattito':
                span_titolo = str(len(list(Element.iter('intervento'))))
                with open(percorso_file,'a', encoding='utf-8') as file:
                    file.write("# Titolo per i prossimi {} interventi: ".format(span_titolo) + Element.find('titolo').text + "\n")
            elif Element.tag == 'fase':
                span_titolo = str(len(list(Element.iter('intervento'))))
                with open(percorso_file,'a', encoding='utf-8') as file:
                    file.write("# Titolo per i prossimi {} interventi: ".format(span_titolo) + Element.find('titolo').text + "\n")


# In[61]:


log


# In[68]:


ds = parser.predict(log['blocco frase no. 0 (frase 23):'], text = 'it')


# Provo a vedere se, diminuendo la lunghezza del testo, diaparser è in grado di gestirlo (ho dovuto assegnare il testo a una nuova variabile perché dopo l'esecuzione delle celle precedenti ho chiuso la sessione - ho recuperato il testo dall'output delle celle):

# In[12]:


testo_incriminato = "L'Abbate Giuseppe La Marca Francesca Labriola Vincenza Lacarra Marco Lapia Mara Latini Giorgia Lattanzio Paolo Lazzarini Arianna Legnaioli Donatella Lepri Stefano Librandi Gianfranco Licatini Caterina Liuni Marzio Liuzzi Mirella Lo Monte Carmelo Locatelli Alessandra Lolini Mario Lollobrigida Francesco Lombardo Antonio Longo Fausto Lorefice Marialucia Lorenzin Beatrice Lorenzoni Eva Lorenzoni Gabriele Losacco Alberto Lotti Luca Lovecchio Giorgio Lucaselli Ylenja Lucchini Elena Lupi Maurizio Maccanti Elena Macina Anna Madia Maria Anna Maggioni Marco Magi Riccardo Maglione Pasquale Mammì Stefania Manca Alberto Manca Gavino Mancini Claudio Mandelli Andrea Maniero Alvise Manzato Franco Manzo Teresa Maraia Generoso Marattin Luigi Marchetti Riccardo Augusto Mariani Felice Marin Marco Marino Bernardo Marrocco Patrizia Martina Maurizio Martinciglio Vita Martino Antonio Marzana Maria Maschio Ciro Masi Angela Maturi Filippo Mauri Matteo Mazzetti Erica Melicchio Alessandro Melilli Fabio Meloni Giorgia Menga Rosa Miceli Carmelo Micillo Salvatore Migliore Gennaro Migliorino Luca Milanato Lorena Minardo Antonino Minniti Marco Misiti Carmelo Massimo Molinari Riccardo Mollicone Federico Molteni Nicola Montaruli Augusta Mor Mattia Morani Alessia Morassut Roberto Morelli Alessandro Morgoni Mario Morrone Jacopo Moschioni Daniele Mugnai Stefano Mulè Giorgio Mura Andrea Mura Romina Murelli Elena Muroni Rossella Musella Graziano Nanni Iolanda Napoli Osvaldo Nappi Silvana Nardi Martina Navarra Pietro Nesci Dalila Nevi Raffaele Nitti Michele Nobili Luciano Noja Lisa Novelli Roberto Occhionero Giuseppina Occhiuto Roberto Olgiati Riccardo Orfini Matteo Orlando Andrea Orrico Anna Laura Orsini Andrea Osnato Marco Padoan Pietro Carlo Pagani Alberto Pagano Alessandro Pagano Ubaldo Paita Raffaella Palazzotto Erasmo Pallini Maria Palmieri Antonio Palmisano Valentina Panizzut Massimiliano Paolini Luca Rodolfo Papiro Antonella Parentela Paolo Parisse Martina Parolo Ugo Pastorino Luca Patassini Tullio Patelli Cristina Paternoster Paolo Paxia Maria Laura Pedrazzini Claudio Pella Roberto Pellicani Nicola Pentangelo Antonio Perantoni Mario Perconti Filippo Giuseppe Perego Di Cremnago Matteo Pettarin Guido Germano Pettazzi Lino Pezzopane Stefania Piastra Carlo Picchi Guglielmo Piccoli Nardelli Flavia Pignatone Dedalo Cosimo Gaetano Pini Giuditta Pittalis Pietro Pizzetti Luciano Plangger Albrecht Polidori Catia Pollastrini Barbara Polverini Renata Porchietto Claudia Portas Giacomo Potenti Manfredi Prestigiacomo Stefania Prestipino Patrizia Pretto Erik Umberto Prisco Emanuele Provenza Nicola Quartapelle Procopio Lia Racchella Germano Raciti Fausto Raduzzi Raphael Raffa Angela Raffaelli Elena Rampelli Fabio Ribolla Alberto Ricciardi Riccardo Ripani Elisabetta Rixi Edoardo Rizzetto Walter Rizzo Gianluca Rizzo Nervo Luca Rizzone Marco Romaniello Cristian Romano Andrea Romano Paolo Nicolò Rosato Ettore Rospi Gianluca Rossello Cristina Rossi Andrea Rossini Emanuela Rossini Roberto Rosso Roberto Rostan Michela Rotelli Mauro Rotondi Gianfranco Rotta Alessia Ruffino Daniela Ruggieri Andrea Ruggiero Francesca Anna Ruocco Carla Russo Giovanni Russo Paolo Saccani Jotti Gloria M.R. Saitta Eugenio Salafia Angela Saltamartini Barbara Sangregorio Eugenio Santelli Jole Sapia Francesco Sarli Doriana Sarro Carlo Sarti Giulia Sasso Rossano Savino Elvira Savino Sandra Scagliusi Emanuele Scalfarotto Ivan Scanu Lucia Scerra Filippo Schirò Angela Schullian Manfred Scoma"


# In[10]:


ds = parser.predict(" ".join(testo_incriminato.split(' ')[:400]), text = 'it')


# Anche con 401 parole (L'Abbate viene scomposto in L' + Abbate), diaparser dà errore.
# Proviamo con 350:

# In[13]:


ds = parser.predict(" ".join(testo_incriminato.split(' ')[:350]), text = 'it')


# Con 201:

# In[14]:


ds = parser.predict(" ".join(testo_incriminato.split(' ')[:200]), text = 'it')


# In[15]:


ds


# In[20]:


ds.sentences


# In[16]:


ds2 = parser.predict(" ".join(testo_incriminato.split(' ')[200:400]), text = 'it')


# In[17]:


ds2


# In[21]:


ds2.sentences


# In[18]:


ds3 = parser.predict(" ".join(testo_incriminato.split(' ')[400:]), text = 'it')


# In[19]:


ds3


# In[22]:


ds3.sentences

