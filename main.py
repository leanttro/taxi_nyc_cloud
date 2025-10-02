import os
import joblib
import requests # Usado para fazer o download
from flask import Flask, request, jsonify
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
modelos_carregados = False

# --- SEUS LINKS DE DOWNLOAD DIRETO DO GOOGLE DRIVE ---
URL_MODELO_TEMPO = 'https://drive.google.com/uc?export=download&id=1HsAuRtPU4r6MJowAg2IMu2ouwVKY8O-H'
URL_MODELO_VALOR = 'https://drive.google.com/uc?export=download&id=1ilxE_91OGTHIk0R6T3YGRFspH4g5B5xC'

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
        print(f"Download para {destination} concluído.")
    except Exception as e:
        print(f"ERRO ao baixar {url}. Detalhes: {e}")
        raise

def carregar_modelos():
    """
    Verifica se os modelos existem, faz o download se necessário, e os carrega na memória.
    """
    global modelo_tempo, modelo_valor, modelos_carregados
    
    # Baixa os modelos apenas se eles não existirem no ambiente
    if not os.path.exists(PATH_MODELO_TEMPO):
        download_file(URL_MODELO_TEMPO, PATH_MODELO_TEMPO)
        
    if not os.path.exists(PATH_MODELO_VALOR):
        download_file(URL_MODELO_VALOR, PATH_MODELO_VALOR)

    print("Carregando modelos .pkl na memória...")
    modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
    modelo_valor = joblib.load(PATH_MODELO_VALOR)
    
    modelos_carregados = True
    print("Modelos carregados com sucesso!")

# --- ENDPOINT PRINCIPAL DA API ---
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
    return "API de Previsão (Scikit-learn) com download de modelo está no ar!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))