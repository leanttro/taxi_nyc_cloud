import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
import os 
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <<< ADICIONE ISSO AQUI



app = Flask(__name__)

# Nome do arquivo Parquet: deve ser o mesmo nome no GitHub!
caminho_parquet = 'dados.parquet' 

# Define o diretório base (robusto contra variações de ambiente do Render)
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Constrói o caminho completo do arquivo de forma robusta
CAMINHO_COMPLETO_PARQUET = os.path.join(BASEDIR, caminho_parquet)

# Carregue o arquivo Parquet uma única vez quando a API iniciar
try:
    # Tenta carregar o arquivo usando o caminho completo
    df_previsoes = pd.read_parquet(CAMINHO_COMPLETO_PARQUET, engine='pyarrow')
    print("DataFrame de previsões carregado com sucesso.")
    print(f"Caminho do arquivo carregado: {CAMINHO_COMPLETO_PARQUET}")
except FileNotFoundError:
    print(f"Erro: O arquivo Parquet '{CAMINHO_COMPLETO_PARQUET}' não foi encontrado.")
    df_previsoes = None
except Exception as e:
    print(f"Erro ao carregar o Parquet: {e}")
    df_previsoes = None


def encontrar_previsao_mais_proxima(dados_entrada):
    if df_previsoes is None:
        return None

    df = df_previsoes.copy()
    
    # 1. Calcular a diferença absoluta para cada coluna
    df['diff_distancia'] = np.abs(df['distancia_km'] - dados_entrada['trip_distance'])
    df['diff_hora'] = np.abs(df['hora_dia'] - dados_entrada['pickup_hour'])
    df['diff_dia'] = np.abs(df['dia_semana'] - dados_entrada['pickup_day_of_week'])
    df['diff_passageiros'] = np.abs(df['passageiros'] - dados_entrada['passenger_count'])
    
    # 2. Somar as diferenças para encontrar a linha mais próxima
    df['diferenca_total'] = (df['diff_distancia'] * 10) + df['diff_hora'] + df['diff_dia'] + df['diff_passageiros']

    # 3. Encontrar a linha com a menor diferença
    previsao_mais_proxima = df.loc[df['diferenca_total'].idxmin()]
    
    return {
        'duracao_prevista_min': previsao_mais_proxima['duracao_prevista_min'],
        'valor_previsto_usd': previsao_mais_proxima['valor_previsto_usd']
    }

@app.route('/prever', methods=['POST'])
def prever():
    try:
        dados_entrada = request.get_json()
    except:
        return jsonify({'error': 'Payload JSON inválido.'}), 400
        
    previsao = encontrar_previsao_mais_proxima(dados_entrada)
    
    if previsao:
        return jsonify(previsao)
    else:
        return jsonify({'error': 'Erro interno: Arquivo de dados não carregado. Verifique os logs do Render.'}), 500
