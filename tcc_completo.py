import geopandas as gpd
import pandas as pd
from pyproj import Proj, transform
import folium
import requests
import json

niteroi = gpd.read_file(r'Limite_de_Bairros\Limite_de_Bairros.shp')

# Pegando os centroides
centroide = niteroi.geometry.centroid
centroide

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

df_niteroi

######################################

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

df_niteroi

####################################

mapa = folium.Map(location = [-22.918769490782978, -43.056979733841224], zoom_start = 12, width = 600, height = 400, control_scale = True)

for bairro in lista_bairros:
    folium.Marker(location = [df_niteroi['Latitude'][bairro], df_niteroi['Longitude'][bairro]],
                  tooltip = bairro, 
                  icon = folium.Icon(color = 'black'),).add_to(mapa)

mapa

###########################

# Adicionando os lockers

dic_lck = {
    'LCK Locker Niterói': [0, 0, -22.895003479257202, -43.123676732116806],
    'LCK Locker Plaza Niterói': [0, 0, -22.89685736201976, -43.12368572236378],
    'LCK Locker Ibiza Central Shopping': [0, 0, -22.934797810452835, -43.022309860219984],
    'LCK Locker MultiCenter Itaipu': [0, 0, -22.950992190154313, -43.029263021257925],
    'LCK Locker Rede Economia Largo da Batalha': [0, 0, -22.90201224264317, -43.063982861147544]
}

df_lck = pd.DataFrame(dic_lck)

dic_cdds = {
    'CDD Niterói': [0, 0, -22.887424942376885, -43.12354567072342],
    'CDD Itaipu': [0, 0, -22.941380166125, -43.05286546954709],
    'CDD Icaraí': [0, 0, -22.895901773417418, -43.10074638349823],
    'CDD Largo da batalha': [0, 0, -22.90626685913838, -43.05616179121699]
}

df_cdds = pd.DataFrame(dic_cdds)

df_lck = df_lck.T.rename(columns={0:'Coordenada X', 1: 'Coordenada Y', 2:'Latitude', 3:'Longitude'})

df_cdds = df_cdds.T.rename(columns={0:'Coordenada X', 1: 'Coordenada Y', 2:'Latitude', 3:'Longitude'})

df_completo = pd.concat([df_niteroi, df_lck, df_cdds])

mapa = folium.Map(location = [-22.918769490782978, -43.056979733841224], zoom_start = 12, width = 600, height = 400, control_scale = True)

# Pegando a lista completa de bairros/lockers/cdds
lista_completa = df_completo.index.values.tolist()

for bairro in lista_completa:
    if bairro.split()[0] == 'LCK':
        folium.Marker(location = [df_completo['Latitude'][bairro], df_completo['Longitude'][bairro]],
                    tooltip = bairro, 
                    icon = folium.Icon(color = 'red'),).add_to(mapa)
    elif bairro.split()[0] == 'CDD':
        folium.Marker(location = [df_completo['Latitude'][bairro], df_completo['Longitude'][bairro]],
                    tooltip = bairro, 
                    icon = folium.Icon(color = 'green'),).add_to(mapa)
    else:
        folium.Marker(location = [df_completo['Latitude'][bairro], df_completo['Longitude'][bairro]],
                    tooltip = bairro, 
                    icon = folium.Icon(color = 'black'),).add_to(mapa)

mapa

#############################

# Criando a matriz
matriz_distancias = pd.DataFrame(index=lista_completa, columns=lista_completa)

# Loop para preencher
linhas = matriz_distancias.index.values.tolist()
colunas = matriz_distancias.columns.values.tolist()
for linha in linhas:
    for coluna in colunas:
        url = f'http://router.project-osrm.org/route/v1/driving/{df_completo['Longitude'][coluna]},{df_completo['Latitude'][coluna]};{df_completo['Longitude'][linha]},{df_completo['Latitude'][linha]}?overview=false'
        response = requests.get(url)
        resultado = json.loads(response._content.decode('utf-8'))
        distancia = resultado['routes'][0]['distance']
        # Atualiza a matriz de distancias
        matriz_distancias.at[linha, coluna] = distancia if linha != coluna else '-'


matriz_distancias.to_excel('matriz_distancias.xlsx')