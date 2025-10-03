import os
import joblib
import requests # Usado para fazer o download
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app, resources={r"/prever": {"origins": "*"}})
modelos_carregados = False

# --- LÓGICA DE DOWNLOAD E CARREGAMENTO ---
def download_file(url, destination):
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
    global modelo_tempo, modelo_valor, modelos_carregados
    
    # --- IMPORTANTE: PEGUE OS LINKS DAS VARIÁVEIS DE AMBIENTE ---
    URL_MODELO_TEMPO = os.environ.get('URL_MODELO_TEMPO')
    URL_MODELO_VALOR = os.environ.get('URL_MODELO_VALOR')

    if not URL_MODELO_TEMPO or not URL_MODELO_VALOR:
        print("ERRO CRÍTICO: As variáveis de ambiente URL_MODELO_TEMPO e URL_MODELO_VALOR não foram configuradas no Render.")
        modelos_carregados = False
        return

    PATH_MODELO_TEMPO = 'modelo_tempo.pkl'
    PATH_MODELO_VALOR = 'modelo_valor.pkl'

    # Baixa os modelos sempre que a aplicação iniciar para garantir a versão mais recente
    download_file(URL_MODELO_TEMPO, PATH_MODELO_TEMPO)
    download_file(URL_MODELO_VALOR, PATH_MODELO_VALOR)

    print("Carregando modelos .pkl na memória...")
    try:
        modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
        modelo_valor = joblib.load(PATH_MODELO_VALOR)
        modelos_carregados = True
        print("Modelos carregados com sucesso!")
    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar os modelos .pkl. Detalhes: {e}")
        modelos_carregados = False

# --- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST', 'OPTIONS'])
def prever_corrida():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not modelos_carregados:
        return jsonify({"erro": "Modelos não estão carregados no servidor. Verifique os logs do Render."}), 503

    dados = request.get_json()
    # ... (o resto do código continua igual)
    try:
        dados_df = pd.DataFrame([dados])
        features_tempo = dados_df[["pickup_hour", "pickup_day_of_week", "trip_distance", "passenger_count"]]
        duracao_prevista = modelo_tempo.predict(features_tempo)[0]

        features_valor = features_tempo.copy()
        features_valor['duracao_prevista'] = duracao_prevista
        valor_previsto = modelo_valor.predict(features_valor)[0]

        resultado = {
            "duracao_prevista_min": round(duracao_prevista, 2),
            "valor_previsto_usd": round(valor_previsto, 2)
        }
        return jsonify(resultado), 200
    except Exception as e:
        print(f"ERRO INTERNO AO PREVER: {e}")
        return jsonify({"erro": "Ocorreu um erro no servidor ao processar a previsão."}), 500

# --- ROTA DE TESTE ---
@app.route('/')
def index():
    return "API de Previsão de Corridas do NYC Taxi em funcionamento!"

if __name__ == '__main__':
    carregar_modelos()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)