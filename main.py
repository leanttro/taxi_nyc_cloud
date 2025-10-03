import os
import joblib
# A biblioteca 'requests' foi removida pois não fazemos mais download
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app, resources={r"/prever": {"origins": "*"}})
modelos_carregados = False

# --- CAMINHOS LOCAIS PARA OS MODELOS ---
# Apontando para a pasta 'models' que está no projeto
PATH_MODELO_TEMPO = 'models/modelo_tempo.pkl'
PATH_MODELO_VALOR = 'models/modelo_valor.pkl'

# --- LÓGICA DE CARREGAMENTO (SEM DOWNLOAD) ---
def carregar_modelos():
    global modelo_tempo, modelo_valor, modelos_carregados
    print("Carregando modelos .pkl locais da pasta 'models'...")
    try:
        modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
        modelo_valor = joblib.load(PATH_MODELO_VALOR)
        modelos_carregados = True
        print("Modelos carregados com sucesso!")
    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar os modelos locais. Verifique se os arquivos .pkl estão na pasta 'models'. Detalhes: {e}")
        modelos_carregados = False

# --- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST', 'OPTIONS'])
def prever_corrida():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not modelos_carregados:
        return jsonify({"erro": "Modelos não estão carregados no servidor. Falha no joblib.load(). Verifique os logs."}), 503

    dados = request.get_json()
    required_keys = ["trip_distance", "pickup_hour", "pickup_day_of_week", "passenger_count"]
    if not all(key in dados for key in required_keys):
        return jsonify({"erro": "Dados de entrada faltando."}), 400

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