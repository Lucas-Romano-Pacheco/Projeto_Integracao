import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÕES DO SYSAID ---
SYSAID_URL_BASE = "https://grupontsec.sysaidit.com"
SYSAID_USER = "lucas.pacheco"
SYSAID_PASS = "Chkp!234NTSEC02"

def criar_no_sysaid(info_jira):
    """Função que conecta no SysAid e cria o chamado"""
    session = requests.Session()
    
    # 1. Login no SysAid
    login_url = f"{SYSAID_URL_BASE}/api/v1/login"
    try:
        auth = session.post(login_url, json={"user_name": SYSAID_USER, "password": SYSAID_PASS})
        if auth.status_code != 200:
            print("[SYSAID] Falha na autenticação.")
            return None

        # 2. Montagem do chamado com dados do JIRA
        sr_url = f"{SYSAID_URL_BASE}/api/v1/sr"
        payload = {
            "info": [
                {"key": "title", "value": f"[{info_jira['key']}] {info_jira['summary']}"},
                {"key": "problem_desc", "value": f"Aberto via Integração Jira\nRelator: {info_jira['reporter']}\nStatus Jira: {info_jira['status']}"},
                {"key": "status", "value": "1"},       # 1 = Novo
                {"key": "urgency", "value": "2"},      # 2 = Normal
                {"key": "company", "value": "654"},    # ID da Zivasec visto no seu log
                {"key": "sr_type", "value": "1"}       # 1 = Incidente
            ]
        }

        # 3. Envio para o SysAid
        res = session.post(sr_url, json=payload)
        if res.status_code in [200, 201]:
            return res.json().get('id')
        else:
            print(f"[SYSAID] Erro ao criar: {res.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERRO] Falha na conexão: {e}")
        return None

@app.route('/receber-jira', methods=['POST'])
def receber_jira():
    dados = request.json
    if not dados:
        return jsonify({"status": "vazio"}), 400

    # Extração dos campos do JSON real do Jira
    issue = dados.get('issue', {})
    fields = issue.get('fields', {})
    
    info_jira = {
        "key": issue.get('key', 'N/A'),
        "summary": fields.get('summary', 'Sem assunto'),
        "reporter": fields.get('reporter', {}).get('displayName', 'Desconhecido'),
        "status": fields.get('status', {}).get('name', 'N/A')
    }

    print(f"\n[JIRA] Novo chamado detectado: {info_jira['key']}")
    print(f"[INFO] Processando integração para o SysAid...")

    # Chamada da função de automação
    id_sysaid = criar_no_sysaid(info_jira)

    if id_sysaid:
        print(f"[SUCESSO] Chamado {info_jira['key']} replicado no SysAid como ID: {id_sysaid}")
        return jsonify({"status": "sucesso", "sysaid_id": id_sysaid}), 200
    
    return jsonify({"status": "erro na integracao"}), 500

if __name__ == '__main__':
    import os
    # O Render define a porta automaticamente na variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)