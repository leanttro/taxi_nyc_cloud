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
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        return conn
    except psycopg2.OperationalError as e:
        print(f"Erro de conexão com o banco de dados: {e}")
        return None

def criar_tabela_se_nao_existir():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        # ATUALIZAÇÃO: Adicionadas as colunas nome_usuario e fonte_conhecimento
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
    distancia = data['distancia']
    dia_semana = data['dia_semana']
    hora = data['hora']
    # ATUALIZAÇÃO: Captura dos novos campos. .get() é usado para o nome opcional.
    nome = data.get('nome') # Retorna None se não for enviado
    fonte = data['fonte']

    resultado = df[
        (df['distancia_km'] == distancia) &
        (df['dia_semana'] == dia_semana) &
        (df['hora'] == hora)
    ]

    if not resultado.empty:
        valor_predito = resultado['valor_corrida'].iloc[0]
        tempo_predito = resultado['tempo_viagem_minutos'].iloc[0]

        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                # ATUALIZAÇÃO: Novo comando INSERT com os campos adicionais
                sql = """
                    INSERT INTO simulacoes (distancia_km, dia_semana, hora, nome_usuario, fonte_conhecimento, tempo_predito, valor_predito) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                # ATUALIZAÇÃO: Novos valores passados para o comando SQL
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
        return jsonify({'error': 'Combinação de parâmetros não encontrada'}), 404

criar_tabela_se_nao_existir()

if __name__ == '__main__':
    app.run(debug=True)