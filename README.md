# Data Pipeline & Machine Learning com Táxis de NYC no Databricks

**Status:** Versão Completa

## Visão Geral do Projeto

Este projeto demonstra um ciclo de vida completo de dados, desde a engenharia até a ciência de dados. Utilizando a plataforma Databricks, os dados públicos de táxis de NYC são processados através de um pipeline robusto seguindo a **arquitetura Medallion**. Após o tratamento e a agregação dos dados, são realizadas análises de negócio para extrair insights e, por fim, um modelo de Machine Learning é treinado para prever resultados com base nos dados tratados.

## A Evolução do Projeto

Este repositório representa uma evolução significativa de uma simples ingestão de dados para uma solução de dados completa:

* **Versão 1 (EL no BigQuery):** O foco inicial era apenas na **Extração** e **Carga** (EL) dos dados brutos de uma fonte pública para o Google BigQuery usando um script Python com Pandas.
* **Versão Atual (ELT + ML no Databricks):** O projeto foi migrado para o **Databricks** e expandido para incluir:
    * **Processamento Distribuído com PySpark:** Permitindo escalar para grandes volumes de dados.
    * **Arquitetura Medallion Completa:** Implementação das camadas Bronze, Silver e Gold para garantir qualidade e governança.
    * **Análise de Dados Avançada:** Geração de insights de negócio com consultas SQL diretamente na plataforma.
    * **Modelagem Preditiva:** Desenvolvimento e avaliação de modelos de Machine Learning com Scikit-learn para prever a duração das viagens.

## Arquitetura Medallion no Databricks

O pipeline foi estruturado em três camadas lógicas para garantir um fluxo de dados limpo e organizado:

### Camada Bronze
* **Tabela:** `taxi_nyc_bronze`
* **Objetivo:** Ingestão dos dados brutos (raw data) para criar uma fonte única da verdade no nosso Data Lakehouse.

### Camada Silver
* **Tabela:** `taxi_nyc_silver`
* **Objetivo:** Limpeza, enriquecimento e normalização dos dados. Nesta etapa:
    * Os tipos de dados são corrigidos e padronizados.
    * Dados inconsistentes ou nulos são filtrados.
    * **Engenharia de Features:** Novas colunas são criadas (`pickup_day_of_week`, `pickup_hour`, `trip_duration_minutes`) para potencializar as análises e o modelo de ML.

### Camada Gold
* **Tabela:** `taxi_nyc_gold`
* **Objetivo:** Criação de tabelas agregadas com métricas de negócio, prontas para serem consumidas por dashboards ou pela equipe de ciência de dados.

## Análises e Insights Gerados

Através de consultas SQL na camada Gold, o projeto responde a perguntas de negócio como:

* Qual o volume de corridas e a demanda por hora do dia?
* Quais os dias da semana que geram maior faturamento?
* Como o comportamento da demanda se difere entre dias úteis e fins de semana?
* Quais são os piores horários para dirigir, com base na velocidade média das corridas?

## Machine Learning: Previsão da Duração da Viagem

Para agregar inteligência ao negócio, foi desenvolvido um modelo para prever a duração das viagens (`trip_duration_minutes`).

* **Features Utilizadas:** `pickup_hour`, `pickup_day_of_week`, `trip_distance`, `passenger_count`.
* **Modelos Avaliados:**
    1.  **Regressão Linear:** Apresentou performance insatisfatória (**R² de -0.38%**), servindo como baseline.
    2.  **Random Forest Regressor:** Demonstrou resultados excelentes, com um **R² de 66.39%**, explicando grande parte da variabilidade dos dados e alcançando um erro médio (RMSE) de apenas **9.09 minutos**.

## Como Executar

1.  **Ambiente:** Este projeto foi desenvolvido para ser executado em um ambiente Databricks.
2.  **Importar Notebook:** Faça o upload do notebook `Taxi_nyc_notebook.ipynb` para o seu workspace no Databricks.
3.  **Cluster:** Anexe o notebook a um cluster Spark em execução.
4.  **Execução:** Execute as células sequencialmente para criar as camadas Bronze, Silver, Gold, realizar as análises e treinar os modelos de Machine Learning.

## Próximos Passos

* **Automação com Databricks Jobs:** Orquestrar o notebook para rodar de forma agendada (diária, mensal) e automática.
* **MLOps com MLflow:** Utilizar o MLflow (integrado ao Databricks) para registrar experimentos, versionar o modelo Random Forest e prepará-lo para o deploy.
* **Visualização:** Conectar o Databricks a uma ferramenta de BI (Power BI, Looker Studio) para criar dashboards interativos a partir da camada Gold.

## Autor

**Leandro Andrade de Oliveira**
* **LinkedIn:** `https://www.linkedin.com/in/leanttro/`
