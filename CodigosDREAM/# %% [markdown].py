# %% [markdown]
# # Progress of the SYNAPSE project   
# 
# ### Participants:
# - Martin Rule
# - Emiliano Jimémez  
# 

# %% [markdown]
# ##### PCA bacteries and NIH Racial Category
# 
# First we started analyzing the metadata and taxonomy_relabd, we tried to find a patron to start with the machine learning project

# %%
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# datos 
metadata = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\metadata\metadata.csv")
rel_abun = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\taxonomy\taxonomy_relabd.species.csv")

# Unir los datasets y seleccionar solo las columnas necesarias
rel_abun_etn = pd.merge(metadata[['specimen', 'NIH Racial Category']], rel_abun, on='specimen')

# Preparar los datos para PCA
data_pca = rel_abun_etn.drop(columns=['specimen', 'NIH Racial Category'])

# Realizar PCA
pca = PCA(n_components=2)
pca_result = pca.fit_transform(data_pca)

# Convertir los resultados a un DataFrame
pca_df = pd.DataFrame(data=pca_result, columns=['PC1', 'PC2'])
pca_df['NIH Racial Category'] = rel_abun_etn['NIH Racial Category']

# Graficar los resultados del PCA
plt.figure(figsize=(10, 6))
scatter = plt.scatter(pca_df['PC1'], pca_df['PC2'], c=pca_df['NIH Racial Category'].astype('category').cat.codes)
plt.title('PCA of Taxonomic Relative Abundance')
plt.xlabel('PC1')
plt.ylabel('PC2')
plt.legend(*scatter.legend_elements(), title="NIH Racial Category")
plt.show()

# %%
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Cargar los datos
metadata = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\metadata\metadata.csv")
rel_abun = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\taxonomy\taxonomy_relabd.species.csv")

# Unir los datasets y seleccionar solo las columnas necesarias
rel_abun_etn = pd.merge(metadata[['specimen', 'NIH Racial Category']], rel_abun, on='specimen')

# Preparar los datos para PCA
data_pca = rel_abun_etn.drop(columns=['specimen', 'NIH Racial Category'])

# Realizar PCA
pca = PCA(n_components=2)
pca_result = pca.fit_transform(data_pca)

# Convertir los resultados a un DataFrame
pca_df = pd.DataFrame(data=pca_result, columns=['PC1', 'PC2'])
pca_df['NIH Racial Category'] = rel_abun_etn['NIH Racial Category']

# Mapeo de los códigos a los nombres de las razas
race_categories = pca_df['NIH Racial Category'].astype('category').cat.categories.tolist()
race_colors = pca_df['NIH Racial Category'].astype('category').cat.codes

# Graficar los resultados del PCA
plt.figure(figsize=(10, 6))
scatter = plt.scatter(pca_df['PC1'], pca_df['PC2'], c=race_colors, cmap='viridis')

# Añadir leyenda con los nombres de las razas
plt.legend(handles=scatter.legend_elements()[0], labels=race_categories, title="NIH Racial Category")
plt.title('PCA of Taxonomic Relative Abundance')
plt.xlabel('Dominant Species Variation ')
plt.ylabel('Subdominant Species Variation ')
plt.show()

# %%
import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Cargar los datos
metadata = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\metadata\metadata.csv")
rel_abun = pd.read_csv(r"C:\SS\datosSynapse\Training\Training\taxonomy\taxonomy_relabd.species.csv")

# Unir los datasets y seleccionar solo las columnas necesarias
rel_abun_etn = pd.merge(metadata[['specimen', 'NIH Racial Category']], rel_abun, on='specimen')

# Preparar los datos para PCA
data_pca = rel_abun_etn.drop(columns=['specimen', 'NIH Racial Category'])

# Realizar PCA
pca = PCA(n_components=2)
pca_result = pca.fit_transform(data_pca)

# Convertir los resultados a un DataFrame
pca_df = pd.DataFrame(data=pca_result, columns=['PC1', 'PC2'])
pca_df['NIH Racial Category'] = rel_abun_etn['NIH Racial Category']

