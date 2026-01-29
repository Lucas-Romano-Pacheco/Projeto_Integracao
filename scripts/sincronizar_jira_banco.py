import requests
import sqlite3
import os
import schedule
import time
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Usamos caminhos absolutos para evitar erros de localização da pasta 'data'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DATA = os.path.join(BASE_DIR, 'data')
CAMINHO_DB = os.path.join(PASTA_DATA, 'integracao_jira.db')

# --- CREDENCIAIS ---
JIRA_URL = "https://jira.sescgo.com.br"
JIRA_USER = "milton.orgil"
JIRA_PASS = "%Qk4fs1*"

def garantir_infraestrutura():
    """Cria a pasta e o banco ANTES de tentar conectar na internet"""
    if not os.path.exists(PASTA_DATA):
        os.makedirs(PASTA_DATA)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Pasta 'data' criada.")

    conn = sqlite3.connect(CAMINHO_DB)
    cursor = conn.cursor()
    # Criação das tabelas com as 7 colunas solicitadas
    cursor.execute('''CREATE TABLE IF NOT EXISTS chamados (
                        chave TEXT PRIMARY KEY, 
                        titulo TEXT, 
                        prioridade TEXT, 
                        tipo TEXT,
                        relator TEXT, 
                        data_criacao TEXT,
                        data_atualizacao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS comentarios (
                        id_comentario TEXT PRIMARY KEY, 
                        chave_chamado TEXT, 
                        autor TEXT, 
                        corpo TEXT, 
                        data_criado TEXT)''')
    conn.commit()
    conn.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Infraestrutura do banco verificada e pronta.")

def formatar_data_amigavel(data_iso):
    """Formata atualização para 'há X dias HH:MM AM/PM'"""
    try:
        dt_obj = datetime.strptime(data_iso[:19], '%Y-%m-%dT%H:%M:%S')
        agora = datetime.now()
        diferenca = agora - dt_obj
        hora_formatada = dt_obj.strftime('%I:%M %p')
        if diferenca.days == 0: return f"hoje às {hora_formatada}"
        elif diferenca.days == 1: return f"ontem às {hora_formatada}"
        else: return f"há {diferenca.days} dias {hora_formatada}"
    except: return data_iso

def executar_sincronizacao():
    print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando varredura no Jira...")
    
    jql = 'project = CSSS AND status = "Suporte Multidata"'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {'jql': jql, 'fields': 'key,summary,priority,issuetype,reporter,created,updated,comment', 'maxResults': 50}

    try:
        # Reduzimos o timeout para 15s para o script não ficar "preso" se a rede cair
        response = requests.get(url, auth=(JIRA_USER, JIRA_PASS), params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Aviso: Jira retornou erro {response.status_code}. Tentaremos novamente no próximo ciclo.")
            return

        issues = response.json().get('issues', [])
        total_na_fila = len(issues)
        
        conn = sqlite3.connect(CAMINHO_DB)
        cursor = conn.cursor()

        novos = 0
        atualizados = 0

        for issue in issues:
            chave = issue['key']
            f = issue['fields']
            data_criacao = f.get('created')[:10] # Formato AAAA-MM-DD
            data_up_api = formatar_data_amigavel(f.get('updated'))
            
            cursor.execute('SELECT data_atualizacao FROM chamados WHERE chave = ?', (chave,))
            resultado = cursor.fetchone()
            
            if resultado is None: novos += 1
            elif resultado[0] != data_up_api: atualizados += 1

            cursor.execute('INSERT OR REPLACE INTO chamados VALUES (?,?,?,?,?,?,?)', 
                         (chave, f['summary'], f.get('priority', {}).get('name'), 
                          f.get('issuetype', {}).get('name'), f['reporter']['displayName'], 
                          data_criacao, data_up_api))

        conn.commit()
        conn.close()

        print(f"--- Relatório do Ciclo ---")
        print(f"Encontrados {total_na_fila} chamados na fila.")
        if novos > 0: print(f"-> {novos} novos adicionados.")
        if atualizados > 0: print(f"-> {atualizados} atualizados.")
        if novos == 0 and atualizados == 0: print(f"-> Nenhuma alteração.")
        print(f"--------------------------")

    except requests.exceptions.RequestException as e:
        print(f"Aviso de Rede: Servidor do Jira demorou a responder. Próxima tentativa em 30 min.")

# Agendamento
schedule.every(3).seconds.do(executar_sincronizacao)

if __name__ == "__main__":
    # 1. Garante que o banco exista ANTES de qualquer erro de rede
    garantir_infraestrutura()
    
    # 2. Tenta a primeira sincronização
    executar_sincronizacao()
    
    print("Monitoramento ativo. Aguardando próximos ciclos...")
    while True:
        schedule.run_pending()
        time.sleep(1)