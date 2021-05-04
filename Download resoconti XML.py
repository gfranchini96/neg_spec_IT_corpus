#!/usr/bin/env python
# coding: utf-8

# N.B. Ho osservato che nei file XML salvati nel mio computer a volte scomparivano degli spazi (es. 'dellaRenault' in luogo di 'della Renault' nel resoconto numero 9 della legislatura numero 18 o 'diroutine' in luogo di 'di routine' nel resoconto 18 della stessa legislatura), mi pare sempre prima di una parola che era contenuta in un tag \\<emphasis\>\. Ho debuggato passo passo e la scomparsa dello spazio non si verificava prima del metodo .write(), il che significa che è dovuta al metodo stesso o ad altro che non so come risolvere. Come soluzione di comodo, ho aggiunto uno spazio in testa al testo di ogni tag \\<emphasis\>\, il che sembra funzionare.

# In[1]:


from urllib.request import urlopen
from lxml import etree
import re
import copy


# In[2]:


regex_sigla = re.compile('\([^a-z]+?\) *\.?')
regex_virgola_punto = re.compile('\s*[,.]?\s*')
regex_punto = re.compile('\s*\.')
def pulitura_intervento(Element_intervento, attributi):
    testo_senza_tag = re.sub(" +"," ",re.sub('[\t\n]',"",re.sub('(?<!\t| )\n(?! )'," ",etree.tostring(Element_intervento, encoding='unicode', method='text'))))
    indentazione = re.search('[\t\n]+', Element_intervento.tail)[0]
    Element_intervento.clear()
    # per le quattro righe qua sotto si potrebbero usare invece le re
    Element_intervento.text = testo_senza_tag.strip()
    if Element_intervento.text[0] == '.' or Element_intervento.text[0] == ',':
        Element_intervento.text = Element_intervento.text[1:]
    Element_intervento.text = Element_intervento.text.strip()
    Element_intervento.tail = indentazione
    for key,value in attributi.items():
        Element_intervento.attrib[key] = value
    return

''' 

Questa funzione serve a capire con che tipo di intervento si ha a che fare e trattarlo conseguentemente

Riposa sull'assunto che gli interventi siano tutti riconducibili a quattro tipi: parlamentari (dove appare una sigla del 
tipo (PD) nella coda - 'tail'- del tag <nominativo>), procedurali 1 (in cui il testo del tag <nominativo> non è il 
nome e cognome,  controintuitivamente, ma la qualifica di chi parla (es. PRESIDENTE)), procedurali 2 (in cui il testo del tag 
<nominativo> è il nome e cognome e la qualifica di chi parla è inserita nel tag <emphasis> che segue dopo una virgola) e di 
esterni (in cui la qualifica di chi parla è inserita nel tag <emphasis> che segue il tag <nominativo> dopo una virgola).
È comunque previsto un caso di fallback.

'''

