from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

try:
    df = pd.read_parquet('dados.parquet')
except FileNotFoundError:
    print("ERRO: O arquivo 'dados.parquet' não foi encontrado.")
    df = pd.DataFrame()

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    # Acessa a variável de ambiente 'DATABASE_URL'
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

def criar_tabela_se_nao_existir():
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
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
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
    
    resultado = df[
        (df['distancia_km'] == distancia) &
        (df['hora'] == hora) &
        (df['dia_semana'] == dia_semana)
    ]

    if not resultado.empty:
        valor_predito = resultado['valor_corrida'].iloc[0]
        tempo_predito = resultado['tempo_viagem_minutos'].iloc[0]
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
        return jsonify({
            'valor_corrida': f'{valor_predito:.2f}',
            'tempo_viagem_minutos': f'{tempo_predito:.1f}'
        })
    else:
        return jsonify({'error': 'Combinação de parâmetros não encontrada nos dados pré-calculados'}), 404

criar_tabela_se_nao_existir()

if __name__ == '__main__':
    app.run(debug=True)