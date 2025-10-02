import os
import joblib
from flask import Flask, request, jsonify
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)

# Flag para controlar o carregamento do modelo
modelos_carregados = False

# --- LÓGICA DE CARREGAMENTO DOS MODELOS ---
def carregar_modelos():
    """
    Carrega os modelos scikit-learn (.pkl) na memória.
    """
    global modelo_tempo, modelo_valor, modelos_carregados
    print("Iniciando carregamento dos modelos .pkl...")
    
    modelo_tempo = joblib.load('modelo_tempo.pkl')
    modelo_valor = joblib.load('modelo_valor.pkl')
    
    modelos_carregados = True
    print("Modelos carregados com sucesso!")

# --- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST'])
def prever_corrida():
    """
    Recebe os dados da corrida em JSON e retorna a previsão usando scikit-learn.
    """
    # Garante que os modelos sejam carregados apenas na primeira requisição
    if not modelos_carregados:
        carregar_modelos()

    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo da requisição não é um JSON válido."}), 400

    try:
        # Prepara os dados de entrada em um DataFrame Pandas
        dados_df = pd.DataFrame([dados])
        features_tempo = dados_df[["pickup_hour", "pickup_day_of_week", "trip_distance", "passenger_count"]]
        
        # 1. Prever a DURAÇÃO
        duracao_prevista = modelo_tempo.predict(features_tempo)[0]
        
        # 2. Adicionar a duração prevista como feature para o próximo modelo
        features_valor = features_tempo.copy()
        features_valor['duracao_prevista'] = duracao_prevista

        # 3. Prever o VALOR
        valor_previsto = modelo_valor.predict(features_valor)[0]
        
        # Monta a resposta
        resultado = {
            "distancia_km": dados['trip_distance'],
            "hora_dia": dados['pickup_hour'],
            "dia_semana": dados['pickup_day_of_week'],
            "passageiros": dados['passenger_count'],
            "duracao_prevista_min": round(duracao_prevista, 2),
            "valor_previsto_usd": round(valor_previsto, 2)
        }
        
        return jsonify(resultado), 200

    except (ValueError, KeyError) as e:
        return jsonify({"erro": f"Dados de entrada inválidos ou faltando. Detalhe: {e}"}), 400

# --- ROTA DE TESTE ---
@app.route('/')
def index():
    return "API de Previsão (Scikit-learn) está no ar!", 200

# Esta parte é usada pelo Gunicorn no Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))