def gestione_intervento(Element_intervento, Element_padre):
    for Element in Element_intervento.iter('nominativo'):
        nodo_nominativo = Element
        break
    descrizioni = []
    for Element_emphasis in Element_intervento.iter('emphasis'):
        if re.match("\(.*\)",Element_emphasis.text): 
            # per eliminare le descrizioni degli stenografi su cosa sta accadendo in aula, che sembrano essere sempre inseriti in un tag emphasis ed inclusi in parentesi tonde.
            # ritengo bassa la probabilità di falsi positivi perché sarebbe strano mettere in italico anche le parentesi in altri casi.
            descrizioni.append(Element_emphasis)
        else: Element_emphasis.text =" "+ Element_emphasis.text
    for descrizione in descrizioni:
        descrizione.getparent().remove(descrizione)
    attributi = copy.deepcopy(Element_intervento.attrib)
    attributi['idNominativo'] = nodo_nominativo.attrib['id']
    attributi['cognomeNome'] = nodo_nominativo.attrib['cognomeNome']
    #intervento parlamentare
    stringa_controllo = nodo_nominativo.tail.strip()
    for token in stringa_controllo.split()[0:3]:
        if regex_sigla.match(token) is not None:
            sigla = regex_sigla.match(token)[0].strip(".")
            attributi['tipo'] = 'parlamentare'
            attributi['partito'] = sigla
            nodo_nominativo.tail = regex_sigla.sub("", nodo_nominativo.tail).strip()
            nodo_nominativo.text = None
            pulitura_intervento(Element_intervento, attributi)
            return
    # intervento extra_parlamentare o procedurale (caso di 'Segretario/a')
    # N.B. questo approccio fallisce nel caso in cui ci sia un tag emphasis prima del tag emphasis che racchiude la
    # qualifica di chi parla. Mi sembrava improbabile al punto da non poter accadere, ma nella seduta 28 della legislatura
    # 18, all'intervento con id tit00050.sub00020.int00090 e quello successivo si trova un tag emphasis che racchiude 
    # una sola virgola prima del tag emphasis che racchiude la qualifica. Penso si tratti di un errore, per cui procedo
    # a correggerlo a mano e aggiungere una struttura di avvertimento (con un print) nei casi in cui la qualifica risulti
    # strana (es. vuota, una virgola ecc.)
    if nodo_nominativo.getnext() is not None and regex_virgola_punto.fullmatch(nodo_nominativo.tail) is not None and nodo_nominativo.getnext().tag == 'emphasis':
        nodo_qualifica = nodo_nominativo.getnext()
        if re.match(",? ?[Ss]egretari[oa]",nodo_qualifica.text.strip()) is not None:
            attributi['tipo'] = 'procedurale'
            nodo_qualifica.tail = regex_virgola_punto.sub("", nodo_qualifica.tail, count = 1).strip()
        else: attributi['tipo'] = 'extra_parlamentare'
        attributi['qualifica'] = nodo_qualifica.text.strip().strip(",").strip()
        if attributi['qualifica'] in (',','.',''):
            print("Qualifica anomala per l'intervento con id {} della seduta numero {}.".format(Element_intervento.attrib['id'],seduta.attrib['numero']))
        nodo_nominativo.tail = None
        nodo_nominativo.text = None
        nodo_qualifica.text = None
        pulitura_intervento(Element_intervento, attributi)
        return
    # intervento procedurale
    if sorted(nodo_nominativo.attrib['cognomeNome'].upper().split()) != sorted(nodo_nominativo.text.split()):
        attributi['tipo'] = 'procedurale'
        attributi['qualifica'] = nodo_nominativo.text
        nodo_nominativo.tail = regex_punto.sub("",nodo_nominativo.tail, count=1)
        nodo_nominativo.text = None
        pulitura_intervento(Element_intervento, attributi)
        return
    # intervento parlamentare (troncato)
    if re.match(r' *?…', re.sub(r'[\t\n]',"", nodo_nominativo.tail)) is not None:
        lista_interventi_precedenti = list(list(Element_padre.iterancestors('seduta'))[0].iter('intervento'))
        lista_interventi_precedenti = lista_interventi_precedenti[lista_interventi_precedenti.index(Element_intervento)-4:lista_interventi_precedenti.index(Element_intervento)]
        lista_interventi_precedenti.reverse()
        for intervento_precedente in lista_interventi_precedenti:
            if intervento_precedente.attrib['tipo'] == 'parlamentare' and intervento_precedente.attrib['idNominativo'] == nodo_nominativo.attrib['id']:
                attributi['tipo'] = 'parlamentare'
                attributi['partito'] = intervento_precedente.attrib['partito']
                nodo_nominativo.text = None
                pulitura_intervento(Element_intervento, attributi)
                return
    #caso generico
    attributi['tipo'] = 'altro'
    nodo_nominativo.text = None
    pulitura_intervento(Element_intervento, attributi)
    numero_seduta = seduta.attrib['numero']
    print("Trovato intervento anomalo nella seduta numero {}; l'intervento inizia così: '{}...'".format(numero_seduta, Element_intervento.text[:70]))
    return


# In[3]:


num_legislatura = str(18)
for num_seduta in range(1, 30):
    indirizzo_web = "http://documenti.camera.it/apps/resoconto/getXmlStenografico.aspx?idNumero=00{}&idLegislatura={}".format(num_seduta, num_legislatura)
    xml = urlopen(indirizzo_web).read()
    seduta = etree.fromstring(xml)
    # rimuove tag per la data estesa (inutile perché la data è già negli attributi di <seduta>)
    seduta[0].remove(seduta[0].find('dataEstesa'))
    tag_da_tenere = ['intervento', 'dibattito']
    for Element in seduta[1]:
        if Element.tag not in tag_da_tenere:
            seduta[1].remove(Element)
    tag_da_tenere = ['titolo','fase','intervento']
    file_da_salvare = False
    for Element in seduta[1]:
        if Element.tag == 'dibattito':
            da_salvare = False
            for Element2 in Element:
                if Element2.tag == 'intervento':
                    da_salvare = True
                    file_da_salvare = True
                    gestione_intervento(Element2, Element)    
                elif Element2.tag == 'fase':
                    fase_da_salvare = False
                    for Element3 in Element2:
                        if Element3.tag == 'intervento':
                            fase_da_salvare = True
                            da_salvare = True
                            file_da_salvare = True
                            gestione_intervento(Element3, Element2)
                        elif Element3.tag not in tag_da_tenere:
                            Element2.remove(Element3)
                    # se la fase contiene solo elementi che sono stati eliminati, viene eliminata anch'essa
                    if fase_da_salvare is False:
                        Element.remove(Element2)
                elif Element2.tag not in tag_da_tenere:
                    Element.remove(Element2)
            # se il dibattito contiene solo elementi che sono stati eliminati, viene eliminato anch'esso
            if da_salvare is False:
                seduta[1].remove(Element)
        else: gestione_intervento(Element, seduta[1])
    if file_da_salvare is True:
        seduta_albero = etree.ElementTree(seduta)
        seduta_albero.write('Resoconti/legislatura_{}/seduta_{}.xml'.format(num_legislatura,num_seduta), encoding ='utf-8')
    else:
        print("Seduta {} non salvata perché priva di interventi.".format(num_seduta))


