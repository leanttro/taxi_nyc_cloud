import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Ativa CORS na instância correta

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
    # Ajuste: Aumenta o peso da Hora do Dia (diff_hora * 3) para melhorar a precisão em horários de pico.
    df['diferenca_total'] = (df['diff_distancia'] * 10) + (df['diff_hora'] * 3) + df['diff_dia'] + df['diff_passageiros']

    # 3. Encontrar a linha com a menor diferença
    previsao_mais_proxima = df.loc[df['diferenca_total'].idxmin()]
    
    return {
        'duracao_prevista_min': previsao_mais_proxima['duracao_prevista_min'],
        'valor_previsto_usd': previsao_mais_proxima['valor_previsto_usd']
    }

@app.route('/prever', methods=['POST']) # <--- ROTA CORRIGIDA DE VOLTA PARA '/prever'
def predict():
    if df_previsoes is None:
        return jsonify({'error': 'Modelo de previsões não carregado. Verifique o arquivo dados.parquet.'}), 500

    try:
        dados_entrada = request.get_json()

        # Validação básica dos dados de entrada
        required_keys = ['trip_distance', 'pickup_hour', 'pickup_day_of_week', 'passenger_count']
        if not all(key in dados_entrada for key in required_keys):
            return jsonify({'error': 'Dados de entrada incompletos ou inválidos.'}), 400

        # Converte a entrada para float/int para a função de pesquisa
        dados_entrada = {
            'trip_distance': float(dados_entrada.get('trip_distance')),
            'pickup_hour': int(dados_entrada.get('pickup_hour')),
            'pickup_day_of_week': int(dados_entrada.get('pickup_day_of_week')),
            'passenger_count': int(dados_entrada.get('passenger_count', 1)) # Default para 1 passageiro
        }

        # Encontra a previsão mais próxima (KNN manual)
        resultado = encontrar_previsao_mais_proxima(dados_entrada)

        if resultado:
            return jsonify(resultado), 200
        else:
            return jsonify({'error': 'Não foi possível encontrar uma previsão próxima.'}), 404

    except ValueError:
        return jsonify({'error': 'Um ou mais valores de entrada não são numéricos válidos.'}), 400
    except Exception as e:
        print(f"Erro inesperado durante a previsão: {e}")
        return jsonify({'error': 'Erro interno do servidor ao processar a previsão.'}), 500

if __name__ == '__main__':
    # O Gunicorn (servidor de produção) não usará esta linha, mas é útil para testes locais
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)
