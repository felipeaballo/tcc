import geopandas as gpd
import pandas as pd
from pyproj import Proj, transform
import folium
import requests
import json

niteroi = gpd.read_file(r'Limite_de_Bairros\Limite_de_Bairros.shp')

# Pegando os centroides
centroide = niteroi.geometry.centroid

# Dando uma olhada nos bairros
niteroi['tx_nome']

# Criando um DF com os dados: nomes do bairros, coordenada X do centroide e coordenada Y do centroide
df_niteroi = pd.DataFrame(data=[niteroi['tx_nome'], centroide.x, centroide.y])

# Transpondo o DF para ser melhor visualizado
df_niteroi = df_niteroi.T

# Alterando o nome das colunas para o DF ficar melhor
df_niteroi.rename(columns={'tx_nome': 'Bairro', 'Unnamed 0': 'Coordenada X', 'Unnamed 1': 'Coordenada Y'}, inplace=True)

# Setando o index como a coluna do nome do bairro para ficar melhor de utilizar
df_niteroi = df_niteroi.set_index('Bairro')


##########################

# Agora, vamos precisar trazer as medidas dos centroides que estão em metros para coordenadas para usar no mapa (latitude e longitude)
'''
from pyproj import Proj, transform

# Coordenadas do centróide em metros (exemplo para Varzea das Moças)
centroide_x = df_niteroi['Coordenada X']['Varzea das Moças']
centroide_y = df_niteroi['Coordenada Y']['Varzea das Moças']

# Definir o sistema de coordenadas de origem (UTM) e destino (latitude e longitude)
in_proj = Proj(proj='utm', zone=23, south=True, ellps='WGS84')  # Zona UTM 23S para Niterói
out_proj = Proj(proj='latlong', ellps='WGS84')

# Converter coordenadas do centróide de UTM para latitude e longitude
longitude, latitude = transform(in_proj, out_proj, centroide_x, centroide_y)

# Imprimir as coordenadas em latitude e longitude
print("Latitude:", latitude)
print("Longitude:", longitude)
'''
# Agora, fazendo isso para todos os bairros e adicionando no DF

# Pegando a lista de bairros
lista_bairros = df_niteroi.index.values.tolist()

# Definir o sistema de coordenadas de origem (UTM) e destino (latitude e longitude)
in_proj = Proj(proj='utm', zone=23, south=True, ellps='WGS84')  # Zona UTM 23S para Niterói
out_proj = Proj(proj='latlong', ellps='WGS84')

# Lista com as latitudes
lista_latitudes = []
# Lista com as longitudes
lista_longitudes = []

# loop para todos bairros
for bairro in lista_bairros:
    centroide_x = df_niteroi['Coordenada X'][bairro]
    centroide_y = df_niteroi['Coordenada Y'][bairro]
    longitude, latitude = transform(in_proj, out_proj, centroide_x, centroide_y)
    lista_latitudes.append(latitude)
    lista_longitudes.append(longitude)

# Adicionando as listas no DF
df_niteroi['Latitude'] = lista_latitudes
df_niteroi['Longitude'] = lista_longitudes


######################################

# Agora, vamos plotar no folium

mapa = folium.Map(location = [-22.918769490782978, -43.056979733841224], zoom_start = 12, width = 600, height = 400, control_scale = True)

for bairro in lista_bairros:
    folium.Marker(location = [df_niteroi['Latitude'][bairro], df_niteroi['Longitude'][bairro]],
                  tooltip = bairro, 
                  icon = folium.Icon(color = 'black'),).add_to(mapa)

mapa

###############################

# Agora, precisamos encontrar a distancia entre cada bairro, com isso, montaremos uma matriz de distancias

# Criando a matriz
matriz_distancias = pd.DataFrame(index=lista_bairros, columns=lista_bairros)

# Exemplo abaixo de como pegar a distancia entre o Centro e Itaipu

'''
import requests
import json

url = f'http://router.project-osrm.org/route/v1/driving/{df_niteroi['Longitude']['Centro']},{df_niteroi['Latitude']['Centro']};{df_niteroi['Longitude']['Itaipu']},{df_niteroi['Latitude']['Itaipu']}?overview=false'

response = requests.get(url)

resultado = json.loads(response._content.decode('utf-8'))

resultado['routes'][0]['distance']
'''

# Loop para preencher
linhas = matriz_distancias.index.values.tolist()
colunas = matriz_distancias.columns.values.tolist()
for linha in linhas:
    for coluna in colunas:
        url = f'http://router.project-osrm.org/route/v1/driving/{df_niteroi['Longitude'][coluna]},{df_niteroi['Latitude'][coluna]};{df_niteroi['Longitude'][linha]},{df_niteroi['Latitude'][linha]}?overview=false'
        response = requests.get(url)
        resultado = json.loads(response._content.decode('utf-8'))
        distancia = resultado['routes'][0]['distance']
        # Atualiza a matriz de distancias
        matriz_distancias.at[linha, coluna] = distancia if linha != coluna else '-'

######################

# Escrevendo o resultado numa planilha

matriz_distancias.to_excel('matriz_distancias.xlsx')

### Agora, só preciso adicionar os lockers e colocar ele nessa brincadeira da matriz de distancias