# <h1> VECCHI </h1>

# In[36]:


regex_sigla = re.compile(r'\([^a-z]+?\) *\.?')

# scelto di salvare solo interventi di parlamentari di cui era riportato il partito
# gli altri interventi sono o di extra-parlamentari o di ordine procedurale, a quanto ho potuto vedere
# gli interventi di extra-parlamentari sarebbero interessanti da vedere e salvare; quelli procedurali
# sarebbero inutili, credo, perché sono ripetitivi e cerimoniali.
# comunque per il momento fatta questa selezione
def gestione_intervento(Element_intervento, Element_padre):
    da_salvare = False
    nodo_nominativo = None
    sigla = ""
    for Element_nominativo in Element_intervento.iter('nominativo'):
        stringa_controllo = Element_nominativo.tail.strip()
        for token in stringa_controllo.split()[0:3]:
            if regex_sigla.match(token) is not None:
                sigla = regex_sigla.match(token)[0].strip(".")
                nodo_nominativo = Element_nominativo
                da_salvare = True
                break
    if da_salvare:
        nodo_nominativo.text = None
        nodo_nominativo.tail = regex_sigla.sub("", nodo_nominativo.tail).strip()
        testo_senza_tag = re.sub(r'[\t\n]',"",etree.tostring(Element_intervento, encoding='unicode', method='text'))
        attributi = copy.deepcopy(Element_intervento.attrib)
        attributi['partito'] = sigla
        attributi['idNominativo'] = nodo_nominativo.attrib['id']
        attributi['cognomeNome'] = nodo_nominativo.attrib['cognomeNome']
        indentazione = re.search(r'[\t\n]+', Element_intervento.tail)[0]
        Element_intervento.clear()
        Element_intervento.text = testo_senza_tag 
        Element_intervento.tail = indentazione
        for key,value in attributi.items():
            Element_intervento.attrib[key] = value
    else:
        Element_padre.remove(Element_intervento)
    return da_salvare


# In[39]:


num_legislatura = str(18)
for num_seduta in range(20,30):
    indirizzo_web = "http://documenti.camera.it/apps/resoconto/getXmlStenografico.aspx?idNumero=00{}&idLegislatura={}".format(num_seduta, num_legislatura)
    xml = urlopen(indirizzo_web).read()
    seduta = etree.fromstring(xml)
    # rimuove tag per la data estesa (inutile perché la data è già negli attributi di <seduta>)
    seduta[0].remove(seduta[0].find('dataEstesa'))
    tag_da_tenere = ['intervento', 'dibattito']
    for Element in seduta[1]:
        if Element.tag not in tag_da_tenere:
            seduta[1].remove(Element)
    tag_da_tenere = ['titolo','fase','intervento']
    file_da_salvare = False
    for Element in seduta[1]:
        if Element.tag == 'dibattito':
            da_salvare = False
            for Element2 in Element:
                if Element2.tag == 'intervento':
                    if gestione_intervento(Element2, Element):
                        da_salvare = True
                        file_da_salvare = True
                elif Element2.tag == 'fase':
                    fase_da_salvare = False
                    for Element3 in Element2:
                        if Element3.tag == 'intervento':
                            if gestione_intervento(Element3, Element2):
                                fase_da_salvare = True
                                da_salvare = True
                                file_da_salvare = True
                        elif Element3.tag not in tag_da_tenere:
                            Element2.remove(Element3)
                    # se la fase contiene solo interventi che sono stati eliminati, viene eliminata anch'essa
                    if fase_da_salvare is False:
                        Element.remove(Element2)
                elif Element2.tag not in tag_da_tenere:
                    Element.remove(Element2)
            # se il dibattito contiene solo interventi che sono stati eliminati, viene eliminato anch'esso
            if da_salvare is False:
                seduta[1].remove(Element)
        else: gestione_intervento(Element, seduta[1])
    if file_da_salvare is True:
        seduta_albero = etree.ElementTree(seduta)
        seduta_albero.write('Resoconti/legislatura_{}/seduta_{}.xml'.format(num_legislatura,num_seduta), encoding ='utf-8')
    else:
        print("Seduta {} non salvata perché priva di interventi di parlamentari 'politici'.".format(num_seduta))

