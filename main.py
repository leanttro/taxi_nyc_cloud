import os
import joblib
import requests # Usado para fazer o download
from flask import Flask, request, jsonify
from flask_cors import CORS 
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
# Configura o CORS para permitir requisições de qualquer origem
CORS(app)  
modelos_carregados = False

# --- SEUS LINKS DE DOWNLOAD DIRETO DO GOOGLE DRIVE ---
# O código agora vai PRIORIZAR as variáveis de ambiente do Render.
# Se não encontrar, ele usará os links abaixo como um fallback.
URL_MODELO_TEMPO = os.environ.get('URL_MODELO_TEMPO', 'https://drive.google.com/uc?export=download&id=1Anwt3rJqRPLEQ36bJG-0KuqXDUYNmF4r')
URL_MODELO_VALOR = os.environ.get('URL_MODELO_VALOR', 'https://drive.google.com/uc?export=download&id=1QURYrIup2PSI9UWRyRjpeYyCcWyWBYv9')

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
    try:
        global modelo_tempo, modelo_valor
        modelo_tempo = joblib.load(PATH_MODELO_TEMPO)
        modelo_valor = joblib.load(PATH_MODELO_VALOR)
        modelos_carregados = True
        print("Modelos carregados com sucesso!")
    except Exception as e:
        print(f"ERRO ao carregar os modelos .pkl. Detalhes: {e}")
        raise

# --- ENDPOINT PRINCIPAL DA API ---
@app.route('/prever', methods=['POST', 'OPTIONS'])
def prever_corrida():
    if not modelos_carregados:
        # Se os modelos não estiverem na memória, retorna um erro ou tenta carregar.
        # Para evitar lentidão na primeira requisição, o ideal é que eles já estejam carregados.
        return jsonify({"erro": "Modelos não estão carregados no servidor."}), 503

    dados = request.get_json()
    
    # Validação simples dos dados de entrada
    required_keys = ["trip_distance", "pickup_hour", "pickup_day_of_week", "passenger_count"]
    if not all(key in dados for key in required_keys):
        return jsonify({"erro": "Dados de entrada faltando. Verifique os campos."}), 400

    try:
        dados_df = pd.DataFrame([dados])
        
        # Previsão do tempo
        features_tempo = dados_df[["pickup_hour", "pickup_day_of_week", "trip_distance", "passenger_count"]]
        duracao_prevista = modelo_tempo.predict(features_tempo)[0]
        
        # Previsão do valor
        features_valor = features_tempo.copy()
        features_valor['duracao_prevista'] = duracao_prevista
        valor_previsto = modelo_valor.predict(features_valor)[0]
        
        resultado = {
            "distancia_km": dados['trip_distance'],
            "hora_dia": dados['pickup_hour'],
            "dia_semana": dados['pickup_day_of_week'],
            "passageiros": dados['passenger_count'],
            "duracao_prevista_min": round(duracao_prevista, 2),
            "valor_previsto_usd": round(valor_previsto, 2)
        }
        return jsonify(resultado), 200
        
    except Exception as e:
        # Retorna um erro genérico para o cliente, mas loga o detalhe no servidor
        print(f"ERRO INTERNO AO PREVER: {e}")
        return jsonify({"erro": f"Ocorreu um erro no servidor ao processar a previsão."}), 500

# --- ROTA DE TESTE ---
@app.route('/')
def index():
    return "API de Previsão de Corridas do NYC Taxi em funcionamento!"

if __name__ == '__main__':
    # Garante que os modelos sejam baixados e carregados na memória 
    # quando a aplicação for iniciada pelo Gunicorn no Render.
    carregar_modelos() 
    
    # A variável PORT é injetada pelo Render. O padrão 5000 é para teste local.
    port = int(os.environ.get("PORT", 5000))
    # 'debug=False' é importante para produção. 'host=0.0.0.0' permite conexões externas.
    app.run(host='0.0.0.0', port=port, debug=False)