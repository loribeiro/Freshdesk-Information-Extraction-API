import json
import requests
import csv
import getpass
from datetime import datetime
"""
    Autor: Lucas de Oliveira Ribeiro
    Data: 03/09/2019
    Descrição: API responsável por recuperar estatísticas sobre artigos criados no FreshDesk
    Dependência: A aplicação utiliza um arquivo no formato json para recuperar as credênciais e Url's utilizadas para as requisições
    Saída esperada: A aplicação deverá retornar um arquivo chamado "estatisticas.csv" com todas as informações extraidas dos artigos

"""
def permission(e , p):
     r = requests.get("https://"+"tecnotrends.freshdesk.com/api/v2/solutions/categories", auth = (e, p))
     return r


email = None
senha = None 


while True:
    e = input('digite seu email: ')
    p = getpass.getpass(prompt = 'digite seu password: ')
    if permission(e,p).status_code == 200:
        email = e
        senha = p 
        break
    else:
        print('Email ou senha inválidos, por favor tente novamente.')

config_dict = []
with open('config.json','r') as f:
    config_dict = json.load(f)

#Classe responsavel por guardar as informações dos artigos    
class Article:
    def __init__(self,agent_id, title, description,date, likes, dislikes, views , folder):
        self.agent_id = agent_id
        self.agent_name = None
        self.title = title
        self.description = description
        self.created_at = date
        self.thumbs_up = likes
        self.thumbs_down = dislikes
        self.hits = views
        self.folder = folder
        
#Classe responsável por guardar as informações dos analistas        
class Agent:
     def __init__(self,Id, name,email):
        self.Id = Id
        self.name = name
        self.email = email
        
#Classe responsável por armazenar as categorias em que o freshDesk foi dividido (Ex: Modulo Sagres, Ambiente , Desenvolvimento)
class Categories:
     def __init__(self,Id, name, description):
        self.Id = Id
        self.name = name
        self.description =description

        
# Classe responsável por armazenar as informações das pastas dentro das categorias       
class Folders:
     def __init__(self,Id, name, description):
        self.Id = Id
        self.name = name
        self.description =description

#Função responsável por fazer a requisição dos artigos dado o ID da pasta
def request_articles(ID):
    rest_of_url = config_dict["Url_Article"].replace("[ID_ARTICLE]",ID)
    #print(rest_of_url)
    pagina = 1
    while True:
        print("pagina = " + str(pagina))
        req = requests.get("https://"+ config_dict["domain"] + rest_of_url + "?page=" + str(pagina) , auth = (email, senha))
        print("tamanho da requisição "+ str(len(req.json())))
        if len(req.json()) > 0:
            if pagina == 1:
                r = req.json()
            else:
                r = r + req.json()
        else:
            break
        pagina = pagina+1
    return r

#Função responsável  por fazer a requisição das categorias 
def request_categories():
    r = requests.get("https://"+ config_dict["domain"] + config_dict["Url_Categories"], auth = (email, senha))  #(api_key, password))
    return r

#Função responsável  por fazer a requisição dos Analistas  
def request_agents():
    r = requests.get("https://"+ config_dict["domain"] + config_dict["Url_Agent"], auth = ("ResOfSqx4Z7GHRO5y3XQ", "x"))
    return r

#Função responsável  por fazer a requisição das pastas dado o ID da Categoria
def request_folders(ID):
    rest_of_url = config_dict["Url_Folders"].replace("[ID_Categories]",ID)
    r = requests.get("https://"+ config_dict["domain"] + rest_of_url, auth = (email, senha))
    return r

#Função responsável por retornar todos os analistas como uma lista
def agents(resposta):
    agents_set = []
    if resposta.status_code == 200:

      print ("Request processed successfully, the response is given below")
      a = resposta_agents.json()

      for x in a:
          #print(x['contact']['email'])
          agents_set.append(Agent(x['id'],x['contact']['name'],x['contact']['email']))

      return agents_set

    else:
      print ("Failed to read agents, errors are displayed below,")
      response = json.loads(r.content)
      print (response["errors"])
      print ("x-request-id : " + r.headers['x-request-id'])
      print ("Status Code : " + str(r.status_code))

#Função responsável por retornar todas as categorias como uma lista
def categories():

    categories_set = []
    resposta_categories = request_categories()

    if resposta_categories.status_code == 200:

      #print ("Request processed successfully, the response is given below")
      a = resposta_categories.json()

      for x in a:
          categories_set.append(Categories(x['id'],x['name'],x['description']))

      return categories_set

    else:
      print ("Failed to read categories, errors are displayed below,")
      response = json.loads(resposta_categories.content)
      print (response["errors"])
      print ("x-request-id : " + resposta_categories.headers['x-request-id'])
      print ("Status Code : " + str(resposta_categories.status_code))

#Função responsável por retornar todas as pastas como uma lista
def folders():

    folders_set = []

    for categoria in categories():

        a = request_folders(str(categoria.Id)).json()

        for folder in a:
            folders_set.append(Folders(folder['id'],folder['name'],folder['description']))
            #print(folder['name'])

    return folders_set

#função responsável por retornar todas os artigos como lista
def articles(pastas):

    articles_set = []

    for pasta in pastas:
        a = request_articles(str(pasta.Id))
        for artigo in a:
            #print(pasta.name)
            articles_set.append(Article(artigo['agent_id'],artigo['title'],artigo['description'],artigo['created_at'],artigo['thumbs_up'],artigo['thumbs_down'],artigo['hits'],pasta.name))

    return articles_set

#Inicio da área de cruzamento de informaçoes

resposta_agents = request_agents() #resposta_agents recebe o resultado da requisição dos analistas

analistas = agents(resposta_agents) # conjunto de todos os analistas
categorias = categories() # conjunto de todas as categorias 
pastas = folders()  # conjunto de todas as pastas 
artigos = articles(pastas) # conjunto de todos os artigos 
dicionario = {} # varíavel para evitar que entre no segundo for quando já se tem a informação
for artigo in artigos:
    if artigo.agent_name is None:
        if str(artigo.agent_id) in dicionario:
            artigo.agent_name = dicionario[str(artigo.agent_id)]
        else:
            for analista in analistas:
                if artigo.agent_id == analista.Id:
                    artigo.agent_name = analista.name
                    dicionario[str(artigo.agent_id)] = analista.name
                    break

#Fim da área de cruzamento de informações


#A variável linha é uma lista de listas que armazenará as linhas que serão impressas no arquivo csv
#A primeira linha é o cabeçalho do arquivo, informando os nomes das colunas
linha = [['Id do Analista','Nome do Analista', 'Titulo do Artigo', 'Data de Criação' , 'Likes' , 'Dislikes' , 'Visualizações', 'Pasta']]

for artigo in artigos:
    #d = datetime.strptime(artigo.created_at,'%Y-%m-%d %H:%M:%S')
    #day_string = d.strftime()
    day = (artigo.created_at).split('T')
    linha.append([str(artigo.agent_id) ,
                    artigo.agent_name ,
                    artigo.title ,
                    day[0] ,
                    str(artigo.thumbs_up), 
                    str(artigo.thumbs_down), 
                    str(artigo.hits) ,
                    str(artigo.folder) ])
    
#Arquivo é gravado com as linhas presentes na variavel linha
with open('estatisticas.csv', 'w', newline = '') as csvFile:
    writer = csv.writer(csvFile, quoting = csv.QUOTE_ALL )
    writer.writerows(linha)
csvFile.close()


