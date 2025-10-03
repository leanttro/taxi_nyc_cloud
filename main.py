import os
import joblib
import requests # Usado para fazer o download
from flask import Flask, request, jsonify
from flask_cors import CORS 
import pandas as pd

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
CORS(app)  
modelos_carregados = False

# --- SEUS LINKS DE DOWNLOAD DIRETO DO GOOGLE DRIVE ---
# O código agora vai PRIORIZAR as variáveis de ambiente do Render.
# Se não encontrar, ele usará os links abaixo como um fallback.
URL_MODELO_TEMPO = os.environ.get('URL_MODELO_TEMPO', 'https://drive.google.com/uc?export=download&id=1Anwt3rJqRPLEQ36bJG-0KuqXDUYNmF4r')
URL_MODELO_VALOR = os.environ.get('URL_MODELO_VALOR', 'https://drive.google.com/uc?export=download&id=1QURYrIup2PSI9UWRyRjpeYyCcWyWBYv9')

# Caminhos locais onde os arquivos serão salvos no Render
PATH_MODELO_TEMPO = 'modelo_tempo.pkl'
PATH_MODELO_VALOR = 'modelo_valor.pkl'

# --- O RESTO DO SEU CÓDIGO CONTINUA DAQUI PARA BAIXO ---