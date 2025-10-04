import os
import psycopg2
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- INICIALIZAÇÃO DA APLICAÇÃO ---
app = Flask(__name__)
# Habilita o CORS para que seu front-end em outro domínio possa acessar a API
CORS(app) 

# Carrega o arquivo de previsões na memória quando a aplicação inicia
try:
    df = pd.read_parquet('dados.parquet')
except FileNotFoundError:
    print("ERRO CRÍTICO: O arquivo 'dados.parquet' não foi encontrado. A API não poderá fazer previsões.")
    df = pd.DataFrame()

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_db_connection():
    """Conecta ao banco de dados usando a variável de ambiente."""
    try:
        db_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(db_url)
        return conn
    except KeyError:
        print("ERRO CRÍTICO: A variável de ambiente DATABASE_URL não está definida!")
        raise
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise

def criar_tabela_se_nao_existir():
    """Cria a tabela 'simulacoes' com a estrutura correta se ela não existir."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
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
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Tabela 'simulacoes' verificada/criada com sucesso.")
    except Exception as e:
        print(f"ERRO ao criar a tabela: {e}")

# --- ROTAS DA API ---
@app.route('/')
def home():
    """Renderiza a página HTML principal."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint principal que faz a previsão e salva no banco de dados."""
    if df.empty:
        return jsonify({'error': 'Servidor não conseguiu carregar os dados de previsão.'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Requisição JSON inválida ou vazia.'}), 400

    try:
        # 1. Coleta os dados do front-end
        distancia = data['trip_distance']
        hora = data['pickup_hour']
        dia_semana = data['pickup_day_of_week']
        nome = data.get('nome')
        fonte = data['fonte']
    except KeyError as e:
        return jsonify({'error': f'Campo obrigatório ausente: {e}'}), 400

    # 2. Faz a previsão usando o arquivo Parquet
    resultado = df[
        (df['distancia_km'] == distancia) &
        (df['hora'] == hora) &
        (df['dia_semana'] == dia_semana)
    ]

    if not resultado.empty:
        valor_predito = resultado['valor_corrida'].iloc[0]
        tempo_predito = resultado['tempo_viagem_minutos'].iloc[0]

        # 3. Salva a simulação no banco de dados
        try:
            conn = get_db_connection()
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

        # 4. Retorna a resposta para o front-end
        return jsonify({
            'valor_corrida': f'{valor_predito:.2f}',
            'tempo_viagem_minutos': f'{tempo_predito:.1f}'
        })
    else:
        return jsonify({'error': 'Combinação de parâmetros não encontrada'}), 404

# --- EXECUÇÃO ---
# Cria a tabela quando o servidor inicia (seja localmente ou no Render)
criar_tabela_se_nao_existir()

if __name__ == "__main__":
    # Roda o servidor de desenvolvimento do Flask apenas se executado localmente
    app.run(debug=True)