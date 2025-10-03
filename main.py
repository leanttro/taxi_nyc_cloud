import os
import joblib
import requests # Usado para fazer o download
from flask import Flask, request, jsonify
from flask_cors import CORS 
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app)  
modelos_carregados = False

# --- SEUS LINKS DE DOWNLOAD DIRETO DO GOOGLE DRIVE ---
# Links atualizados com os novos modelos compatíveis
URL_MODELO_TEMPO = 'https://drive.google.com/uc?export=download&id=1Anwt3rJqRPLEQ36bJG-0KuqXDUYNmF4r'
URL_MODELO_VALOR = 'https://drive.google.com/uc?export=download&id=1QURYrIup2PSI9UWRyRjpeYyCcWyWBYv9'

# Caminhos locais onde os arquivos serão salvos no Render
PATH_MODELO_TEMPO = 'modelo_tempo.pkl'
PATH_MODELO_VALOR = 'modelo_valor.pkl'


# --- LÓGICA DE DOWNLOAD E CARREGAMENTO ---
def download_file(url, destination):
    """Faz o download de um arquivo de uma URL."""
    print(f"Baixando modelo de {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(destination, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Modelo baixado com sucesso em {destination}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")
        # Se falhar, o Render já tentará novamente. Não é necessário relançar o erro aqui.
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

def carregar_modelos():
    """Carrega os modelos se eles existirem localmente, ou os baixa primeiro."""
    global modelo_tempo, modelo_valor, modelos_carregados
    if not os.path.exists(PATH_MODELO_TEMPO):
        download_file(URL_MODELO_TEMPO, PATH_MODELO_TEMPO)
    if not os.path.exists(PATH_MODELO_VALOR):
        download_file(URL_MODELO_VALOR, PATH_MODELO_VALOR)
    
    if os.path.exists(PATH_MODELO_TEMPO) and os.path.exists(PATH_MODELO_VALOR):
        print("Carregando modelos do disco...")
        try:
            modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
            modelo_valor = joblib.load(PATH_MODELO_VALOR)
            modelos_carregados = True
            print("Modelos carregados com sucesso!")
        except Exception as e:
            print(f"Erro ao carregar os modelos: {e}")
            modelos_carregados = False
    else:
        print("Atenção: Os arquivos de modelo não foram encontrados. A API não fará previsões.")
        modelos_carregados = False


# -- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST'])
def prever_corrida():
    if not modelos_carregados:
        carregar_modelos()

    dados = request.get_json()
    try:
        dados_df = pd.DataFrame([dados])
        features_tempo = dados_df[["pickup_hour", "pickup_day_of_week", "trip_distance", "passenger_count"]]
        duracao_prevista = modelo_tempo.predict(features_tempo)[0]
        features_valor = features_tempo.copy()
        features_valor['duracao_prevista'] = duracao_prevista
        valor_previsto = modelo_valor.predict(features_valor)[0]
        resultado = {
            "distancia_km": dados['trip_distance'], "hora_dia": dados['pickup_hour'],
            "dia_semana": dados['pickup_day_of_week'], "passageiros": dados['passenger_count'],
            "duracao_prevista_min": round(duracao_prevista, 2), "valor_previsto_usd": round(valor_previsto, 2)
        }
        return jsonify(resultado), 200
    except (ValueError, KeyError) as e:
        return jsonify({"erro": f"Dados de entrada inválidos ou faltando. Detalhe: {e}"}), 400

# --- ROTA DE TESTE ---
@app.route('/')
def index():
    return "API de Previsão de Corridas do NYC Taxi em funcionamento!"

# --- EXECUÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    # A primeira chamada para carregar os modelos.
    carregar_modelos()
    # A variável PORT é injetada pelo Render.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)