import os
import psycopg2
from psycopg2 import sql
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # libera CORS para seu front-end

# ----------------------------
# Conexão com o banco de dados
# ----------------------------
def get_db_connection():
    try:
        db_url = os.environ['DATABASE_URL']  # Nome da variável de ambiente no Render
        conn = psycopg2.connect(db_url)
        return conn
    except KeyError:
        raise Exception("A variável de ambiente DATABASE_URL não está definida!")
    except Exception as e:
        raise Exception(f"Erro ao conectar ao banco de dados: {e}")

# ----------------------------
# Criação da tabela se não existir
# ----------------------------
def criar_tabela_se_nao_existir():
    conn = get_db_connection()
    cur = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS simulacoes (
        id SERIAL PRIMARY KEY,
        origem TEXT NOT NULL,
        destino TEXT NOT NULL,
        preco NUMERIC,
        data_simulacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()

# ----------------------------
# Endpoint de teste
# ----------------------------
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    origem = data.get('origem')
    destino = data.get('destino')
    preco = 42.0  # apenas um exemplo fixo
    # salva no banco
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO simulacoes (origem, destino, preco) VALUES (%s, %s, %s);",
            (origem, destino, preco)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'origem': origem,
        'destino': destino,
        'preco': preco
    })

# ----------------------------
# Inicialização da aplicação
# ----------------------------
if __name__ == "__main__":
    criar_tabela_se_nao_existir()
    app.run(host='0.0.0.0', port=10000)