# Obtener los límites globales de los ejes para PC1 y PC2
x_min, x_max = pca_df['PC1'].min() - 1, pca_df['PC1'].max() + 1
y_min, y_max = pca_df['PC2'].min() - 1, pca_df['PC2'].max() + 1

# Obtener las categorías únicas
race_categories = pca_df['NIH Racial Category'].unique()

# Crear gráficos individuales para cada raza con los mismos ejes
for race in race_categories:
    race_df = pca_df[pca_df['NIH Racial Category'] == race]

    plt.figure(figsize=(10, 6))
    plt.scatter(race_df['PC1'], race_df['PC2'], label=race)
    plt.title(f'PCA of Taxonomic Relative Abundance for {race}')
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.xlim(x_min, x_max)  # Establecer los límites de PC1
    plt.ylim(y_min, y_max)  # Establecer los límites de PC2
    plt.legend(title="NIH Racial Category")
    plt.show()

# %% [markdown]
# ##### NIH Racial Category Bacteria table
# 
# Martin saw and explained that the PCA did not give us information that served us, but we proceeded to make a heatmap, without first see made a table with the most common bacteria of NIH Racial Category

# %% [markdown]
# <img src="TOP10bacim.png">

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar el archivo TOP10bacteriesmostcommun.csv
top10_bacteria_file_path = r'C:\Users\Emiliano\Desktop\SS python VSC\TOP10bacteriesmostcommun.csv'

# Leer el archivo CSV en un DataFrame
top10_bacteria_df = pd.read_csv(top10_bacteria_file_path)

# Eliminar el símbolo de porcentaje y forzar la conversión a tipo numérico
for column in top10_bacteria_df.columns[1:]:
    top10_bacteria_df[column] = pd.to_numeric(top10_bacteria_df[column].replace('%', '', regex=True), errors='coerce')

# Colocar los nombres de las bacterias como índice para que aparezcan en el gráfico
top10_bacteria_df.set_index('Unnamed: 0', inplace=True)

# Crear el mapa de calor con los nombres de las bacterias
plt.figure(figsize=(10, 8))
sns.heatmap(top10_bacteria_df, annot=True, cmap="YlGnBu", cbar_kws={'label': 'Porcentaje (%)'})

# Etiquetas y título
plt.title("Mapa de Calor: TOP 10 Bacterias más Comunes por Categoría Racial")
plt.ylabel("Bacterias")
plt.xlabel("Categorías Raciales")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

# Mostrar el gráfico
plt.show()

# %% [markdown]
# So we did it with 5 bacteria

# %% [markdown]
# <img src="TOP5bacim.png">

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar el archivo TOP5bacteriesmostcommun.csv
top10_bacteria_file_path = r'C:\Users\Emiliano\Desktop\SS python VSC\TOP5bacteriesraces.csv'

# Leer el archivo CSV en un DataFrame
top10_bacteria_df = pd.read_csv(top10_bacteria_file_path)

# Eliminar el símbolo de porcentaje y forzar la conversión a tipo numérico
for column in top10_bacteria_df.columns[1:]:
    top10_bacteria_df[column] = pd.to_numeric(top10_bacteria_df[column].replace('%', '', regex=True), errors='coerce')

# Colocar los nombres de las bacterias como índice para que aparezcan en el gráfico
top10_bacteria_df.set_index('Unnamed: 0', inplace=True)

# Crear el mapa de calor con los nombres de las bacterias
plt.figure(figsize=(10, 8))
sns.heatmap(top10_bacteria_df, annot=True, cmap="YlGnBu", cbar_kws={'label': 'Porcentaje (%)'})

# Etiquetas y título
plt.title("Mapa de Calor: TOP 10 Bacterias más Comunes por Categoría Racial")
plt.ylabel("Bacterias")
plt.xlabel("Categorías Raciales")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

# Mostrar el gráfico
plt.show()


