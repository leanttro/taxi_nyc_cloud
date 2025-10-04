from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Tenta carregar o arquivo Parquet, com tratamento de erro
try:
    df = pd.read_parquet('dados.parquet')
except FileNotFoundError:
    print("ERRO: O arquivo 'dados.parquet' não foi encontrado. Certifique-se de que ele está na mesma pasta que o app.py.")
    df = pd.DataFrame() # Cria um dataframe vazio para evitar que o app quebre ao iniciar

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    # --- A ÚNICA LINHA ALTERADA ESTÁ AQUI ---
    conn = psycopg2.connect(os.environ['postgresql://taxi_simulacoes_db_user:n13itHNrUkSChN4uNKdgpPeYntUUfWZ2@dpg-d3gl1k63jp1c73esbuo0-a/taxi_simulacoes_db'])
    return conn

def criar_tabela_se_nao_existir():
    """Executa o comando SQL para criar nossa tabela de simulações se ela ainda não existir."""
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS simulacoes (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                distancia_km FLOAT,
                dia_semana INTEGER,
                hora INTEGER,
                nome_usuario TEXT, 
                fonte_conhecimento TEXT,
                tempo_predito FLOAT,
                valor_predito FLOAT
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Tabela 'simulacoes' verificada/criada com sucesso.")

@app.route('/')
def home():
    """Renderiza a página inicial (index.html)."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Recebe os dados do front-end, busca a previsão e salva o resultado no banco."""
    if df.empty:
        return jsonify({'error': 'Dados de previsão não carregados no servidor.'}), 500

    data = request.json

    try:
        distancia = data['trip_distance']
        hora = data['pickup_hour']
        dia_semana = data['pickup_day_of_week']
        nome = data.get('nome')
        fonte = data['fonte']
    except KeyError as e:
        return jsonify({'error': f'Campo obrigatório ausente no envio: {e}'}), 400
    
    # A busca no DataFrame usa os nomes das colunas do arquivo Parquet, o que já estava correto.
    resultado = df[
        (df['distancia_km'] == distancia) &
        (df['hora'] == hora) &
        (df['dia_semana'] == dia_semana)
    ]

    if not resultado.empty:
        valor_predito = resultado['valor_corrida'].iloc[0]
        tempo_predito = resultado['tempo_viagem_minutos'].iloc[0]

        # Tenta salvar a previsão no banco de dados
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                sql = """
                    INSERT INTO simulacoes (distancia_km, dia_semana, hora, nome_usuario, fonte_conhecimento, tempo_predito, valor_predito) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (distancia, dia_semana, hora, nome, fonte, tempo_predito, valor_predito)
                cur.execute(sql, params)
                conn.commit()
                cur.close()
                conn.close()
        except Exception as e:
            print(f"AVISO: Falha ao salvar no banco de dados: {e}")

        # Retorna o resultado para o front-end
        return jsonify({
            'valor_corrida': f'{valor_predito:.2f}',
            'tempo_viagem_minutos': f'{tempo_predito:.1f}'
        })
    else:
        return jsonify({'error': 'Combinação de parâmetros não encontrada nos dados pré-calculados'}), 404

# Executa a função para criar a tabela logo que a aplicação iniciar
criar_tabela_se_nao_existir()

if __name__ == '__main__':
    app.run(debug=True)