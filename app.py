import pandas as pd
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# O nome do seu arquivo Parquet
caminho_parquet = 'previsoes_historico.parquet' 

# Carregue o arquivo Parquet uma única vez quando a API iniciar
try:
    df_previsoes = pd.read_parquet(caminho_parquet)
    print("DataFrame de previsões carregado com sucesso.")
except FileNotFoundError:
    print("Erro: O arquivo Parquet não foi encontrado.")
    df_previsoes = None

def encontrar_previsao_mais_proxima(dados_entrada):
    if df_previsoes is None:
        return None

    # Normalizar as distâncias para garantir que a hora não tenha um peso maior
    # Pode ser feito de forma mais complexa, mas essa é uma abordagem simples
    df = df_previsoes.copy()
    
    # Calcular a diferença absoluta para cada coluna
    df['diff_distancia'] = np.abs(df['distancia_km'] - dados_entrada['trip_distance'])
    df['diff_hora'] = np.abs(df['hora_dia'] - dados_entrada['pickup_hour'])
    df['diff_dia'] = np.abs(df['dia_semana'] - dados_entrada['pickup_day_of_week'])
    df['diff_passageiros'] = np.abs(df['passageiros'] - dados_entrada['passenger_count'])
    
    # Somar as diferenças para encontrar a linha mais próxima
    df['diferenca_total'] = (df['diff_distancia'] * 10) + df['diff_hora'] + df['diff_dia'] + df['diff_passageiros']

    # Encontrar a linha com a menor diferença
    previsao_mais_proxima = df.loc[df['diferenca_total'].idxmin()]
    
    return {
        'duracao_prevista_min': previsao_mais_proxima['duracao_prevista_min'],
        'valor_previsto_usd': previsao_mais_proxima['valor_previsto_usd']
    }

@app.route('/prever', methods=['POST'])
def prever():
    dados_entrada = request.get_json()
    previsao = encontrar_previsao_mais_proxima(dados_entrada)
    
    if previsao:
        return jsonify(previsao)
    else:
        return jsonify({'error': 'Não foi possível encontrar uma previsão'}), 500

if __name__ == '__main__':
    app.run(debug=True)