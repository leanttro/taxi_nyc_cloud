import pandas as pd
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# O nome do seu arquivo Parquet foi simplificado para evitar erros de caminho no Render
caminho_parquet = 'dados.parquet' 

# Carregue o arquivo Parquet uma única vez quando a API iniciar
try:
    # O motor 'pyarrow' é o padrão e mais eficiente para arquivos Parquet grandes
    df_previsoes = pd.read_parquet(caminho_parquet, engine='pyarrow')
    print("DataFrame de previsões carregado com sucesso.")
except FileNotFoundError:
    print(f"Erro: O arquivo Parquet '{caminho_parquet}' não foi encontrado.")
    df_previsoes = None
except Exception as e:
    print(f"Erro ao carregar o Parquet: {e}")
    df_previsoes = None


def encontrar_previsao_mais_proxima(dados_entrada):
    if df_previsoes is None:
        # Retorna um erro se o DataFrame não foi carregado
        return None

    df = df_previsoes.copy()
    
    # 1. Calcular a diferença absoluta para cada coluna
    # Os nomes das colunas aqui (distancia_km, hora_dia, etc.) DEVEM ser os mesmos do arquivo Parquet.
    df['diff_distancia'] = np.abs(df['distancia_km'] - dados_entrada['trip_distance'])
    df['diff_hora'] = np.abs(df['hora_dia'] - dados_entrada['pickup_hour'])
    df['diff_dia'] = np.abs(df['dia_semana'] - dados_entrada['pickup_day_of_week'])
    df['diff_passageiros'] = np.abs(df['passageiros'] - dados_entrada['passenger_count'])
    
    # 2. Somar as diferenças para encontrar a linha mais próxima
    # Multiplicar a distância por 10 dá a ela mais peso no cálculo do "vizinho mais próximo"
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
        return jsonify({'error': 'Erro interno. Verifique se o arquivo de dados foi carregado corretamente.'}), 500

# Se você não estiver usando gunicorn, esta linha inicia o servidor Flask
# if __name__ == '__main__':
#     app.run(debug=True)
