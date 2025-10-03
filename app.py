import os
import joblib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app, resources={r"/prever": {"origins": "*"}})
modelos_carregados = False

# Global variables for models (will be set inside carregar_modelos)
modelo_tempo = None
modelo_valor = None

# --- CAMINHOS LOCAIS PARA OS MODELOS ---
PATH_MODELO_TEMPO = 'models/modelo_tempo.pkl'
PATH_MODELO_VALOR = 'models/modelo_valor.pkl'

# --- LÓGICA DE CARREGAMENTO ---
def carregar_modelos():
    """Carrega os modelos PKL na memória do servidor."""
    global modelo_tempo, modelo_valor, modelos_carregados
    print("Carregando modelos .pkl locais da pasta 'models'...")
    try:
        # Tenta carregar os modelos. Se as versões (como scikit-learn 1.7.2) forem incompatíveis,
        # este é o ponto onde a exceção Value Error (dtype size changed) ocorre.
        modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
        modelo_valor = joblib.load(PATH_MODELO_VALOR)
        modelos_carregados = True
        print("Modelos carregados com sucesso!")
    except Exception as e:
        print(f"ERRO CRÍTICO ao carregar os modelos locais. Detalhes: {e}")
        # A mensagem de erro da API 503 vem daqui:
        modelos_carregados = False

# === CORREÇÃO CRÍTICA PARA RENDER (GUNICORN) ===
# O Gunicorn ignora o bloco 'if __name__ == "__main__":',
# então a função de carregamento deve ser chamada no escopo global.
carregar_modelos() 

# --- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST', 'OPTIONS'])
def prever_corrida():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Se a flag for False, a função retorna o erro 503 (Modelo não carregado)
    if not modelos_carregados:
        return jsonify({"erro": "Modelos não estão carregados no servidor. Falha no joblib.load(). Verifique os logs."}), 503

    dados = request.get_json()
    required_keys = ["trip_distance", "pickup_hour", "pickup_day_of_week", "passenger_count"]
    if not all(key in dados for key in required_keys):
        return jsonify({"erro": "Dados de entrada faltando."}), 400

    try:
        dados_df = pd.DataFrame([dados])
        features_tempo = dados_df[["pickup_hour", "pickup_day_of_week", "trip_distance", "passenger_count"]]
        
        # Previsão de Tempo
        duracao_prevista = modelo_tempo.predict(features_tempo)[0]

        # Previsão de Valor (usando a duração como feature)
        features_valor = features_tempo.copy()
        features_valor['duracao_prevista'] = duracao_prevista
        valor_previsto = modelo_valor.predict(features_valor)[0]

        resultado = {
            "duracao_prevista_min": float(round(duracao_prevista, 2)),
            "valor_previsto_usd": float(round(valor_previsto, 2))
        }
        return jsonify(resultado), 200
    except Exception as e:
        print(f"ERRO INTERNO AO PREVER: {e}")
        return jsonify({"erro": "Ocorreu um erro no servidor ao processar a previsão."}), 500

# --- ROTA PARA SERVIR O HTML ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Removida a chamada carregar_modelos() daqui, pois ela é executada no escopo global.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)