import pandas as pd
from openai import OpenAI,RateLimitError
import requests
import time
import random
from config import URL_BASE,USUARIO_SITE,SENHA_SITE,OPENAI_API_KEY

# Configurar os detalhes de autenticação e o URL do seu site WordPress
url_base = URL_BASE
usuario = USUARIO_SITE
senha = SENHA_SITE

# Configurar a chave da API
chave_api = OPENAI_API_KEY
client = OpenAI(api_key=chave_api)

#ESCOLHO DA ONDE PEGO OS DADOS
dados = pd.read_excel('posts.xlsx')
# Converter a coluna 'Link Wordpress' para o tipo 'object'
dados['Link Wordpress'] = dados['Link Wordpress'].astype('object')

# Gerar um nome único para a imagem
def gerar_nome_imagem():
    timestamp = str(int(time.time()))  # Obter timestamp atual em segundos
    aleatorio = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))  # Gerar parte aleatória
    return f'imagem_{timestamp}_{aleatorio}.jpg'

# Iterar sobre os dados
for indice, linha in dados.iterrows():
    if pd.isna(linha['Link Wordpress']):
        # Se o 'Link Wordpress' for nulo, fazer uma busca
        busca = linha['Keyword']
        try:
            #------------------------------------------------------
            #                      ARTIGO                         -
            #------------------------------------------------------
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": f"Escreva um artigo com no minimo 2000 palavras sobre o tema '{busca}'."},
                ]
            )
            titulo_artigo = busca
            conteudo_artigo = response.choices[0].message.content

            # Criar um novo post
            novo_post = {
                'title': titulo_artigo,
                'content':conteudo_artigo,
                'status': 'draft'
            }
            # Fazer uma solicitação POST para criar o post
            response = requests.post(
                url_base + 'posts',
                json=novo_post,
                auth=(usuario, senha)
            )
            id_artigo = 0
            if response.status_code == 201:
                id_artigo=response.json()['id']
                print('Post criado com sucesso!')
                print('ID do novo post:', response.json()['id'])
            else:
                print('Erro ao criar o post:', response.text)

            dados.at[indice, 'Link Wordpress'] = f'{URL_BASE}/wp-json/wp/v2/posts/{id_artigo}'
            dados['Link Wordpress'] = dados['Link Wordpress'].astype(str)

            #------------------------------------------------------
            #                      IMAGEM                         -
            #------------------------------------------------------
            if(id_artigo!=0):
                #-------------------------------------------------------
                #                      IMAGEM ARTIGO                  -
                #-------------------------------------------------------
                # response_imagem = client.images.generate(
                #     model="dall-e-3",
                #     prompt=f"A imagem que representa o tema '{busca}':\n",
                #     n=1,
                # )
                # Obter a URL da imagem gerada
                # url_imagem = response_imagem.data[0].url

                #UPLOAD PARA WODPRESS
                # nome_arquivo = gerar_nome_imagem()
                # with open(nome_arquivo, 'wb') as f:
                #     response_imagem = requests.get(url_imagem)
                #     f.write(response_imagem.content)

                # Fazer upload da imagem para o WordPress
                # dados_imagem = {
                #     'file': (nome_arquivo, open(nome_arquivo, 'rb'), 'image/jpeg'),
                # }
                # response_upload = requests.post(
                #     url_base + 'media',
                #     files=dados_imagem,
                #     auth=(usuario, senha)
                # )
                #-------------------------------------------------------
                #                      IMAGEM THUMB                  -
                #-------------------------------------------------------
                response_thumb = client.images.generate(
                    model="dall-e-3",
                    prompt=f"A imagem que representa o tema '{busca}':\n vai ser usada para capa do artigo.",
                    n=1,
                )
                # Obter a URL da imagem gerada
                url_thumb = response_thumb.data[0].url
                
                #UPLOAD PARA WODPRESS
                nome_thumb = gerar_nome_imagem()
                with open(nome_thumb, 'wb') as f:
                    response_imagem = requests.get(url_thumb)
                    f.write(response_imagem.content)
                dados_imagemthumb = {
                    'file': (nome_thumb, open(nome_thumb, 'rb'), 'image/jpeg'),
                }
                response_uploadthumb = requests.post(
                    url_base + 'media',
                    files=dados_imagemthumb,
                    auth=(usuario, senha)
                )
                #-------------------------------------------------------
                #                      SUBIR AS IMAGENS                -
                #-------------------------------------------------------
                # Verificar se o upload da imagem foi bem-sucedido
                if response_uploadthumb.status_code == 201:
                    # url_imagem_carregada = response_upload.json()['source_url']
                    url_thumb_carregada = response_uploadthumb.json()['source_url']

                    conteudo_artigo_com_imagem = f'{conteudo_artigo}'
                    # Atualizar o post no WordPress com o conteúdo atualizado
                    dados_post_atualizado = {
                        'content': conteudo_artigo_com_imagem,
                        'featured_media': response_uploadthumb.json()['id'],
                        'status': 'publish'
                    }

                    response_atualizacao = requests.put(
                        url_base + f'posts/{id_artigo}',
                        json=dados_post_atualizado,
                        auth=(usuario, senha)
                    )

                    if response_atualizacao.status_code == 200:
                        print('Imagem e conteúdo adicionados ao artigo com sucesso!')
                    else:
                        print('Erro ao adicionar a imagem e conteúdo ao artigo:', response_atualizacao.text)
                else:
                    print('Erro ao fazer upload da imagem:', response_uploadthumb.text)
          
        except RateLimitError:
             print("Você atingiu a cota de uso da API. Por favor, aguarde ou entre em contato com o suporte.")
#SALVA O EXEL COM O LINK DO POST
dados.to_excel('posts.xlsx', index=False)    
        
        
