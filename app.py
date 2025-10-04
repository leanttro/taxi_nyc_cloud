from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/predict": {"origins": "*"}})

# Carregar parquet
try:
    df = pd.read_parquet('dados.parquet')
except FileNotFoundError:
    print("ERRO: O arquivo 'dados.parquet' não foi encontrado.")
    df = pd.DataFrame()

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        db_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise

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

@app.route('/predict', methods=['POST', 'OPTIONS'])
@cross_origin()
def predict():
    if df.empty:
        return jsonify({'error': 'Servidor não conseguiu carregar os dados de previsão.'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Requisição JSON inválida ou vazia.'}), 400

    try:
        distancia = data['trip_distance']
        hora = data['hora']
        dia_semana = data['dia_semana']
        nome = data.get('nome')
        fonte = data['fonte']
    except KeyError as e:
        return jsonify({'error': f'Campo obrigatório ausente: {e}'}), 400

    resultado = df[
        (df['distancia_km'] == distancia) &
        (df['hora_dia'] == hora) & 
        (df['dia_semana'] == dia_semana)
    ]

    if not resultado.empty:
        # CORREÇÃO: Converter os tipos numpy para float padrão do Python
        valor_predito = float(resultado['valor_previsto_usd'].iloc[0])
        tempo_predito = float(resultado['duracao_prevista_min'].iloc[0])

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
            # Não quebra a aplicação se o DB falhar, apenas avisa no log
            print(f"AVISO: Falha ao salvar no banco de dados: {e}")

        return jsonify({
            'valor_corrida': f'{valor_predito:.2f}',
            'tempo_viagem_minutos': f'{tempo_predito:.1f}'
        })
    else:
        return jsonify({'error': 'Combinação de parâmetros não encontrada'}), 404

# Roda a criação da tabela na inicialização do app
try:
    criar_tabela_se_nao_existir()
except Exception as e:
    print(f"ERRO CRÍTICO ao inicializar o banco de dados: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
