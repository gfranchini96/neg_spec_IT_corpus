#!/usr/bin/env python
# coding: utf-8

# Altra cosa molto utile potrebbe essere effettuare una segmentazione di frasi (altrimenti ti lasci da analizzare 
# anche frasi molto lunghe di cui ti interessa solo una piccola parte), o tramite un modello di NLP o tramite regole 
# euristiche (es. se la frase è più lunga di x token, separarla anche sulle virgole)

# In[1]:


import copy
import re
import spacy
import xml.etree.ElementTree as ET
tokenizer = spacy.load('it_core_news_sm').tokenizer


# In[2]:


interventi = {}
numero_legislatura = str(18)
numero_seduta = str(5)
tree = ET.parse('Resoconti/legislatura_{}/seduta_{}.xml'.format(numero_legislatura, numero_seduta))
seduta = tree.getroot()
seduta_da_analizzare = False
for intervento in seduta.iter("intervento"):
    if intervento.attrib['tipo'] != 'procedurale':
        seduta_da_analizzare = True
        break


# In[3]:


def annotazione_frase(counter_frasi, frase, lista_frasi_vuota = False):
    global token_counter
    global inizio_dumping
    if lista_frasi_vuota == False:
        if counter_frasi > 0:
            print("\nPREC.:" + lista_frasi[counter_frasi-1] + "FINE PREC.")    
        if counter_frasi < len(lista_frasi)-1:
            print("\nSUCC.:" + lista_frasi[counter_frasi+1] +"FINE SUCC.")
    print("\n" + frase)
    da_analizzare = input("Vuoi analizzare questa frase?[sì/no/forse]")
    print("\n\n\n")
    if da_analizzare in ('no','No','NO','nO',''):
        for token in [t.text for t in tokenizer(frase)]:
            interventi[numero_intervento].append((token_counter, token, "O", "-"))
            #interventi[numero_intervento].append((token_counter, token, "O", ("-",)))
            token_counter += 1
    elif da_analizzare in ('sì','si','Sì'):
        for token in [t.text for t in tokenizer(frase)]:
            cue = " "
            scopes =" "
            interventi[numero_intervento].append((token_counter, token, cue, scopes))
            token_counter += 1
    elif da_analizzare in ('dubbio', 'dub', 'forse'):
        for token in [t.text for t in tokenizer(frase)]:
            cue = "?"
            scopes ="?"
            interventi[numero_intervento].append((token_counter, token, cue, scopes))
            token_counter += 1
    if counter_frasi % 9 == 0:
        with open(percorso_file,'a', encoding='utf-8') as file:
            for token_tuple in interventi[numero_intervento][inizio_dumping:]:
                file.write(str(token_tuple[0]) + "\t" + token_tuple[1] +"\t" + token_tuple[2] + "\t" + token_tuple[3])
                file.write("\n")
        inizio_dumping = token_counter
    elif counter_frasi == (len(lista_frasi)-1) or lista_frasi is False:
        with open(percorso_file,'a', encoding='utf-8') as file:
            for token_tuple in interventi[numero_intervento][inizio_dumping:]:
                file.write(str(token_tuple[0])+"\t"+token_tuple[1] +"\t" + token_tuple[2] + "\t" + token_tuple[3])
                file.write("\n")


# In[4]:


if seduta_da_analizzare:
    percorso_file = 'Resoconti_annotati/legislatura_{}/{}.tsv'.format(numero_legislatura, numero_seduta)
    file_esiste = False
    try:
        with open(percorso_file, 'x', encoding='utf-8') as file:
            legenda = "ID\tTOKEN\tCUE\tSCOPES\n"
            file.write(legenda)
    except FileExistsError:
        file_esiste = True
        with open(percorso_file, 'r', encoding='utf-8') as file:
            riga = file.readline()
            ultima_riga = ""
            while(riga != ""):
                if re.match(r'\*\*\* INTERVENTO NUMERO [0-9]+ \*\*\*', riga) is not None:
                    intervento_iniziale = int(re.search(r'[0-9]+', riga)[0])
                ultima_riga = riga
                riga = file.readline()
            if re.match(r'\*\*\* INTERVENTO NUMERO [0-9]+ \*\*\*', ultima_riga) is not None:
                token_counter = 0
            else:
                token_counter = int(ultima_riga.split("\t")[0])+1
            intervento = list(seduta.iter("intervento"))[intervento_iniziale]
        if token_counter <= (len([t.text for t in tokenizer(intervento.text)]) - 1):
            numero_intervento = intervento_iniziale
            interventi[numero_intervento] = []
            testo = " ".join([t.text for t in tokenizer(intervento.text)][token_counter:])
            lista_frasi = re.findall(r".+?[….?!:;]", testo)
            inizio_dumping = 0
            if len(lista_frasi) == 0:
                annotazione_frase(1, testo, lista_frasi_vuota = True)
            else:
                for counter_frasi, frase in enumerate(lista_frasi):
                    annotazione_frase(counter_frasi, frase.strip())
            numero_intervento += 1
        else:
            numero_intervento = intervento_iniziale+1
    if file_esiste:
        for intervento in list(seduta.iter("intervento"))[numero_intervento:]:
            if intervento.attrib['tipo'] != 'procedurale':
                with open(percorso_file,'a', encoding='utf-8') as file:
                    riga_iniziale = '*** INTERVENTO NUMERO {} ***\n'.format(numero_intervento)
                    file.write(riga_iniziale)
                interventi[numero_intervento] = []
                lista_frasi = re.findall(r".+?[….?!:;]", intervento.text)
                token_counter = 0
                inizio_dumping = 0
                for counter_frasi, frase in enumerate(lista_frasi):
                    annotazione_frase(counter_frasi, frase.strip())
            numero_intervento += 1
    else:
        for numero_intervento, intervento in enumerate(seduta.iter("intervento")):
            if intervento.attrib['tipo'] != 'procedurale':
                with open(percorso_file,'a', encoding='utf-8') as file:
                    riga_iniziale = '*** INTERVENTO NUMERO {} ***\n'.format(numero_intervento)
                    file.write(riga_iniziale)
                interventi[numero_intervento] = []
                lista_frasi = re.findall(r".+?[….?!:;]", intervento.text)
                token_counter = 0
                inizio_dumping = 0
                for counter_frasi, frase in enumerate(lista_frasi):
                    annotazione_frase(counter_frasi, frase.strip())

