import requests
import json
import sqlite3
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DATA = os.path.join(BASE_DIR, 'data')
PASTA_OUTPUT = os.path.join(BASE_DIR, 'output')
CAMINHO_DB = os.path.join(PASTA_DATA, 'integracao_jira.db')

# Garante que todas as pastas existam
for p in [PASTA_DATA, PASTA_OUTPUT]:
    if not os.path.exists(p): os.makedirs(p)

# --- CREDENCIAIS ---
JIRA_URL = "https://jira.sescgo.com.br"
JIRA_USER = "milton.orgil"
JIRA_PASS = "%Qk4fs1*"

def garantir_tabelas(cursor):
    """Cria a estrutura do banco se não existir"""
    cursor.execute('''CREATE TABLE IF NOT EXISTS chamados 
                      (chave TEXT PRIMARY KEY, titulo TEXT, status TEXT, relator TEXT, data_criacao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS comentarios 
                      (id_comentario TEXT PRIMARY KEY, chave_chamado TEXT, autor TEXT, corpo TEXT, data_criado TEXT)''')

def sincronizar_completo():
    print(f"[{datetime.now()}] Iniciando sincronização e geração de relatórios...")
    
    jql = 'project = CSSS AND status = "Suporte Multidata"'
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {'jql': jql, 'fields': 'key,summary,status,reporter,created,comment', 'maxResults': 50}

    try:
        response = requests.get(url, auth=(JIRA_USER, JIRA_PASS), params=params)
        if response.status_code != 200: return print(f"Erro Jira: {response.status_code}")
        
        dados_jira = response.json()
        issues = dados_jira.get('issues', [])

        # 1. SALVAR JSON BRUTO (Auditoria técnica)
        with open(os.path.join(PASTA_DATA, "ultimo_pull_jira.json"), "w", encoding="utf-8") as f:
            json.dump(dados_jira, f, indent=4, ensure_ascii=False)

        # 2. PROCESSAMENTO (Banco + TXT)
        conn = sqlite3.connect(CAMINHO_DB)
        cursor = conn.cursor()
        garantir_tabelas(cursor)

        # Caminhos dos arquivos TXT
        txt_chamados = os.path.join(PASTA_OUTPUT, "conferencia_jira.txt")
        txt_comentarios = os.path.join(PASTA_OUTPUT, "comentarios_extraidos.txt")

        with open(txt_chamados, "w", encoding="utf-8") as f_ch, open(txt_comentarios, "w", encoding="utf-8") as f_co:
            f_ch.write(f"RELATÓRIO DE CHAMADOS ABERTOS - {datetime.now()}\n" + "="*50 + "\n")
            f_co.write(f"HISTÓRICO DE COMENTÁRIOS - {datetime.now()}\n" + "="*50 + "\n")

            for issue in issues:
                chave = issue['key']
                f = issue['fields']
                
                # Salvar no Banco
                cursor.execute('INSERT OR REPLACE INTO chamados VALUES (?,?,?,?,?)', 
                             (chave, f['summary'], f['status']['name'], f['reporter']['displayName'], f['created']))
                
                # Escrever no TXT de Chamados
                f_ch.write(f"ID: {chave} | Título: {f['summary']} | Relator: {f['reporter']['displayName']}\n")

                # Processar Comentários
                f_co.write(f"\n>>> CHAMADO: {chave} <<<\n")
                comentarios = f.get('comment', {}).get('comments', [])
                
                if not comentarios:
                    f_co.write("Sem comentários.\n")
                else:
                    for c in comentarios:
                        # Salvar no Banco
                        cursor.execute('INSERT OR IGNORE INTO comentarios VALUES (?,?,?,?,?)',
                                     (c['id'], chave, c['author']['displayName'], c['body'], c['created']))
                        # Escrever no TXT de Comentários
                        f_co.write(f"[{c['created']}] {c['author']['displayName']}: {c['body']}\n")
                
                f_co.write("-" * 30 + "\n")

        conn.commit()
        conn.close()
        print(f"Sucesso! Banco atualizado e relatórios gerados na pasta /output.")

    except Exception as e:
        print(f"Falha na operação: {e}")

if __name__ == "__main__":
    sincronizar_completo()