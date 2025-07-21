import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import calendar
import time
import random
import hashlib
import threading
import json
import traceback
import requests
import base64

# Verificar se é modo admin (versão dinâmica corrigida)
is_admin = False
try:
    # Primeiro, tentar obter a chave dos secrets
    try:
        admin_key = st.secrets.get("ADMIN_URL_KEY", "desenvolvimento")
    except:
        admin_key = "desenvolvimento"  # Fallback para desenvolvimento local
    
    # Verificar query params (método novo)
    query_params = st.query_params
    is_admin = query_params.get("admin") == admin_key
    
except:
    try:
        # Método antigo (Streamlit Cloud mais antigo)
        try:
            admin_key = st.secrets.get("ADMIN_URL_KEY", "desenvolvimento")
        except:
            admin_key = "desenvolvimento"
        
        query_params = st.experimental_get_query_params()
        is_admin = query_params.get("admin", [None])[0] == admin_key
        
    except:
        # Fallback final
        is_admin = False

# Configuração da página (AGORA PODE SER PRIMEIRO!)
if is_admin:
    st.set_page_config(
        page_title="Painel Administrativo",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
else:
    st.set_page_config(
        page_title="Agendamento Online",
        page_icon="💆‍♀️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

# CSS UNIFICADO
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: #f8f9fa;
        min-height: 100vh;
    }
    
    .admin-header {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .admin-header h1 {
        color: #1f2937;
        font-size: 2rem;
        margin: 0;
        font-weight: 700;
    }
    
    .admin-header .badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
    }
    
    .main-header {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e9ecef;
    }
    
    .main-header h1 {
        color: #1f2937;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: #6b7280;
        font-size: 1.2rem;
        margin: 0;
    }
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .stat-card.success::before {
        background: linear-gradient(90deg, #10b981, #059669);
    }
    
    .stat-card.warning::before {
        background: linear-gradient(90deg, #f59e0b, #d97706);
    }
    
    .stat-card.danger::before {
        background: linear-gradient(90deg, #ef4444, #dc2626);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #6b7280;
        font-size: 1rem;
        font-weight: 500;
    }
    
    .main-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f1f3f5;
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border: 2px solid #e9ecef !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        background: #f8f9fa !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #667eea !important;
        background: white !important;
        box-shadow: 0px 0px 0px 3px rgba(102,126,234,0.1) !important;
    }
    
    .stTextInput > label,
    .stSelectbox > label,
    .stDateInput > label {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 16px !important;
        margin-bottom: 8px !important;
    }
    
    .stButton > button {
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: 2px solid transparent !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        box-shadow: 0px 4px 12px rgba(102,126,234,0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0px 6px 16px rgba(102,126,234,0.4) !important;
    }
    
    .alert {
        padding: 16px 20px;
        border-radius: 8px;
        margin: 16px 0;
        font-weight: 500;
        border-left: 4px solid;
    }
    
    .alert-success {
        background: #ecfdf5;
        color: #047857;
        border-left-color: #10b981;
    }
    
    .alert-error {
        background: #fef2f2;
        color: #b91c1c;
        border-left-color: #ef4444;
    }
    
    .alert-warning {
        background: #fffbeb;
        color: #b45309;
        border-left-color: #f59e0b;
    }
    
    .alert-info {
        background: #eff6ff;
        color: #1d4ed8;
        border-left-color: #3b82f6;
    }
    
    .appointment-summary {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 6px 24px;
        border-radius: 15px;
        margin: 20px 0;
        border-left: 5px solid #667eea;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
    }
    
    .appointment-summary h3 {
        color: #667eea;
        margin-bottom: 16px;
        font-size: 1.3rem;
    }
    
    .summary-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2px;   /* ← MENOS ESPAÇO */
        padding: 1px 0;      /* ← MENOS PADDING */
        border-bottom: 1px solid #dee2e6;
    }
    
    .summary-item:last-child {
        border-bottom: none;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        
        .admin-header {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
        }
        
        .stats-container {
            grid-template-columns: 1fr;
        }
        
        .main-card {
            padding: 1.5rem;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Configurações
DB = "agenda.db"
# Configurações
try:
    SENHA_CORRETA = st.secrets.get("ADMIN_PASSWORD", "admin123")
except:
    SENHA_CORRETA = "admin123"  # Para desenvolvimento local

# Funções do banco
def conectar():
    return sqlite3.connect(DB)

def init_config():
    conn = conectar()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT,
            telefone TEXT,
            data TEXT,
            horario TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS dias_uteis (
            dia TEXT PRIMARY KEY
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS bloqueios (
            data TEXT PRIMARY KEY
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')

    try:
        c.execute("SELECT email FROM agendamentos LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE agendamentos ADD COLUMN email TEXT DEFAULT ''")

    try:
        c.execute("SELECT status FROM agendamentos LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE agendamentos ADD COLUMN status TEXT DEFAULT 'pendente'")

    c.execute('''
        CREATE TABLE IF NOT EXISTS bloqueios_horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            horario TEXT,
            UNIQUE(data, horario)
        )
    ''')

    conn.commit()
    conn.close()

def obter_configuracao(chave, padrao=None):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT valor FROM configuracoes WHERE chave=?", (chave,))
        resultado = c.fetchone()
        if resultado:
            valor = resultado[0]
            if valor == "True":
                return True
            elif valor == "False":
                return False
            try:
                return int(valor)
            except ValueError:
                try:
                    return float(valor)
                except ValueError:
                    return valor
        return padrao
    except:
        return padrao
    finally:
        conn.close()

def salvar_configuracao(chave, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, str(valor)))
    conn.commit()
    conn.close()

def horario_disponivel(data, horario):
    conn = conectar()
    c = conn.cursor()
    
    # Verificar se há agendamento neste horário
    c.execute("SELECT * FROM agendamentos WHERE data=? AND horario=? AND status != 'cancelado'", (data, horario))
    if c.fetchone():
        conn.close()
        return False
    
    # Verificar se o dia inteiro está bloqueado
    try:
        c.execute("SELECT * FROM bloqueios WHERE data=?", (data,))
        if c.fetchone():
            conn.close()
            return False
    except:
        pass
    
    # NOVO: Verificar se a data está em algum período bloqueado
    if data_em_periodo_bloqueado(data):
        conn.close()
        return False    
    
    # Verificar se o horário específico está bloqueado
    try:
        c.execute("SELECT * FROM bloqueios_horarios WHERE data=? AND horario=?", (data, horario))
        if c.fetchone():
            conn.close()
            return False
    except:
        pass
    
    # Verificar bloqueios permanentes
    if horario_bloqueado_permanente(data, horario):
        conn.close()
        return False
    
    # NOVO: Verificar bloqueios semanais
    if horario_bloqueado_semanal(data, horario):
        conn.close()
        return False
    
    conn.close()
    return True

def adicionar_agendamento(nome, telefone, email, data, horario):
    """Adiciona agendamento com integração Todoist"""
    conn = conectar()
    c = conn.cursor()
    
    confirmacao_automatica = obter_configuracao("confirmacao_automatica", False)
    status_inicial = "confirmado" if confirmacao_automatica else "pendente"
    
    agendamento_id = None
    try:
        c.execute("INSERT INTO agendamentos (nome_cliente, telefone, email, data, horario, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (nome, telefone, email, data, horario, status_inicial))
        agendamento_id = c.lastrowid
        conn.commit()
    except sqlite3.OperationalError:
        c.execute("INSERT INTO agendamentos (nome_cliente, telefone, data, horario) VALUES (?, ?, ?, ?)",
                  (nome, telefone, data, horario))
        agendamento_id = c.lastrowid
        conn.commit()
    finally:
        conn.close()
    
    # Envio de emails (código original mantido)
    envio_automatico = obter_configuracao("envio_automatico", False)
    enviar_confirmacao = obter_configuracao("enviar_confirmacao", True)
    
    if status_inicial == "confirmado" and email and agendamento_id and envio_automatico and enviar_confirmacao:
        try:
            enviar_email_confirmacao(agendamento_id, nome, email, data, horario)
        except Exception as e:
            print(f"❌ Erro ao enviar email de confirmação automática: {e}")
    
    # NOVO: Integração com Todoist
    todoist_ativo = obter_configuracao("todoist_ativo", False)
    incluir_pendentes = obter_configuracao("todoist_incluir_pendentes", True)
    
    if todoist_ativo and agendamento_id:
        # Decidir se deve criar tarefa baseado nas configurações
        deve_criar = False
        
        if status_inicial == "confirmado":
            deve_criar = True  # Sempre cria para confirmados
        elif status_inicial == "pendente" and incluir_pendentes:
            deve_criar = True  # Só cria para pendentes se configurado
        
        if deve_criar:
            try:
                sucesso = criar_tarefa_todoist(agendamento_id, nome, telefone, email, data, horario)
                if sucesso:
                    print(f"✅ Tarefa Todoist criada: {nome} - {data} {horario}")
                else:
                    print(f"⚠️ Falha ao criar tarefa Todoist: {nome}")
            except Exception as e:
                print(f"❌ Erro na integração Todoist: {e}")
    
    backup_agendamentos_futuros_github()
    return status_inicial

def cancelar_agendamento(nome, telefone, data):
    """Cancela agendamento mudando status para 'cancelado' em vez de deletar"""
    conn = conectar()
    c = conn.cursor()
    
    # Buscar TODOS os agendamentos do dia
    agendamentos_do_dia = []
    
    try:
        c.execute("SELECT id, email, horario FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=? AND status IN ('pendente', 'confirmado')", (nome, telefone, data))
        agendamentos_do_dia = c.fetchall()
    except sqlite3.OperationalError:
        try:
            c.execute("SELECT id, horario FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=? AND status IN ('pendente', 'confirmado')", (nome, telefone, data))
            agendamentos_sem_email = c.fetchall()
            agendamentos_do_dia = [(ag[0], '', ag[1]) for ag in agendamentos_sem_email]
        except:
            c.execute("SELECT id, horario FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=?", (nome, telefone, data))
            agendamentos_sem_email = c.fetchall()
            agendamentos_do_dia = [(ag[0], '', ag[1]) for ag in agendamentos_sem_email]
    
    # Verificar se existem agendamentos CANCELÁVEIS
    try:
        c.execute("SELECT COUNT(*) FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=? AND status IN ('pendente', 'confirmado')", (nome, telefone, data))
        existe = c.fetchone()[0] > 0
    except sqlite3.OperationalError:
        c.execute("SELECT COUNT(*) FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=?", (nome, telefone, data))
        existe = c.fetchone()[0] > 0
    
    if existe and agendamentos_do_dia:
        # Cancelar TODOS os agendamentos do dia no sistema
        try:
            c.execute("UPDATE agendamentos SET status = 'cancelado' WHERE nome_cliente=? AND telefone=? AND data=?", 
                     (nome, telefone, data))
            conn.commit()
            conn.close()

            print(f"✅ {len(agendamentos_do_dia)} agendamento(s) cancelado(s): {nome} - {data}")

            # NOVO: Integração com Todoist para MÚLTIPLOS eventos
            todoist_ativo = obter_configuracao("todoist_ativo", False)
            remover_cancelados = obter_configuracao("todoist_remover_cancelados", True)
            
            if todoist_ativo and remover_cancelados:
                eventos_deletados = 0
                for agendamento in agendamentos_do_dia:
                    agendamento_id = agendamento[0]
                    horario = agendamento[2]
                    
                    try:
                        sucesso = deletar_tarefa_todoist(data, nome)
                        if sucesso:
                            eventos_deletados += 1
                            print(f"✅ Tarefa Todoist removida: {horario}")
                        else:
                            print(f"⚠️ Falha ao remover tarefa Todoist: {horario}")
                    except Exception as e:
                        print(f"❌ Erro ao remover tarefa Todoist {horario}: {e}")
                
                print(f"📝 Todoist: {eventos_deletados}/{len(agendamentos_do_dia)} tarefas removidas")
            
            # Enviar email de cancelamento (código original mantido)
            envio_automatico = obter_configuracao("envio_automatico", False)
            enviar_cancelamento = obter_configuracao("enviar_cancelamento", True)
            
            if envio_automatico and enviar_cancelamento and agendamentos_do_dia:
                primeiro_agendamento = agendamentos_do_dia[0]
                email_cliente = primeiro_agendamento[1] if len(primeiro_agendamento) > 1 else ""
                
                if email_cliente:
                    if len(agendamentos_do_dia) > 1:
                        horarios_cancelados = ", ".join([ag[2] for ag in agendamentos_do_dia])
                        horario_para_email = f"Horários: {horarios_cancelados}"
                    else:
                        horario_para_email = agendamentos_do_dia[0][2]
                    
                    try:
                        sucesso = enviar_email_cancelamento(nome, email_cliente, data, horario_para_email, "cliente")
                        if sucesso:
                            print(f"✅ Email de cancelamento enviado para {email_cliente}")
                        else:
                            print(f"❌ Falha ao enviar email de cancelamento para {email_cliente}")
                    except Exception as e:
                        print(f"❌ Erro ao enviar email de cancelamento: {e}")
            
            backup_agendamentos_futuros_github()
            return True
            
        except sqlite3.OperationalError:
            # Se não tem coluna status, criar ela e tentar novamente
            try:
                c.execute("ALTER TABLE agendamentos ADD COLUMN status TEXT DEFAULT 'pendente'")
                conn.commit()
                
                c.execute("UPDATE agendamentos SET status = 'cancelado' WHERE nome_cliente=? AND telefone=? AND data=?", 
                         (nome, telefone, data))
                conn.commit()
                conn.close()
                
                print(f"✅ {len(agendamentos_do_dia)} agendamento(s) cancelado(s): {nome} - {data}")
                
                # Todoist e email (mesmo código de cima)
                todoist_ativo = obter_configuracao("todoist_ativo", False)
                remover_cancelados = obter_configuracao("todoist_remover_cancelados", True)
                
                if todoist_ativo and remover_cancelados:
                    eventos_deletados = 0
                    for agendamento in agendamentos_do_dia:
                        agendamento_id = agendamento[0]
                        horario = agendamento[2]
                        
                        try:
                            sucesso = deletar_tarefa_todoist(data, nome)
                            if sucesso:
                                eventos_deletados += 1
                                print(f"✅ Tarefa Todoist removida: {horario}")
                        except Exception as e:
                            print(f"❌ Erro ao remover tarefa Todoist {horario}: {e}")
                    
                    print(f"📝 Todoist: {eventos_deletados}/{len(agendamentos_do_dia)} tarefas removidas")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro ao atualizar status: {e}")
                conn.close()
                return False
        
    else:
        conn.close()
        return False

def obter_dias_uteis():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT dia FROM dias_uteis")
        dias = [linha[0] for linha in c.fetchall()]
        if not dias:
            dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    except:
        dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    conn.close()
    return dias

def salvar_dias_uteis(dias):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM dias_uteis")
    for dia in dias:
        c.execute("INSERT INTO dias_uteis (dia) VALUES (?)", (dia,))
    conn.commit()
    conn.close()

def obter_datas_bloqueadas():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT data FROM bloqueios")
        datas = [linha[0] for linha in c.fetchall()]
    except:
        datas = []
    conn.close()
    return datas

def adicionar_bloqueio(data):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bloqueios (data) VALUES (?)", (data,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remover_bloqueio(data):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM bloqueios WHERE data=?", (data,))
    conn.commit()
    conn.close()

def obter_bloqueios():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT data FROM bloqueios ORDER BY data")
        datas = [linha[0] for linha in c.fetchall()]
    except:
        datas = []
    conn.close()
    return datas

def buscar_agendamentos():
    conn = conectar()
    c = conn.cursor()
    
    try:
        c.execute("SELECT id, data, horario, nome_cliente, telefone, email, status FROM agendamentos ORDER BY data, horario")
        agendamentos = c.fetchall()
    except:
        try:
            c.execute("SELECT id, data, horario, nome_cliente, telefone FROM agendamentos ORDER BY data, horario")
            agendamentos_sem_extras = c.fetchall()
            agendamentos = [ag + ('', 'pendente') for ag in agendamentos_sem_extras]
        except:
            agendamentos = []
    
    conn.close()
    return agendamentos

def atualizar_status_agendamento(agendamento_id, novo_status):
    """Atualiza status do agendamento com integração Todoist"""
    conn = conectar()
    c = conn.cursor()
    
    # Buscar dados do agendamento antes de atualizar
    c.execute("SELECT nome_cliente, email, data, horario, telefone FROM agendamentos WHERE id = ?", (agendamento_id,))
    agendamento_dados = c.fetchone()
    
    # Atualizar status
    c.execute("UPDATE agendamentos SET status = ? WHERE id = ?", (novo_status, agendamento_id))
    conn.commit()
    conn.close()
    
    # NOVO: Integração com Todoist
    todoist_ativo = obter_configuracao("todoist_ativo", False)
    
    if todoist_ativo and agendamento_dados:
        nome_cliente = agendamento_dados[0]
        email = agendamento_dados[1] if len(agendamento_dados) > 1 else ""
        data = agendamento_dados[2] if len(agendamento_dados) > 2 else ""
        horario = agendamento_dados[3] if len(agendamento_dados) > 3 else ""
        telefone = agendamento_dados[4] if len(agendamento_dados) > 4 else ""
        
        try:
            if novo_status == 'confirmado':
                # Verificar se tarefa já existe
                tarefa_existente = obter_configuracao(f"todoist_task_{agendamento_id}", "")
                
                if not tarefa_existente:
                    # Criar nova tarefa se não existe
                    sucesso = criar_tarefa_todoist(agendamento_id, nome_cliente, telefone, email, data, horario)
                    if sucesso:
                        print(f"✅ Tarefa Todoist criada para confirmação: {nome_cliente}")
                else:
                    # Atualizar tarefa existente
                    sucesso = atualizar_tarefa_todoist(agendamento_id, nome_cliente, novo_status)
                    if sucesso:
                        print(f"✅ Tarefa Todoist atualizada para confirmado: {nome_cliente}")
                
            elif novo_status == 'atendido':
                # Marcar como concluída
                marcar_concluido = obter_configuracao("todoist_marcar_concluido", True)
                if marcar_concluido:
                    sucesso = atualizar_tarefa_todoist(agendamento_id, nome_cliente, novo_status)
                    if sucesso:
                        print(f"🎉 Tarefa Todoist marcada como concluída: {nome_cliente}")
                
            elif novo_status == 'cancelado':
                # Remover tarefa
                remover_cancelados = obter_configuracao("todoist_remover_cancelados", True)
                if remover_cancelados:
                    sucesso = deletar_tarefa_todoist(data, nome_cliente)
                    if sucesso:
                        print(f"🗑️ Tarefa Todoist removida: {nome_cliente}")
                
        except Exception as e:
            print(f"❌ Erro na integração Todoist: {e}")
    
    # Envio de emails (código original mantido)
    envio_automatico = obter_configuracao("envio_automatico", False)
    enviar_confirmacao = obter_configuracao("enviar_confirmacao", True)
    
    if novo_status == 'confirmado' and agendamento_dados and len(agendamento_dados) >= 4 and envio_automatico and enviar_confirmacao:
        nome_cliente, email, data, horario = agendamento_dados[:4]
        if email:
            try:
                enviar_email_confirmacao(agendamento_id, nome_cliente, email, data, horario)
            except Exception as e:
                print(f"❌ Erro ao enviar email de confirmação: {e}")
    
    # Email de cancelamento
    enviar_cancelamento = obter_configuracao("enviar_cancelamento", True)
    
    if novo_status == 'cancelado' and agendamento_dados and len(agendamento_dados) >= 4 and envio_automatico and enviar_cancelamento:
        nome_cliente, email, data, horario = agendamento_dados[:4]
        if email:
            try:
                enviar_email_cancelamento(nome_cliente, email, data, horario, "admin")
            except Exception as e:
                print(f"❌ Erro ao enviar email de cancelamento: {e}")
    
    backup_agendamentos_futuros_github()           

def deletar_agendamento(agendamento_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM agendamentos WHERE id=?", (agendamento_id,))
    conn.commit()
    conn.close()
    backup_agendamentos_futuros_github()

def adicionar_bloqueio_horario(data, horario):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bloqueios_horarios (data, horario) VALUES (?, ?)", (data, horario))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remover_bloqueio_horario(data, horario):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM bloqueios_horarios WHERE data=? AND horario=?", (data, horario))
    conn.commit()
    conn.close()

def obter_bloqueios_horarios():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT data, horario FROM bloqueios_horarios ORDER BY data, horario")
        bloqueios = c.fetchall()
    except:
        bloqueios = []
    conn.close()
    return bloqueios

def adicionar_bloqueio_permanente(horario_inicio, horario_fim, dias_semana, descricao):
    conn = conectar()
    c = conn.cursor()
    try:
        # Criar tabela se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS bloqueios_permanentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horario_inicio TEXT,
                horario_fim TEXT,
                dias_semana TEXT,
                descricao TEXT
            )
        ''')
        
        dias_str = ",".join(dias_semana)
        c.execute("INSERT INTO bloqueios_permanentes (horario_inicio, horario_fim, dias_semana, descricao) VALUES (?, ?, ?, ?)", 
                  (horario_inicio, horario_fim, dias_str, descricao))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao adicionar bloqueio permanente: {e}")
        return False
    finally:
        conn.close()

def obter_bloqueios_permanentes():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT id, horario_inicio, horario_fim, dias_semana, descricao FROM bloqueios_permanentes ORDER BY horario_inicio")
        bloqueios = c.fetchall()
        return bloqueios
    except:
        return []
    finally:
        conn.close()

def remover_bloqueio_permanente(bloqueio_id):
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM bloqueios_permanentes WHERE id=?", (bloqueio_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def horario_bloqueado_permanente(data, horario):
    """Verifica se um horário está bloqueado permanentemente"""
    conn = conectar()
    c = conn.cursor()
    try:
        # Descobrir o dia da semana
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        dia_semana = data_obj.strftime("%A")  # Monday, Tuesday, etc.
        
        # Buscar bloqueios permanentes
        c.execute("SELECT horario_inicio, horario_fim, dias_semana FROM bloqueios_permanentes")
        bloqueios = c.fetchall()
        
        for inicio, fim, dias in bloqueios:
            # Verificar se o dia está nos dias bloqueados
            if dia_semana in dias.split(","):
                # Verificar se o horário está no intervalo
                if inicio <= horario <= fim:
                    return True
        
        return False
    except:
        return False
    finally:
        conn.close()

def adicionar_bloqueio_semanal(dia_semana, horarios_bloqueados, descricao=""):
    """Adiciona bloqueio recorrente para um dia da semana específico"""
    conn = conectar()
    c = conn.cursor()
    try:
        # Criar tabela se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS bloqueios_semanais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dia_semana TEXT,
                horarios TEXT,
                descricao TEXT,
                UNIQUE(dia_semana, horarios)
            )
        ''')
        
        horarios_str = ",".join(horarios_bloqueados)
        c.execute("INSERT INTO bloqueios_semanais (dia_semana, horarios, descricao) VALUES (?, ?, ?)", 
                  (dia_semana, horarios_str, descricao))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Erro ao adicionar bloqueio semanal: {e}")
        return False
    finally:
        conn.close()

def obter_bloqueios_semanais():
    """Obtém todos os bloqueios semanais"""
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("SELECT id, dia_semana, horarios, descricao FROM bloqueios_semanais ORDER BY dia_semana")
        bloqueios = c.fetchall()
        return bloqueios
    except:
        return []
    finally:
        conn.close()

def remover_bloqueio_semanal(bloqueio_id):
    """Remove um bloqueio semanal"""
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM bloqueios_semanais WHERE id=?", (bloqueio_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def horario_bloqueado_semanal(data, horario):
    """Verifica se um horário está bloqueado por regra semanal"""
    conn = conectar()
    c = conn.cursor()
    try:
        # Descobrir o dia da semana
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        dia_semana = data_obj.strftime("%A")  # Monday, Tuesday, etc.
        
        # Buscar bloqueios semanais para este dia
        c.execute("SELECT horarios FROM bloqueios_semanais WHERE dia_semana=?", (dia_semana,))
        bloqueios = c.fetchall()
        
        for (horarios_str,) in bloqueios:
            horarios_bloqueados = horarios_str.split(",")
            if horario in horarios_bloqueados:
                return True
        
        return False
    except:
        return False
    finally:
        conn.close()

def enviar_email_confirmacao(agendamento_id, cliente_nome, cliente_email, data, horario):
    """Envia email de confirmação automático"""
    
    if not obter_configuracao("envio_automatico", False):
        return False
    
    try:
        # Obter configurações de email
        email_sistema = obter_configuracao("email_sistema", "")
        senha_email = obter_configuracao("senha_email", "")
        servidor_smtp = obter_configuracao("servidor_smtp", "smtp.gmail.com")
        porta_smtp = obter_configuracao("porta_smtp", 587)
        
        if not email_sistema or not senha_email:
            return False
        
        # Obter dados do profissional
        nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
        especialidade = obter_configuracao("especialidade", "Clínico Geral")
        nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
        telefone_contato = obter_configuracao("telefone_contato", "(11) 3333-4444")
        whatsapp = obter_configuracao("whatsapp", "(11) 99999-9999")
        
        # Endereço completo
        endereco_rua = obter_configuracao("endereco_rua", "Rua das Flores, 123")
        endereco_bairro = obter_configuracao("endereco_bairro", "Centro")
        endereco_cidade = obter_configuracao("endereco_cidade", "São Paulo - SP")
        endereco_completo = f"{endereco_rua}, {endereco_bairro}, {endereco_cidade}"
        
        instrucoes_chegada = obter_configuracao("instrucoes_chegada", "Favor chegar 10 minutos antes do horário agendado.")
        
        # Formatar data
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        data_formatada = data_obj.strftime("%d/%m/%Y - %A")
        data_formatada = data_formatada.replace('Monday', 'Segunda-feira')\
            .replace('Tuesday', 'Terça-feira').replace('Wednesday', 'Quarta-feira')\
            .replace('Thursday', 'Quinta-feira').replace('Friday', 'Sexta-feira')\
            .replace('Saturday', 'Sábado').replace('Sunday', 'Domingo')
        
        # Usar template personalizado ou padrão
        template = obter_configuracao("template_confirmacao", 
            "Olá {nome}!\n\nSeu agendamento foi confirmado:\n📅 Data: {data}\n⏰ Horário: {horario}\n\nAguardamos você!")
        
        # Substituir variáveis no template
        corpo = template.format(
            nome=cliente_nome,
            data=data_formatada,
            horario=horario,
            local=nome_clinica,
            endereco=endereco_completo,
            profissional=nome_profissional,
            especialidade=especialidade
        )
        
        # Adicionar informações extras
        corpo += f"""

📍 Local: {nome_clinica}
🏠 Endereço: {endereco_completo}
📞 Telefone: {telefone_contato}
💬 WhatsApp: {whatsapp}

📝 Instruções importantes:
{instrucoes_chegada}

Atenciosamente,
{nome_profissional} - {especialidade}
{nome_clinica}
"""
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = email_sistema
        msg['To'] = cliente_email
        msg['Subject'] = f"✅ Agendamento Confirmado - {nome_profissional}"
        
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        
        # Enviar email
        server = smtplib.SMTP(servidor_smtp, porta_smtp)
        server.starttls()
        server.login(email_sistema, senha_email)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

def enviar_email_cancelamento(cliente_nome, cliente_email, data, horario, cancelado_por="cliente"):
    """Envia email de cancelamento"""
    
    if not obter_configuracao("envio_automatico", False):
        return False
    
    try:
        # Obter configurações de email
        email_sistema = obter_configuracao("email_sistema", "")
        senha_email = obter_configuracao("senha_email", "")
        servidor_smtp = obter_configuracao("servidor_smtp", "smtp.gmail.com")
        porta_smtp = obter_configuracao("porta_smtp", 587)
        
        if not email_sistema or not senha_email:
            return False
        
        # Obter dados do profissional
        nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
        especialidade = obter_configuracao("especialidade", "Clínico Geral")
        nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
        telefone_contato = obter_configuracao("telefone_contato", "(11) 3333-4444")
        whatsapp = obter_configuracao("whatsapp", "(11) 99999-9999")
        
        # Endereço completo
        endereco_rua = obter_configuracao("endereco_rua", "Rua das Flores, 123")
        endereco_bairro = obter_configuracao("endereco_bairro", "Centro")
        endereco_cidade = obter_configuracao("endereco_cidade", "São Paulo - SP")
        endereco_completo = f"{endereco_rua}, {endereco_bairro}, {endereco_cidade}"
        
        # Formatar data
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        data_formatada = data_obj.strftime("%d/%m/%Y - %A")
        data_formatada = data_formatada.replace('Monday', 'Segunda-feira')\
            .replace('Tuesday', 'Terça-feira').replace('Wednesday', 'Quarta-feira')\
            .replace('Thursday', 'Quinta-feira').replace('Friday', 'Sexta-feira')\
            .replace('Saturday', 'Sábado').replace('Sunday', 'Domingo')
        
        # Criar mensagem baseada em quem cancelou
        msg = MIMEMultipart()
        msg['From'] = email_sistema
        msg['To'] = cliente_email
        
        if cancelado_por == "cliente":
            msg['Subject'] = f"✅ Cancelamento Confirmado - {nome_profissional}"
            corpo = f"""
Olá {cliente_nome}!

Seu cancelamento foi processado com sucesso!

📅 Data cancelada: {data_formatada}
⏰ Horário cancelado: {horario}
🏥 Local: {nome_clinica}

Você pode fazer um novo agendamento quando desejar através do nosso sistema online.

📞 Dúvidas? Entre em contato:
📱 Telefone: {telefone_contato}
💬 WhatsApp: {whatsapp}

Atenciosamente,
{nome_profissional} - {especialidade}
{nome_clinica}
"""
        else:
            msg['Subject'] = f"⚠️ Agendamento Cancelado - {nome_profissional}"
            corpo = f"""
Olá {cliente_nome}!

Infelizmente precisamos cancelar seu agendamento:

📅 Data: {data_formatada}
⏰ Horário: {horario}
🏥 Local: {nome_clinica}

Pedimos desculpas pelo inconveniente. 

Por favor, entre em contato conosco para reagendar:
📞 Telefone: {telefone_contato}
💬 WhatsApp: {whatsapp}
📍 Endereço: {endereco_completo}

Ou faça um novo agendamento através do nosso sistema online.

Atenciosamente,
{nome_profissional} - {especialidade}
{nome_clinica}
"""
        
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        
        # Enviar email
        server = smtplib.SMTP(servidor_smtp, porta_smtp)
        server.starttls()
        server.login(email_sistema, senha_email)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email de cancelamento: {e}")
        return False

def exportar_agendamentos_csv():
    """Exporta todos os agendamentos para CSV"""
    import csv
    import io
    
    try:
        # Buscar todos os agendamentos
        # Buscar apenas agendamentos futuros
        agendamentos_todos = buscar_agendamentos()

        # Filtrar só os futuros
        hoje = datetime.now().date()
        agendamentos = []
        for agendamento in agendamentos_todos:
            try:
                data_agendamento = datetime.strptime(agendamento[1], "%Y-%m-%d").date()
                if data_agendamento >= hoje:
                    agendamentos.append(agendamento)
            except:
                continue
        
        if not agendamentos:
            return None
        
        # Criar buffer em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['ID', 'Data', 'Horário', 'Nome', 'Telefone', 'Email', 'Status'])
        
        # Dados
        for agendamento in agendamentos:
            if len(agendamento) == 7:
                writer.writerow(agendamento)
            elif len(agendamento) == 6:
                # Adicionar status padrão se não existir
                row = list(agendamento) + ['pendente']
                writer.writerow(row)
            else:
                # Formato antigo sem email
                row = list(agendamento) + ['Não informado', 'pendente']
                writer.writerow(row)
        
        # Retornar conteúdo do CSV
        csv_data = output.getvalue()
        output.close()
        
        return csv_data
        
    except Exception as e:
        st.error(f"Erro ao exportar: {e}")
        return None

def importar_agendamentos_csv(csv_content):
    """Importa agendamentos de um arquivo CSV"""
    import csv
    import io
    
    try:
        # Ler o conteúdo CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        conn = conectar()
        c = conn.cursor()
        
        importados = 0
        duplicados = 0
        erros = 0
        
        for row in reader:
            try:
                # Extrair dados do CSV
                agendamento_id = row.get('ID', '')
                data = row.get('Data', '')
                horario = row.get('Horário', '') or row.get('Horario', '')
                nome = row.get('Nome', '')
                telefone = row.get('Telefone', '')
                email = row.get('Email', '') or row.get('E-mail', '') or ''
                status = row.get('Status', 'pendente')
                
                # Validar dados obrigatórios
                if not all([data, horario, nome, telefone]):
                    erros += 1
                    continue
                
                # Verificar se já existe (evitar duplicatas)
                c.execute("SELECT COUNT(*) FROM agendamentos WHERE data=? AND horario=? AND nome_cliente=? AND telefone=? AND status IN ('pendente', 'confirmado')", 
                         (data, horario, nome, telefone))
                
                if c.fetchone()[0] > 0:
                    duplicados += 1
                    continue
                
                # Inserir no banco
                try:
                    c.execute("""INSERT INTO agendamentos 
                               (nome_cliente, telefone, email, data, horario, status) 
                               VALUES (?, ?, ?, ?, ?, ?)""",
                             (nome, telefone, email, data, horario, status))
                    importados += 1
                except sqlite3.OperationalError:
                    # Versão antiga sem email e status
                    c.execute("""INSERT INTO agendamentos 
                               (nome_cliente, telefone, data, horario) 
                               VALUES (?, ?, ?, ?)""",
                             (nome, telefone, data, horario))
                    importados += 1
                    
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                erros += 1
                continue
        
        conn.commit()
        conn.close()
        
        return {
            'importados': importados,
            'duplicados': duplicados, 
            'erros': erros,
            'sucesso': True
        }
        
    except Exception as e:
        return {
            'importados': 0,
            'duplicados': 0,
            'erros': 0,
            'sucesso': False,
            'erro': str(e)
        }

# ========================================
# 2. ADICIONAR ESTAS FUNÇÕES ANTES DA LINHA "# Inicializar banco":
# ========================================

def criar_menu_horizontal():
    """Cria menu horizontal responsivo para admin"""
    
    # Inicializar opção padrão se não existir
    if 'menu_opcao' not in st.session_state:
        st.session_state.menu_opcao = "⚙️ Configurações Gerais"
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 0.5rem; border-radius: 4px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(59,130,246,0.2);">
        <p style="color: white; text-align: center; margin: 0; font-size: 1rem; font-weight: 400; letter-spacing: 1px;">🔧 Menu Administrativo</p>
    """, unsafe_allow_html=True)
    
    # Menu responsivo ATUALIZADO com 7 colunas (NOVO!)
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        if st.button("⚙️ **Configurações**", 
                    key="btn_config", 
                    use_container_width=True,
                    help="Configurações gerais do sistema"):
            st.session_state.menu_opcao = "⚙️ Configurações Gerais"
            st.rerun()
    
    with col2:
        if st.button("📅 **Agenda**", 
                    key="btn_agenda", 
                    use_container_width=True,
                    help="Configurar dias úteis"):
            st.session_state.menu_opcao = "📅 Configurar Agenda"
            st.rerun()
    
    with col3:
        if st.button("🗓️ **Bloqueios**", 
                    key="btn_bloqueios", 
                    use_container_width=True,
                    help="Gerenciar bloqueios de datas/horários"):
            st.session_state.menu_opcao = "🗓️ Gerenciar Bloqueios"
            st.rerun()
    
    with col4:
        if st.button("👥 **Agendamentos**", 
                    key="btn_agendamentos", 
                    use_container_width=True,
                    help="Lista de todos os agendamentos"):
            st.session_state.menu_opcao = "👥 Lista de Agendamentos"
            st.rerun()
    
    with col5:
        if st.button("💾 **Backup**", 
                    key="btn_backup", 
                    use_container_width=True,
                    help="Backup e restauração de dados"):
            st.session_state.menu_opcao = "💾 Backup & Restauração"
            st.rerun()
    
    with col6:
        if st.button("🔗 **Integrações**", 
                    key="btn_integracoes", 
                    use_container_width=True,
                    help="Integração com Todoist e outros serviços"):
            st.session_state.menu_opcao = "🔗 Integrações"
            st.rerun()
    
    with col7:
        if st.button("🚪 **Sair**", 
                    key="btn_sair", 
                    use_container_width=True,
                    help="Fazer logout do painel admin"):
            st.session_state.authenticated = False
            st.session_state.menu_opcao = "⚙️ Configurações Gerais"  # Reset
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar opção atual selecionada
    st.markdown(f"""
    <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
        <span style="color: #667eea; font-weight: 600;">📍 Seção atual: {st.session_state.menu_opcao}</span>
    </div>
    """, unsafe_allow_html=True)
    
    return st.session_state.menu_opcao


def get_github_config():
    """Obtém configurações do GitHub"""
    
    # Configuração padrão (fallback)
    config_local = {
        "token": "",  # ← Vazio agora!
        "repo": st.secrets["GITHUB_REPO"],
        "branch": "main",
        "config_file": "configuracoes.json"
    }    
    # Tentar usar secrets primeiro (para Streamlit Cloud)
    try:
        return {
            "token": st.secrets["GITHUB_TOKEN"],
            "repo": st.secrets["GITHUB_REPO"],
            "branch": st.secrets.get("GITHUB_BRANCH", "main"),
            "config_file": st.secrets.get("CONFIG_FILE", "configuracoes.json")
        }
    except:
        # Fallback para configuração local
        return config_local

def backup_configuracoes_github():
    """Faz backup COMPLETO de todas as configurações para GitHub"""
    try:
        github_config = get_github_config()
        if not github_config or not github_config.get("token"):
            print("❌ Configuração GitHub não encontrada")
            return False
        
        # 1. Buscar CONFIGURAÇÕES GERAIS do banco local
        conn = conectar()
        c = conn.cursor()
        
        backup_data = {}
        
        try:
            c.execute("SELECT chave, valor FROM configuracoes")
            configs = dict(c.fetchall())
            backup_data.update(configs)
        except:
            backup_data = {}
        
        # 2. Buscar DIAS ÚTEIS
        try:
            backup_data['dias_uteis'] = obter_dias_uteis()
        except:
            backup_data['dias_uteis'] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        # 3. Buscar BLOQUEIOS INDIVIDUAIS
        try:
            backup_data['bloqueios_individuais'] = obter_bloqueios()
        except:
            backup_data['bloqueios_individuais'] = []
        
        # 4. Buscar BLOQUEIOS DE PERÍODOS
        try:
            backup_data['bloqueios_periodos'] = obter_bloqueios_periodos()
        except:
            backup_data['bloqueios_periodos'] = []
        
        # 5. Buscar BLOQUEIOS PERMANENTES
        try:
            backup_data['bloqueios_permanentes'] = obter_bloqueios_permanentes()
        except:
            backup_data['bloqueios_permanentes'] = []
        
        # 6. Buscar BLOQUEIOS SEMANAIS
        try:
            backup_data['bloqueios_semanais'] = obter_bloqueios_semanais()
        except:
            backup_data['bloqueios_semanais'] = []
        
        # 7. Buscar BLOQUEIOS DE HORÁRIOS ESPECÍFICOS
        try:
            backup_data['bloqueios_horarios'] = obter_bloqueios_horarios()
        except:
            backup_data['bloqueios_horarios'] = []
        
        conn.close()
        
        # Adicionar informações do backup
        backup_data['_backup_timestamp'] = datetime.now().isoformat()
            # Versão expandida!
        backup_data['_sistema'] = 'Agenda Online - Backup Completo'
        backup_data['_conteudo'] = [
            'configuracoes_gerais',
            'dias_uteis', 
            'bloqueios_individuais',
            'bloqueios_periodos',
            'bloqueios_permanentes', 
            'bloqueios_semanais',
            'bloqueios_horarios'
        ]
        
        # Converter para JSON bonito
        config_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        # Enviar para GitHub
        sucesso = upload_to_github(config_json, github_config)
        
        if sucesso:
            print(f"✅ Backup COMPLETO enviado para GitHub!")
            print(f"📊 Incluído: {len(backup_data)} configurações")
            print(f"📅 Dias úteis: {len(backup_data.get('dias_uteis', []))}")
            print(f"🗓️ Bloqueios: {len(backup_data.get('bloqueios_individuais', []))} individuais")
            print(f"📆 Períodos: {len(backup_data.get('bloqueios_periodos', []))}")
            print(f"⏰ Permanentes: {len(backup_data.get('bloqueios_permanentes', []))}")
            print(f"📋 Semanais: {len(backup_data.get('bloqueios_semanais', []))}")
            print(f"🕐 Horários: {len(backup_data.get('bloqueios_horarios', []))}")
        
        return sucesso
        
    except Exception as e:
        print(f"❌ Erro no backup GitHub expandido: {e}")
        return False

def upload_to_github(content, github_config):
    """Upload de arquivo para GitHub"""
    try:
        headers = {
            "Authorization": f"token {github_config['token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sistema-Agendamento"
        }
        
        # URL da API GitHub
        api_url = f"https://api.github.com/repos/{github_config['repo']}/contents/{github_config['config_file']}"
        
        print(f"🔗 Conectando: {api_url}")
        
        # Verificar se arquivo já existe (para obter SHA)
        response = requests.get(api_url, headers=headers)
        sha = None
        
        if response.status_code == 200:
            sha = response.json()["sha"]
            print("📄 Arquivo existente encontrado, atualizando...")
        elif response.status_code == 404:
            print("📄 Criando arquivo novo...")
        else:
            print(f"⚠️ Resposta inesperada: {response.status_code}")
        
        # Preparar dados para upload
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": f"Backup configurações - {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            "content": content_encoded,
            "branch": github_config['branch']
        }
        
        if sha:
            data["sha"] = sha
        
        # Fazer upload
        print("📤 Enviando backup...")
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print("✅ Backup enviado para GitHub com sucesso!")
            return True
        else:
            print(f"❌ Erro no upload GitHub: {response.status_code}")
            print(f"📋 Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no upload GitHub: {e}")
        return False


def restaurar_configuracoes_github():
    """Restaura TODAS as configurações do GitHub"""
    try:
        github_config = get_github_config()
        if not github_config or not github_config.get("token"):
            print("⚠️ Configuração GitHub não encontrada para restauração")
            return False
        
        # Baixar arquivo do GitHub
        config_json = download_from_github(github_config)
        if not config_json:
            print("📄 Nenhum backup encontrado no GitHub")
            return False
        
        # Parse do JSON
        backup_data = json.loads(config_json)
        
        # Verificar versão do backup
        versao = backup_data.get('_backup_version', '1.0')
        print(f"📦 Restaurando backup versão {versao}")
        
        conn = conectar()
        c = conn.cursor()
        
        # IMPORTANTE: Criar TODAS as tabelas necessárias ANTES de restaurar
        # Tabela de bloqueios permanentes
        c.execute('''
            CREATE TABLE IF NOT EXISTS bloqueios_permanentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                horario_inicio TEXT,
                horario_fim TEXT,
                dias_semana TEXT,
                descricao TEXT
            )
        ''')
        
        # Tabela de bloqueios semanais
        c.execute('''
            CREATE TABLE IF NOT EXISTS bloqueios_semanais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dia_semana TEXT,
                horarios TEXT,
                descricao TEXT,
                UNIQUE(dia_semana, horarios)
            )
        ''')
        
        # Tabela de bloqueios de período
        c.execute('''
            CREATE TABLE IF NOT EXISTS bloqueios_periodos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inicio TEXT,
                data_fim TEXT,
                descricao TEXT,
                criado_em TEXT
            )
        ''')
        
        conn.commit()
        
        restaurados = 0
        
        try:
            # 1. RESTAURAR CONFIGURAÇÕES GERAIS
            configs_gerais = {k: v for k, v in backup_data.items() if not k.startswith('_') and k not in [
                'dias_uteis', 'bloqueios_individuais', 'bloqueios_periodos', 
                'bloqueios_permanentes', 'bloqueios_semanais', 'bloqueios_horarios'
            ]}
            
            for chave, valor in configs_gerais.items():
                c.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", 
                         (chave, valor))
                restaurados += 1
            
            print(f"✅ {len(configs_gerais)} configurações gerais restauradas")
            
            # 2. RESTAURAR DIAS ÚTEIS
            if 'dias_uteis' in backup_data:
                try:
                    # Limpar dias atuais
                    c.execute("DELETE FROM dias_uteis")
                    
                    # Inserir dias do backup
                    for dia in backup_data['dias_uteis']:
                        c.execute("INSERT INTO dias_uteis (dia) VALUES (?)", (dia,))
                    
                    print(f"✅ {len(backup_data['dias_uteis'])} dias úteis restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar dias úteis: {e}")
            
            # 3. RESTAURAR BLOQUEIOS INDIVIDUAIS
            if 'bloqueios_individuais' in backup_data:
                try:
                    # Limpar bloqueios atuais
                    c.execute("DELETE FROM bloqueios")
                    
                    # Inserir bloqueios do backup
                    for data in backup_data['bloqueios_individuais']:
                        c.execute("INSERT OR IGNORE INTO bloqueios (data) VALUES (?)", (data,))
                    
                    print(f"✅ {len(backup_data['bloqueios_individuais'])} bloqueios individuais restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar bloqueios individuais: {e}")
            
            # 4. RESTAURAR BLOQUEIOS DE PERÍODOS
            if 'bloqueios_periodos' in backup_data:
                try:
                    # Limpar períodos atuais
                    c.execute("DELETE FROM bloqueios_periodos")
                    
                    # Inserir períodos do backup
                    for periodo in backup_data['bloqueios_periodos']:
                        if len(periodo) >= 4:  # id, data_inicio, data_fim, descricao, criado_em
                            c.execute("""INSERT INTO bloqueios_periodos 
                                        (data_inicio, data_fim, descricao, criado_em) 
                                        VALUES (?, ?, ?, ?)""",
                                     (periodo[1], periodo[2], periodo[3], 
                                      periodo[4] if len(periodo) > 4 else datetime.now().isoformat()))
                    
                    print(f"✅ {len(backup_data['bloqueios_periodos'])} períodos restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar períodos: {e}")
            
            # 5. RESTAURAR BLOQUEIOS PERMANENTES
            if 'bloqueios_permanentes' in backup_data:
                try:
                    # Agora é seguro fazer DELETE pois a tabela existe
                    c.execute("DELETE FROM bloqueios_permanentes")
                    
                    for bloqueio in backup_data['bloqueios_permanentes']:
                        if len(bloqueio) >= 4:  # id, horario_inicio, horario_fim, dias_semana, descricao
                            c.execute("""INSERT INTO bloqueios_permanentes 
                                        (horario_inicio, horario_fim, dias_semana, descricao) 
                                        VALUES (?, ?, ?, ?)""",
                                     (bloqueio[1], bloqueio[2], bloqueio[3], 
                                      bloqueio[4] if len(bloqueio) > 4 else ""))
                    
                    print(f"✅ {len(backup_data['bloqueios_permanentes'])} bloqueios permanentes restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar bloqueios permanentes: {e}")
            
            # 6. RESTAURAR BLOQUEIOS SEMANAIS
            if 'bloqueios_semanais' in backup_data:
                try:
                    # Agora é seguro fazer DELETE pois a tabela existe
                    c.execute("DELETE FROM bloqueios_semanais")
                    
                    for bloqueio in backup_data['bloqueios_semanais']:
                        if len(bloqueio) >= 3:  # id, dia_semana, horarios, descricao
                            c.execute("""INSERT INTO bloqueios_semanais 
                                        (dia_semana, horarios, descricao) 
                                        VALUES (?, ?, ?)""",
                                     (bloqueio[1], bloqueio[2], 
                                      bloqueio[3] if len(bloqueio) > 3 else ""))
                    
                    print(f"✅ {len(backup_data['bloqueios_semanais'])} bloqueios semanais restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar bloqueios semanais: {e}")
            
            # 7. RESTAURAR BLOQUEIOS DE HORÁRIOS
            if 'bloqueios_horarios' in backup_data:
                try:
                    c.execute("DELETE FROM bloqueios_horarios")
                    
                    for data, horario in backup_data['bloqueios_horarios']:
                        c.execute("INSERT OR IGNORE INTO bloqueios_horarios (data, horario) VALUES (?, ?)", 
                                 (data, horario))
                    
                    print(f"✅ {len(backup_data['bloqueios_horarios'])} bloqueios de horários restaurados")
                except Exception as e:
                    print(f"⚠️ Erro ao restaurar bloqueios de horários: {e}")
            
            conn.commit()
            
            print(f"🎉 RESTAURAÇÃO COMPLETA FINALIZADA!")
            print(f"📊 Total de itens processados: {restaurados + len(backup_data.get('dias_uteis', []))}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante restauração: {e}")
            return False
        finally:
            conn.close()
            
    except Exception as e:
        print(f"❌ Erro na restauração GitHub: {e}")
        return False

def download_from_github(github_config):
    """Download de arquivo do GitHub"""
    try:
        headers = {
            "Authorization": f"token {github_config['token']}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Sistema-Agendamento"
        }
        
        # URL da API GitHub
        api_url = f"https://api.github.com/repos/{github_config['repo']}/contents/{github_config['config_file']}"
        
        print(f"📥 Baixando backup: {api_url}")
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            # Decodificar conteúdo base64
            content_encoded = response.json()["content"]
            content = base64.b64decode(content_encoded).decode('utf-8')
            print("✅ Backup baixado com sucesso")
            return content
        elif response.status_code == 404:
            print("📄 Arquivo de backup não encontrado no GitHub")
            return None
        else:
            print(f"❌ Erro no download GitHub: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro no download GitHub: {e}")
        return None

def backup_agendamentos_futuros_github():
    """Usa o CSV que já funciona e envia para GitHub"""
    try:
        print("🔍 Iniciando backup de agendamentos...")
        
        # 1. Gerar CSV usando função que JÁ FUNCIONA
        csv_data = exportar_agendamentos_csv()
        
        if not csv_data:
            print("📝 Lista vazia - enviando backup de limpeza")
            csv_data = "ID,Data,Horário,Nome,Telefone,Email,Status\n"  # CSV vazio com cabeçalho
        
        print("✅ CSV gerado com sucesso")
        
        # 2. Configurar GitHub para arquivo CSV
        github_config = get_github_config()
        if not github_config or not github_config.get("token"):
            print("❌ GitHub não configurado")
            return False
        
        github_config['config_file'] = 'agendamentos_backup.csv'
        
        # 3. Enviar para GitHub
        print("📤 Enviando para GitHub...")
        sucesso = upload_to_github(csv_data, github_config)
        
        if sucesso:
            print("✅ Backup enviado com sucesso!")
            return True
        else:
            print("❌ Erro ao enviar para GitHub")
            return False
            
    except Exception as e:
        print(f"❌ Erro no backup: {e}")
        return False

def baixar_agendamentos_github():
    """Baixa arquivo de agendamentos do GitHub"""
    try:
        github_config = get_github_config()
        if not github_config or not github_config.get("token"):
            print("❌ GitHub não configurado para recuperação")
            return None
        
        # Configurar para buscar arquivo CSV
        github_config['config_file'] = 'agendamentos_backup.csv'
        
        # Baixar do GitHub
        print("📥 Baixando agendamentos do GitHub...")
        csv_data = download_from_github(github_config)
        
        if csv_data:
            print("✅ Arquivo baixado com sucesso!")
            return csv_data
        else:
            print("📄 Nenhum backup encontrado no GitHub")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        return None

def recuperar_agendamentos_automatico():
    """Recupera agendamentos do GitHub automaticamente - VERSÃO SEGURA"""
    try:
        print("🔄 Nova sessão detectada - verificando backup do GitHub...")
        
        # PASSO 1: Tentar baixar do GitHub (SEM limpar banco ainda)
        print("📥 Tentando baixar backup do GitHub...")
        csv_data = baixar_agendamentos_github()
        
        # PASSO 2: Verificar se conseguiu baixar
        if not csv_data:
            print("📄 GitHub indisponível ou nenhum backup encontrado")
            print("✅ Mantendo dados locais existentes (modo offline)")
            return True  # Não faz nada, preserva dados atuais
        
        print("📋 Backup baixado com sucesso do GitHub!")
        print(f"📊 Tamanho do arquivo: {len(csv_data)} caracteres")
        
        # PASSO 3: SÓ AGORA limpar banco (pois tem dados seguros na memória)
        print("🗑️ Dados do GitHub OK - limpando banco local para sincronização...")
        conn = conectar()
        c = conn.cursor()
        c.execute("DELETE FROM agendamentos")
        conn.commit()
        conn.close()
        print("✅ Banco local limpo!")
        
        # PASSO 4: Importar dados da memória para o banco
        print("📋 Importando agendamentos atualizados do backup...")
        resultado = importar_agendamentos_csv(csv_data)
        
        if resultado['sucesso']:
            print(f"✅ Sincronização completa!")
            print(f"📊 {resultado['importados']} agendamento(s) restaurado(s)")
            if resultado['duplicados'] > 0:
                print(f"⚠️ {resultado['duplicados']} registro(s) duplicado(s) ignorado(s)")
            if resultado['erros'] > 0:
                print(f"❌ {resultado['erros']} registro(s) com erro")
            return True
        else:
            print(f"❌ Erro na importação: {resultado.get('erro', 'Erro desconhecido')}")
            print("⚠️ Dados do GitHub baixados mas falha na importação")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout ao conectar com GitHub - mantendo dados locais")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Sem conexão com GitHub - mantendo dados locais") 
        return True
    except Exception as e:
        print(f"❌ Erro na recuperação automática: {e}")
        print("✅ Mantendo dados locais por segurança")
        return True  # Em caso de qualquer erro, preserva dados atuais


# ========================================
# FUNÇÕES PARA BACKUP POR EMAIL - PASSO 1
# ========================================

def calcular_hash_agendamentos():
    """Calcula hash dos agendamentos para detectar mudanças"""
    try:
        agendamentos = buscar_agendamentos()
        # Converter para string ordenada para hash consistente
        dados_str = str(sorted(agendamentos))
        return hashlib.md5(dados_str.encode()).hexdigest()
    except:
        return ""

def agendamentos_mudaram():
    """Verifica se houve mudanças desde último backup"""
    hash_atual = calcular_hash_agendamentos()
    hash_anterior = obter_configuracao("ultimo_backup_hash", "")
    
    if hash_atual != hash_anterior:
        # Salvar novo hash
        salvar_configuracao("ultimo_backup_hash", hash_atual)
        return True
    return False

def enviar_backup_email_agendamentos(forcar_envio=False):
    """Envia backup dos agendamentos por email"""
    
    # Verificar se backup automático está ativo
    backup_automatico_ativo = obter_configuracao("backup_email_ativo", False)
    if not backup_automatico_ativo and not forcar_envio:
        print("📧 Backup automático por email desativado")
        return False
    
    # Verificar se há mudanças (se não for forçado)
    if not forcar_envio and not agendamentos_mudaram():
        print("📊 Sem mudanças desde último backup - não enviando")
        return False
    
    try:
        # Obter configurações de email
        email_sistema = obter_configuracao("email_sistema", "")
        senha_email = obter_configuracao("senha_email", "")
        servidor_smtp = obter_configuracao("servidor_smtp", "smtp.gmail.com")
        porta_smtp = obter_configuracao("porta_smtp", 587)
        
        # Email de destino para backup
        email_backup = obter_configuracao("email_backup_destino", email_sistema)
        
        if not email_sistema or not senha_email or not email_backup:
            print("❌ Configurações de email incompletas para backup")
            return False
        
        # Gerar CSV dos agendamentos
        csv_data = exportar_agendamentos_csv()
        if not csv_data:
            print("❌ Nenhum agendamento para fazer backup")
            return False
        
        # Estatísticas para o email
        agendamentos = buscar_agendamentos()
        total_agendamentos = len(agendamentos)
        
        # Contar por status
        pendentes = len([a for a in agendamentos if len(a) > 6 and a[6] == "pendente"])
        confirmados = len([a for a in agendamentos if len(a) > 6 and a[6] == "confirmado"])
        atendidos = len([a for a in agendamentos if len(a) > 6 and a[6] == "atendido"])
        cancelados = len([a for a in agendamentos if len(a) > 6 and a[6] == "cancelado"])
        
        # Data/hora atual
        agora = datetime.now()
        data_formatada = agora.strftime("%d/%m/%Y às %H:%M")
        
        # Nome do arquivo
        nome_arquivo = f"agendamentos_backup_{agora.strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Dados do profissional/clínica
        nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
        nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
        
        # Criar email
        msg = MIMEMultipart()
        msg['From'] = email_sistema
        msg['To'] = email_backup
        msg['Subject'] = f"📊 Backup Agendamentos - {nome_clinica} - {agora.strftime('%d/%m/%Y')}"
        
        # Corpo do email
        corpo = f"""
📋 Backup Automático de Agendamentos

🏥 {nome_clinica}
👨‍⚕️ {nome_profissional}

📅 Data/Hora do Backup: {data_formatada}
📊 Total de Agendamentos: {total_agendamentos}

📈 Estatísticas por Status:
⏳ Pendentes: {pendentes}
✅ Confirmados: {confirmados}
🎉 Atendidos: {atendidos}
❌ Cancelados: {cancelados}

📎 Arquivo em Anexo: {nome_arquivo}
💾 Tamanho: {len(csv_data.encode('utf-8')) / 1024:.1f} KB

🤖 Mensagem automática do Sistema de Agendamento
"""
        
        # Anexar corpo do email
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        
        # Anexar arquivo CSV
        from email.mime.application import MIMEApplication
        anexo = MIMEApplication(csv_data.encode('utf-8'), _subtype="csv")
        anexo.add_header('Content-Disposition', 'attachment', filename=nome_arquivo)
        msg.attach(anexo)
        
        # Enviar email
        server = smtplib.SMTP(servidor_smtp, porta_smtp)
        server.starttls()
        server.login(email_sistema, senha_email)
        server.send_message(msg)
        server.quit()
        
        # Salvar data do último backup
        salvar_configuracao("ultimo_backup_email_data", agora.isoformat())
        
        print(f"✅ Backup enviado por email para {email_backup}")
        print(f"📊 {total_agendamentos} agendamentos incluídos no backup")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar backup por email: {e}")
        return False

def interface_backup_email():
    """Interface para configurar backup automático por email"""
    
    st.subheader("📧 Backup Automático por Email")
    
    # Status atual
    backup_ativo = obter_configuracao("backup_email_ativo", False)
    
    if backup_ativo:
        st.success("✅ Backup automático por email ATIVADO")
        
        # Mostrar configurações atuais
        frequencia = obter_configuracao("backup_email_frequencia", "semanal")
        horario = obter_configuracao("backup_email_horario", "08:00")
        email_destino = obter_configuracao("email_backup_destino", "")
        
        st.info(f"""
**📋 Configurações Atuais:**
• **Frequência:** {frequencia.title()}
• **Horário:** {horario}
• **Email de destino:** {email_destino}
        """)
        
        # Mostrar último backup
        ultimo_backup_str = obter_configuracao("ultimo_backup_email_data", "")
        if ultimo_backup_str:
            try:
                ultimo_backup = datetime.fromisoformat(ultimo_backup_str)
                ultimo_formatado = ultimo_backup.strftime("%d/%m/%Y às %H:%M")
                st.info(f"📅 **Último backup enviado:** {ultimo_formatado}")
            except:
                pass
    else:
        st.warning("⚠️ Backup automático por email DESATIVADO")
    
    # Configurações
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**⚙️ Configurações do Backup**")
        
        # Ativar/desativar
        backup_email_ativo = st.checkbox(
            "Ativar backup automático por email",
            value=backup_ativo,
            help="Envia backup dos agendamentos automaticamente por email"
        )
        
        # Frequência
        frequencia_backup = st.selectbox(
            "Frequência do backup:",
            ["diario", "semanal", "mensal"],
            index=["diario", "semanal", "mensal"].index(obter_configuracao("backup_email_frequencia", "semanal")),
            format_func=lambda x: {"diario": "Diário", "semanal": "Semanal", "mensal": "Mensal"}[x],
            help="Com que frequência enviar o backup"
        )
        
        # Horário
        try:
            horario_atual = datetime.strptime(obter_configuracao("backup_email_horario", "08:00"), "%H:%M").time()
        except:
            horario_atual = datetime.strptime("08:00", "%H:%M").time()
        
        horario_backup = st.time_input(
            "Horário do backup:",
            value=horario_atual,
            help="Horário para enviar o backup automaticamente"
        )
        
        # Email de destino
        email_backup_destino = st.text_input(
            "Email de destino:",
            value=obter_configuracao("email_backup_destino", obter_configuracao("email_sistema", "")),
            placeholder="backup@clinica.com",
            help="Email que receberá os backups automáticos"
        )
    
    with col2:
        st.markdown("**🧪 Teste e Backup Manual**")
        
        # Backup manual
        if st.button("📤 Enviar Backup Agora", type="secondary", help="Enviar backup manual independente das configurações"):
            with st.spinner("Gerando e enviando backup..."):
                sucesso = enviar_backup_email_agendamentos(forcar_envio=True)
                if sucesso:
                    st.success("✅ Backup enviado com sucesso!")
                else:
                    st.error("❌ Erro ao enviar backup. Verifique as configurações de email.")
        
        # Verificar mudanças
        if st.button("🔍 Verificar Mudanças", help="Verificar se há mudanças desde último backup"):
            if agendamentos_mudaram():
                st.info("📊 Há mudanças nos agendamentos desde último backup")
            else:
                st.success("✅ Nenhuma mudança desde último backup")
        
        # Informações
        st.markdown("**ℹ️ Como Funciona:**")
        st.info("""
• **Automático:** Verifica mudanças e envia apenas se necessário
• **Inteligente:** Não envia spam se não houver alterações  
• **Seguro:** Anexa CSV com todos os agendamentos
• **Informativo:** Email com estatísticas detalhadas
        """)
    
    # Botão para salvar configurações
    if st.button("💾 Salvar Configurações de Backup", type="primary", use_container_width=True):
        salvar_configuracao("backup_email_ativo", backup_email_ativo)
        salvar_configuracao("backup_email_frequencia", frequencia_backup)
        salvar_configuracao("backup_email_horario", horario_backup.strftime("%H:%M"))
        salvar_configuracao("email_backup_destino", email_backup_destino)
        
        st.success("✅ Configurações de backup salvas!")
        
        if backup_email_ativo:
            st.info(f"""
🎯 **Backup configurado:**
• **Frequência:** {frequencia_backup.title()}
• **Horário:** {horario_backup.strftime('%H:%M')}  
• **Email:** {email_backup_destino}

📧 Próximo backup será enviado automaticamente se houver mudanças!
            """)
        else:
            st.warning("⚠️ Backup automático foi desativado")
        
        st.rerun()

def verificar_hora_backup():
    """Verifica se chegou a hora do backup automático"""
    try:
        backup_ativo = obter_configuracao("backup_email_ativo", False)
        if not backup_ativo:
            return False
        
        # Configurações de agendamento
        frequencia = obter_configuracao("backup_email_frequencia", "semanal")
        horario = obter_configuracao("backup_email_horario", "08:00")
        
        agora = datetime.now()
        hora_backup = datetime.strptime(horario, "%H:%M").time()
        
        # Verificar se é a hora do backup (com tolerância de 1 minuto)
        if abs((agora.time().hour * 60 + agora.time().minute) - 
               (hora_backup.hour * 60 + hora_backup.minute)) > 1:
            return False
        
        # Verificar frequência
        ultimo_backup_str = obter_configuracao("ultimo_backup_email_data", "")
        
        if not ultimo_backup_str:
            return True  # Primeiro backup
        
        try:
            ultimo_backup = datetime.fromisoformat(ultimo_backup_str)
        except:
            return True  # Se der erro, fazer backup
        
        if frequencia == "diario":
            return (agora - ultimo_backup).days >= 1
        elif frequencia == "semanal":
            return (agora - ultimo_backup).days >= 7
        elif frequencia == "mensal":
            return (agora - ultimo_backup).days >= 30
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao verificar hora do backup: {e}")
        return False

def iniciar_monitoramento_backup():
    """Inicia thread para monitoramento automático de backup"""
    def monitorar():
        print("🔄 Monitoramento de backup automático iniciado")
        while True:
            try:
                if verificar_hora_backup():
                    print("⏰ Hora do backup automático!")
                    sucesso = enviar_backup_email_agendamentos()
                    if sucesso:
                        print("✅ Backup automático enviado com sucesso!")
                    else:
                        print("❌ Falha no backup automático")
                
                # Verificar a cada minuto
                time.sleep(60)
                
            except Exception as e:
                print(f"❌ Erro no monitoramento de backup: {e}")
                time.sleep(300)  # Esperar 5 minutos se der erro
    
    # Iniciar thread em background
    thread = threading.Thread(target=monitorar, daemon=True)
    thread.start()

# ========================================
# FUNÇÕES NOVAS PARA BLOQUEIOS DE PERÍODO
# ========================================

def init_config_periodos():
    """Adiciona tabela de bloqueios de período ao banco"""
    conn = conectar()
    c = conn.cursor()
    
    # Criar tabela para bloqueios de período
    c.execute('''
        CREATE TABLE IF NOT EXISTS bloqueios_periodos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_inicio TEXT,
            data_fim TEXT,
            descricao TEXT,
            criado_em TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def adicionar_bloqueio_periodo(data_inicio, data_fim, descricao=""):
    """Adiciona um bloqueio de período (ex: férias, viagem)"""
    conn = conectar()
    c = conn.cursor()
    
    try:
        # Salvar o período na nova tabela
        from datetime import datetime
        criado_em = datetime.now().isoformat()
        
        c.execute("""INSERT INTO bloqueios_periodos 
                    (data_inicio, data_fim, descricao, criado_em) 
                    VALUES (?, ?, ?, ?)""", 
                 (data_inicio, data_fim, descricao, criado_em))
        
        periodo_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return periodo_id
        
    except Exception as e:
        conn.close()
        print(f"Erro ao adicionar período: {e}")
        return False

def obter_bloqueios_periodos():
    """Obtém todos os bloqueios de período"""
    conn = conectar()
    c = conn.cursor()
    
    try:
        c.execute("""SELECT id, data_inicio, data_fim, descricao, criado_em 
                    FROM bloqueios_periodos 
                    ORDER BY data_inicio""")
        periodos = c.fetchall()
        return periodos
    except:
        return []
    finally:
        conn.close()

def remover_bloqueio_periodo(periodo_id):
    """Remove um bloqueio de período"""
    conn = conectar()
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM bloqueios_periodos WHERE id=?", (periodo_id,))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def data_em_periodo_bloqueado(data):
    """Verifica se uma data está em algum período bloqueado"""
    conn = conectar()
    c = conn.cursor()
    
    try:
        c.execute("""SELECT COUNT(*) FROM bloqueios_periodos 
                    WHERE ? BETWEEN data_inicio AND data_fim""", (data,))
        
        resultado = c.fetchone()[0] > 0
        conn.close()
        return resultado
    except:
        conn.close()
        return False

def gerar_codigo_verificacao():
    """Gera código de verificação de 4 dígitos"""
    return str(random.randint(1000, 9999))

def salvar_codigo_verificacao(email, codigo):
    """Salva código de verificação temporário"""
    conn = conectar()
    c = conn.cursor()
    
    # Criar tabela se não existir
    c.execute('''
        CREATE TABLE IF NOT EXISTS codigos_verificacao (
            email TEXT PRIMARY KEY,
            codigo TEXT,
            criado_em TIMESTAMP,
            tentativas INTEGER DEFAULT 0
        )
    ''')
    
    # Limpar códigos antigos (mais de 30 minutos)
    from datetime import datetime, timedelta
    limite = (datetime.now() - timedelta(minutes=30)).isoformat()
    c.execute("DELETE FROM codigos_verificacao WHERE criado_em < ?", (limite,))
    
    # Salvar novo código
    c.execute("""INSERT OR REPLACE INTO codigos_verificacao 
                 (email, codigo, criado_em) VALUES (?, ?, ?)""",
              (email, codigo, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def verificar_codigo(email, codigo_informado):
    """Verifica se o código está correto"""
    conn = conectar()
    c = conn.cursor()
    
    try:
        # Buscar código
        c.execute("""SELECT codigo, tentativas, criado_em 
                    FROM codigos_verificacao WHERE email = ?""", (email,))
        resultado = c.fetchone()
        
        if not resultado:
            conn.close()
            return False, "Código não encontrado. Solicite um novo código."
        
        codigo_salvo, tentativas, criado_em = resultado
        
        # Verificar se não expirou (30 minutos)
        criado_dt = datetime.fromisoformat(criado_em)
        if (datetime.now() - criado_dt).seconds > 1800:  # 30 minutos
            c.execute("DELETE FROM codigos_verificacao WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return False, "Código expirado. Solicite um novo código."
        
        # Verificar tentativas (máximo 5)
        if tentativas >= 5:
            c.execute("DELETE FROM codigos_verificacao WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return False, "Muitas tentativas. Solicite um novo código."
        
        # Verificar código
        if codigo_informado == codigo_salvo:
            # Código correto - deletar da tabela
            c.execute("DELETE FROM codigos_verificacao WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return True, "Código verificado com sucesso!"
        else:
            # Código incorreto - incrementar tentativas
            c.execute("""UPDATE codigos_verificacao 
                        SET tentativas = tentativas + 1 
                        WHERE email = ?""", (email,))
            conn.commit()
            tentativas_restantes = 4 - tentativas
            conn.close()
            return False, f"Código incorreto. {tentativas_restantes} tentativas restantes."
            
    except Exception as e:
        conn.close()
        return False, f"Erro ao verificar código: {str(e)}"

def enviar_codigo_verificacao(email, nome, codigo):
    """Envia código de verificação por email"""
    try:
        # Obter configurações
        email_sistema = obter_configuracao("email_sistema", "")
        senha_email = obter_configuracao("senha_email", "")
        servidor_smtp = obter_configuracao("servidor_smtp", "smtp.gmail.com")
        porta_smtp = obter_configuracao("porta_smtp", 587)
        nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
        nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
        
        if not email_sistema or not senha_email:
            return False
        
        # Criar email
        msg = MIMEMultipart()
        msg['From'] = email_sistema
        msg['To'] = email
        msg['Subject'] = f"🔐 Código de Verificação - {nome_clinica}"
        
        corpo = f"""
Olá {nome}!

Seu código de verificação para agendamento é:

🔐 **{codigo}**

Este código é válido por 30 minutos.

⚠️ Não compartilhe este código com ninguém.

Se você não solicitou este código, ignore este email.

Atenciosamente,
{nome_profissional}
{nome_clinica}
"""
        
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        
        # Enviar
        server = smtplib.SMTP(servidor_smtp, porta_smtp)
        server.starttls()
        server.login(email_sistema, senha_email)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Erro ao enviar código: {e}")
        return False

def obter_client_todoist():
    """Obtém configurações do Todoist"""
    try:
        todoist_ativo = obter_configuracao("todoist_ativo", False)
        if not todoist_ativo:
            return None
            
        api_token = obter_configuracao("todoist_token", "")
        
        if not api_token:
            print("❌ Token Todoist não configurado")
            return None
        
        return api_token
        
    except Exception as e:
        print(f"❌ Erro ao obter token Todoist: {e}")
        return None

def testar_conexao_todoist():
    """Testa a conexão com Todoist"""
    try:
        token = obter_client_todoist()
        if not token:
            return False, "Token não configurado"
        
        # Testar API com endpoint simples
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.todoist.com/rest/v2/projects",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            projetos = response.json()
            return True, f"✅ Conectado! {len(projetos)} projeto(s) encontrado(s)"
        elif response.status_code == 401:
            return False, "❌ Token inválido ou expirado"
        else:
            return False, f"❌ Erro na API: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "❌ Timeout - verifique sua conexão"
    except Exception as e:
        return False, f"❌ Erro: {str(e)}"

def obter_projeto_agendamentos():
    """Obtém ou cria UM ÚNICO projeto 'Agendamentos' no Todoist"""
    try:
        token = obter_client_todoist()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Obter nome configurado do projeto (ou usar padrão)
        nome_projeto = obter_configuracao("todoist_nome_projeto", "📅 Agendamentos")
        
        # Buscar projetos existentes
        response = requests.get(
            "https://api.todoist.com/rest/v2/projects",
            headers=headers
        )
        
        if response.status_code == 200:
            projetos = response.json()
            
            # 1. PRIMEIRO: Procurar pelo nome configurado exato
            for projeto in projetos:
                if projeto['name'] == nome_projeto:
                    print(f"✅ Projeto encontrado: {nome_projeto} (ID: {projeto['id']})")
                    # Salvar ID para não precisar buscar sempre
                    salvar_configuracao("todoist_projeto_id", projeto['id'])
                    return projeto['id']
            
            # 2. SEGUNDO: Procurar por nomes similares (compatibilidade)
            nomes_similares = ['📅 Agendamentos', 'Agendamentos', 'Agenda', 'Clientes']
            for projeto in projetos:
                if projeto['name'] in nomes_similares:
                    print(f"✅ Projeto similar encontrado: {projeto['name']} (ID: {projeto['id']})")
                    # Atualizar nome nas configurações para usar o existente
                    salvar_configuracao("todoist_nome_projeto", projeto['name'])
                    salvar_configuracao("todoist_projeto_id", projeto['id'])
                    return projeto['id']
            
            # 3. TERCEIRO: Se não encontrou, criar novo projeto
            novo_projeto = {
                "name": nome_projeto,
                "color": "blue",
                "comment_count": 0
            }
            
            response = requests.post(
                "https://api.todoist.com/rest/v2/projects",
                headers=headers,
                json=novo_projeto
            )
            
            if response.status_code == 200:
                projeto_criado = response.json()
                projeto_id = projeto_criado['id']
                
                print(f"✅ Novo projeto criado: {nome_projeto} (ID: {projeto_id})")
                
                # Salvar configurações
                salvar_configuracao("todoist_projeto_id", projeto_id)
                salvar_configuracao("todoist_nome_projeto", nome_projeto)
                
                return projeto_id
            else:
                print(f"❌ Erro ao criar projeto: {response.status_code} - {response.text}")
        
        return None
        
    except Exception as e:
        print(f"❌ Erro ao obter projeto: {e}")
        return None

def criar_tarefa_todoist(agendamento_id, nome_cliente, telefone, email_cliente, data, horario):
    """Cria tarefa no Todoist para o agendamento"""
    try:
        token = obter_client_todoist()
        if not token:
            print("⚠️ Todoist não configurado")
            return False
        
        projeto_id = obter_projeto_agendamentos()
        if not projeto_id:
            print("❌ Erro ao obter projeto Agendamentos")
            return False
        
        # Obter configurações do profissional
        nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
        nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
        
        # Preparar dados da tarefa
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        horario_obj = datetime.strptime(horario, "%H:%M").time()
        
        # Combinar data e horário
        data_hora = datetime.combine(data_obj.date(), horario_obj)
        
        # Título da tarefa
        titulo = f"📅 {nome_cliente} - {horario}"
        
        # Descrição com detalhes
        descricao = f"""
**Agendamento - {nome_clinica}**

👤 **Cliente:** {nome_cliente}
📞 **Telefone:** {telefone}
📧 **Email:** {email_cliente}
👨‍⚕️ **Profissional:** {nome_profissional}

🆔 **ID Sistema:** {agendamento_id}
"""
        
        # Dados da tarefa
        tarefa_data = {
            "content": titulo,
            "description": descricao.strip(),
            "project_id": projeto_id,
            "due_datetime": data_hora.strftime("%Y-%m-%dT%H:%M:00"),
            "labels": ["agendamento"],
            "priority": 2  # Prioridade normal
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Criar tarefa
        response = requests.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers=headers,
            json=tarefa_data
        )
        
        if response.status_code == 200:
            tarefa_criada = response.json()
            tarefa_id = tarefa_criada['id']
            
            # Salvar referência no banco para poder deletar depois
            salvar_configuracao(f"todoist_task_{agendamento_id}", tarefa_id)
            
            print(f"✅ Tarefa Todoist criada: {nome_cliente} - {data} {horario}")
            return True
        else:
            print(f"❌ Erro ao criar tarefa Todoist: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao criar tarefa Todoist: {e}")
        return False

def atualizar_tarefa_todoist(agendamento_id, nome_cliente, novo_status):
    """Atualiza tarefa no Todoist baseado no status"""
    try:
        token = obter_client_todoist()
        if not token:
            return False
        
        # Buscar ID da tarefa
        tarefa_id = obter_configuracao(f"todoist_task_{agendamento_id}", "")
        if not tarefa_id:
            print(f"⚠️ Tarefa Todoist não encontrada para ID {agendamento_id}")
            return False
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if novo_status == 'atendido':
            # Marcar como concluída
            response = requests.post(
                f"https://api.todoist.com/rest/v2/tasks/{tarefa_id}/close",
                headers=headers
            )
            
            if response.status_code == 204:
                print(f"✅ Tarefa Todoist marcada como concluída: {nome_cliente}")
                return True
            else:
                print(f"❌ Erro ao marcar tarefa como concluída: {response.status_code}")
                return False
        
        elif novo_status == 'cancelado':
            # Buscar dados do agendamento para deletar tarefa
            try:
                conn = conectar()
                c = conn.cursor()
                c.execute("SELECT data, horario FROM agendamentos WHERE id = ?", (agendamento_id,))
                resultado = c.fetchone()
                conn.close()
                
                if resultado:
                    data, horario = resultado
                    return deletar_tarefa_todoist(data, nome_cliente)
                else:
                    print(f"⚠️ Agendamento {agendamento_id} não encontrado para deletar tarefa")
                    return False
            except Exception as e:
                print(f"❌ Erro ao buscar dados do agendamento: {e}")
                return False
        
        elif novo_status == 'confirmado':
            # Adicionar label "confirmado"
            # Buscar dados atuais da tarefa
            response = requests.get(
                f"https://api.todoist.com/rest/v2/tasks/{tarefa_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                tarefa_atual = response.json()
                labels_atuais = tarefa_atual.get('labels', [])
                
                if 'confirmado' not in labels_atuais:
                    labels_atuais.append('confirmado')
                    
                    # Atualizar tarefa
                    update_data = {
                        "labels": labels_atuais
                    }
                    
                    response = requests.post(
                        f"https://api.todoist.com/rest/v2/tasks/{tarefa_id}",
                        headers=headers,
                        json=update_data
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Tarefa Todoist atualizada para confirmado: {nome_cliente}")
                        return True
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar tarefa Todoist: {e}")
        return False

def deletar_tarefa_todoist(data, nome_cliente):
    """Deleta tarefa do Todoist"""
    try:
        token = obter_client_todoist()
        if not token:
            return False
        
        # Buscar ID da tarefa
        tarefa_id = buscar_tarefa_todoist_por_data_hora(data, nome_cliente)
        if not tarefa_id:
            print(f"⚠️ Tarefa Todoist não encontrada para deletar ID {agendamento_id}")
            return True  # Considera sucesso se não existe
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Deletar tarefa
        response = requests.delete(
            f"https://api.todoist.com/rest/v2/tasks/{tarefa_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            # Remover referência do banco
            conn = conectar()
            c = conn.cursor()
            c.execute("DELETE FROM configuracoes WHERE chave = ?", (f"todoist_task_{agendamento_id}",))
            conn.commit()
            conn.close()
            
            print(f"✅ Tarefa Todoist deletada: ID {agendamento_id}")
            return True
        else:
            print(f"⚠️ Erro ao deletar tarefa Todoist: {response.status_code}")
            return True  # Considera sucesso para não travar o sistema
        
    except Exception as e:
        print(f"❌ Erro ao deletar tarefa Todoist: {e}")
        return False

def gerar_instrucoes_todoist():
    """Gera instruções para obter token do Todoist"""
    return """
🎯 **Como obter seu Token do Todoist:**

1. **Acesse:** https://todoist.com/app/settings/integrations
2. **Faça login** na sua conta Todoist
3. **Role até** "API token"
4. **Copie** o token (40 caracteres)
5. **Cole** no campo abaixo

⚠️ **Importante:**
• **Mantenha** o token seguro (não compartilhe)
• **Se vazar**, gere um novo nas configurações
• **Funciona** com conta gratuita ou premium

✨ **O que acontece:**
• **Cria projeto** "📅 Agendamentos" automaticamente
• **Cada agendamento** vira uma tarefa
• **Notificações** no seu celular/desktop
• **Marca como concluído** quando atendido
"""
 
def buscar_tarefa_todoist_por_data_hora(data, nome_cliente):
    """Busca tarefa no Todoist por data/hora ao invés de ID"""
    try:
        token = obter_client_todoist()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Buscar todas as tarefas do projeto
        projeto_id = obter_projeto_agendamentos()
        if not projeto_id:
            return None
            
        # Listar tarefas do projeto
        response = requests.get(
            f"https://api.todoist.com/rest/v2/tasks?project_id={projeto_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            tarefas = response.json()
            
            # Procurar pela tarefa que contém nome + horário
            for tarefa in tarefas:
                if nome_cliente in tarefa['content']:
                    print(f"✅ Tarefa encontrada: {tarefa['content']} (ID: {tarefa['id']})")
                    return tarefa['id']
            
            print(f"⚠️ Tarefa não encontrada: {nome_cliente} - {data} {horario}")
            return None
        else:
            print(f"❌ Erro ao buscar tarefas: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar tarefa: {e}")
        return None 
    
# Inicializar banco
init_config()

# Inicializar monitoramento de backup automático
#iniciar_monitoramento_backup()

# Inicializar tabela de períodos
init_config_periodos()

# Recuperação por sessão - só uma vez por acesso
if 'agendamentos_recuperados' not in st.session_state:
    try:
        print("🔄 Primeira vez nesta sessão - verificando backup do GitHub...")
        recuperar_agendamentos_automatico()
        st.session_state.agendamentos_recuperados = True
        print("✅ Verificação de backup concluída!")
    except Exception as e:
        print(f"⚠️ Erro na recuperação automática: {e}")
        st.session_state.agendamentos_recuperados = True  # Marca como tentado para não repetir
else:
    print("✅ Backup já verificado nesta sessão - pulando recuperação")

# Inicializar controle de restauração
if 'dados_restaurados' not in st.session_state:
    st.session_state.dados_restaurados = False

# Restaurar configurações do GitHub (apenas uma vez por sessão)
if not st.session_state.dados_restaurados:
    print("🔄 Primeira execução - restaurando dados do GitHub...")
    restaurar_configuracoes_github()
    st.session_state.dados_restaurados = True
    print("✅ Dados restaurados! Próximos st.rerun() não acessarão GitHub.")
else:
    print("✅ Dados já restaurados nesta sessão - pulando GitHub.")

# INTERFACE PRINCIPAL
if is_admin:
    
    # Dentro de alguma seção do admin, adicione:
       
    # PAINEL ADMINISTRATIVO
    st.markdown("""
    <div class="admin-header">
        <h1>🔐 Painel Administrativo</h1>
        <div class="badge">Sistema de Agendamento</div>
    </div>
    """, unsafe_allow_html=True)
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        
        st.subheader("🔒 Acesso Restrito")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha = st.text_input("Digite a senha de administrador:", type="password")
            
            if st.button("🚪 Entrar", type="primary", use_container_width=True):
                if senha == SENHA_CORRETA:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        
        # Estatísticas
        agendamentos = buscar_agendamentos()
        bloqueios = obter_bloqueios()
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        agendamentos_hoje = [a for a in agendamentos if a[1] == hoje]
        agendamentos_mes = [a for a in agendamentos if a[1].startswith(datetime.now().strftime("%Y-%m"))]
        

        # Conteúdo baseado na opção
                # Interface administrativa autenticada com menu horizontal
        opcao = criar_menu_horizontal()
        
        # Conteúdo baseado na opção
        if opcao == "⚙️ Configurações Gerais":


            
            # Tabs para organizar as configurações
            tab1, tab2, tab3 = st.tabs(["📅 Agendamento", "📞 Contato & Local", "📧 Email & Notificações"])
            
            with tab1:
                st.subheader("📅 Configurações de Agendamento")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📆 Período de Agendamento**")
                    
                    # Dias futuros disponíveis
                    dias_futuros = st.slider(
                        "Quantos dias no futuro a agenda ficará aberta:",
                        min_value=7,
                        max_value=120,
                        value=obter_configuracao("dias_futuros", 30),
                        step=1,
                        help="Defina até quantos dias no futuro os clientes podem agendar"
                    )
                    
                    # Antecedência mínima
                    antecedencia_atual = obter_configuracao("antecedencia_minima", 2)
                    antecedencia_opcoes = {
                        "30 minutos": 0.5,
                        "1 hora": 1,
                        "2 horas": 2,
                        "4 horas": 4,
                        "6 horas": 6,
                        "12 horas": 12,
                        "24 horas": 24,
                        "48 horas": 48
                    }
                    
                    antecedencia_texto = "2 horas"
                    for texto, horas in antecedencia_opcoes.items():
                        if horas == antecedencia_atual:
                            antecedencia_texto = texto
                            break
                    
                    antecedencia_selecionada = st.selectbox(
                        "Antecedência mínima para agendamento:",
                        list(antecedencia_opcoes.keys()),
                        index=list(antecedencia_opcoes.keys()).index(antecedencia_texto),
                        help="Tempo mínimo necessário entre o agendamento e 00:00 da data da  consulta"
                    )
                
                with col2:
                    st.markdown("**🕐 Horários de Funcionamento**")
                    
                    # Horário de início
                    try:
                        time_inicio = datetime.strptime(obter_configuracao("horario_inicio", "09:00"), "%H:%M").time()
                    except:
                        time_inicio = datetime.strptime("09:00", "%H:%M").time()
                    
                    horario_inicio = st.time_input(
                        "Horário de início:",
                        value=time_inicio,
                        help="Primeiro horário disponível para agendamento"
                    )
                    
                    # Horário de fim
                    try:
                        time_fim = datetime.strptime(obter_configuracao("horario_fim", "18:00"), "%H:%M").time()
                    except:
                        time_fim = datetime.strptime("18:00", "%H:%M").time()
                    
                    horario_fim = st.time_input(
                        "Horário de término:",
                        value=time_fim,
                        help="Último horário disponível para agendamento"
                    )
                    
                    # Intervalo entre consultas
                    intervalo_atual = obter_configuracao("intervalo_consultas", 60)
                    intervalo_opcoes = {
                        "15 minutos": 15,
                        "30 minutos": 30,
                        "45 minutos": 45,
                        "1 hora": 60,
                        "1h 15min": 75,
                        "1h 30min": 90,
                        "2 horas": 120,
                        "2h 30min": 150,
                        "3 horas": 180
                    }
                    
                    intervalo_texto = "1 hora"
                    for texto, minutos in intervalo_opcoes.items():
                        if minutos == intervalo_atual:
                            intervalo_texto = texto
                            break
                    
                    intervalo_selecionado = st.selectbox(
                        "Duração de cada agendamento:",
                        list(intervalo_opcoes.keys()),
                        index=list(intervalo_opcoes.keys()).index(intervalo_texto),
                        help="Tempo padrão reservado para cada agendamento"
                    )
                
                # Configurações de confirmação
                st.markdown("---")
                st.markdown("**🔄 Modo de Confirmação**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    confirmacao_automatica = st.checkbox(
                        "Confirmação automática de agendamentos",
                        value=obter_configuracao("confirmacao_automatica", False),
                        help="Se ativado, agendamentos são confirmados automaticamente sem necessidade de aprovação manual"
                    )
                
                with col2:
                    if not confirmacao_automatica:
                        st.info("💡 **Modo Manual:** Você precisará confirmar cada agendamento manualmente na aba 'Lista de Agendamentos'")
                    else:
                        st.success("✅ **Modo Automático:** Agendamentos são confirmados instantaneamente")
                
            
            with tab2:
                st.subheader("📞 Informações de Contato e Local")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**👨‍⚕️ Informações Profissionais**")
                    
                    nome_profissional = st.text_input(
                        "Nome do profissional:",
                        value=obter_configuracao("nome_profissional", "Dr. João Silva"),
                        help="Nome que aparecerá no sistema e nos emails"
                    )
                    
                    especialidade = st.text_input(
                        "Especialidade/Área:",
                        value=obter_configuracao("especialidade", "Clínico Geral"),
                        help="Ex: Dermatologia, Psicologia, etc."
                    )
                    
                    registro_profissional = st.text_input(
                        "Registro profissional:",
                        value=obter_configuracao("registro_profissional", "CRM 12345"),
                        help="Ex: CRM, CRP, CRO, etc."
                    )
                
                with col2:
                    st.markdown("**🏥 Informações do Local**")
                    
                    nome_clinica = st.text_input(
                        "Nome da clínica/estabelecimento:",
                        value=obter_configuracao("nome_clinica", "Clínica São Lucas"),
                        help="Nome do local de atendimento"
                    )
                    
                    telefone_contato = st.text_input(
                        "Telefone de contato:",
                        value=obter_configuracao("telefone_contato", "(11) 3333-4444"),
                        help="Telefone que aparecerá no sistema"
                    )
                    
                    whatsapp = st.text_input(
                        "WhatsApp:",
                        value=obter_configuracao("whatsapp", "(11) 99999-9999"),
                        help="Número do WhatsApp para contato"
                    )
                
                st.markdown("**📍 Endereço Completo**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    endereco_rua = st.text_input(
                        "Rua/Avenida:",
                        value=obter_configuracao("endereco_rua", "Rua das Flores, 123"),
                        help="Rua, número e complemento"
                    )
                
                with col2:
                    endereco_bairro = st.text_input(
                        "Bairro:",
                        value=obter_configuracao("endereco_bairro", "Centro"),
                        help="Bairro do estabelecimento"
                    )
                
                with col3:
                    endereco_cidade = st.text_input(
                        "Cidade - UF:",
                        value=obter_configuracao("endereco_cidade", "São Paulo - SP"),
                        help="Cidade e estado"
                    )
                
                # Instruções adicionais
                st.markdown("**📝 Instruções Adicionais**")
                
                instrucoes_chegada = st.text_area(
                    "Instruções para chegada:",
                    value=obter_configuracao("instrucoes_chegada", "Favor chegar 10 minutos antes do horário agendado."),
                    help="Instruções que aparecerão nos emails de confirmação",
                    height=100
                )
            
            with tab3:
                st.subheader("📧 Configurações de Email e Notificações")
                
                # Ativar/desativar sistema de email
                envio_automatico = st.checkbox(
                    "Ativar envio automático de emails",
                    value=obter_configuracao("envio_automatico", False),
                    help="Se ativado, emails serão enviados automaticamente para confirmações e cancelamentos"
                )
                
                if envio_automatico:
                    st.markdown("---")
                    st.markdown("**⚙️ Configurações do Servidor SMTP**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        email_sistema = st.text_input(
                            "Email do sistema:",
                            value=obter_configuracao("email_sistema", ""),
                            placeholder="sistema@clinica.com",
                            help="Email que enviará as confirmações automáticas"
                        )
                        
                        servidor_smtp = st.text_input(
                            "Servidor SMTP:",
                            value=obter_configuracao("servidor_smtp", "smtp.gmail.com"),
                            help="Para Gmail: smtp.gmail.com | Para Outlook: smtp-mail.outlook.com"
                        )
                    
                    with col2:
                        senha_email = st.text_input(
                            "Senha do email:",
                            value=obter_configuracao("senha_email", ""),
                            type="password",
                            help="Para Gmail: use senha de app (não a senha normal da conta)"
                        )
                        
                        try:
                            porta_valor = obter_configuracao("porta_smtp", 587)
                            porta_smtp_value = int(porta_valor) if porta_valor and str(porta_valor).strip() else 587
                        except (ValueError, TypeError):
                            porta_smtp_value = 587

                        porta_smtp = st.number_input(
                            "Porta SMTP:",
                            value=porta_smtp_value,
                            help="Para Gmail: 587 | Para Outlook: 587"
                        )                    
                    
                        st.markdown("---")
                        st.markdown("**🔐 Verificação de Segurança**")
                        
                        verificacao_codigo = st.checkbox(
                            "Exigir código de verificação para agendamentos",
                            value=obter_configuracao("verificacao_codigo_ativa", False),
                            help="Envia um código por email que o cliente deve inserir para confirmar o agendamento"
                        )
                        
                        if verificacao_codigo:
                            col1_ver, col2_ver = st.columns(2)
                            
                            with col1_ver:
                                st.info("""
                                **Como funciona:**
                                • Cliente preenche os dados
                                • Sistema envia código por email
                                • Cliente insere o código
                                • Agendamento é confirmado
                                """)
                            
                            with col2_ver:
                                tempo_expiracao = st.selectbox(
                                    "Tempo de expiração do código:",
                                    ["15 minutos", "30 minutos", "60 minutos"],
                                    index=1,
                                    help="Após este tempo, o código expira"
                                )                    
                    
                    # Configurações de envio
                    st.markdown("---")
                    st.markdown("**📬 Tipos de Email Automático**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        enviar_confirmacao = st.checkbox(
                            "Enviar email de confirmação",
                            value=obter_configuracao("enviar_confirmacao", True),
                            help="Envia email quando agendamento é confirmado"
                        )
                        

                    
                    with col2:
                        enviar_cancelamento = st.checkbox(
                            "Enviar email de cancelamento",
                            value=obter_configuracao("enviar_cancelamento", True),
                            help="Envia email quando agendamento é cancelado"
                        )
                        
                    
                    # Template de email
                    st.markdown("---")
                    st.markdown("**✉️ Personalizar Mensagens**")
                    
                    template_confirmacao = st.text_area(
                        "Template de confirmação:",
                        value=obter_configuracao("template_confirmacao", 
                            "Olá {nome}!\n\nSeu agendamento foi confirmado:\n📅 Data: {data}\n⏰ Horário: {horario}\n\nAguardamos você!"),
                        help="Use {nome}, {data}, {horario}, {local} como variáveis",
                        height=100
                    )
                    
                    # Teste de email
                    st.markdown("---")
                    st.markdown("**🧪 Testar Configurações**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        email_teste = st.text_input(
                            "Email para teste:",
                            value=obter_configuracao("email_teste", ""),
                            placeholder="seu@email.com",
                            help="Digite um email para receber um teste"
                        )
                    
                    with col2:
                        if st.button("📧 Enviar Email Teste", type="secondary"):
                            if email_teste and email_sistema and senha_email:
                                # Salvar o email de teste
                                salvar_configuracao("email_teste", email_teste)
                                
                                # Tentar envio manual (sem chamar função externa)
                                try:
                                    import smtplib
                                    from email.mime.text import MIMEText
                                    from email.mime.multipart import MIMEMultipart
                                    
                                    # Criar mensagem de teste
                                    msg = MIMEMultipart()
                                    msg['From'] = email_sistema
                                    msg['To'] = email_teste
                                    msg['Subject'] = f"🧪 Teste de Email - {nome_profissional}"
                                    
                                    corpo = f"""
Olá!

Este é um email de teste do sistema de agendamento.

✅ Configurações funcionando corretamente!

📧 Email do sistema: {email_sistema}
🏥 Clínica: {nome_clinica}
👨‍⚕️ Profissional: {nome_profissional}

Se você recebeu este email, significa que as configurações SMTP estão corretas.

Atenciosamente,
Sistema de Agendamento Online
"""
                                    
                                    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
                                    
                                    # Enviar email
                                    server = smtplib.SMTP(servidor_smtp, porta_smtp)
                                    server.starttls()
                                    server.login(email_sistema, senha_email)
                                    server.send_message(msg)
                                    server.quit()
                                    
                                    st.success("✅ Email de teste enviado com sucesso!")
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao enviar email: {str(e)}")
                            else:
                                st.warning("⚠️ Preencha o email de teste e configure o sistema primeiro")

                    
                    # Seção de backup GitHub (manter como está)
                    st.markdown("---")
                    st.markdown("**☁️ Backup de Configurações**")   
                
                    # Seção de backup GitHub (ADICIONAR DEPOIS da seção de teste de email)
                    st.markdown("---")
                    st.markdown("**☁️ Backup de Configurações**")
                    
                    backup_github_ativo = st.checkbox(
                        "Ativar backup automático no GitHub",
                        value=obter_configuracao("backup_github_ativo", False),
                        help="Salva automaticamente suas configurações em repositório GitHub privado"
                    )
                    
                    if backup_github_ativo:
                        st.success("✅ Backup automático ativado - suas configurações serão salvas automaticamente!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 Fazer Backup Manual", type="secondary"):
                                with st.spinner("Enviando backup para GitHub..."):
                                    try:
                                        if backup_configuracoes_github():
                                            st.success("✅ Backup enviado com sucesso!")
                                            st.info(f"🔗 Confira em: https://github.com/{st.secrets['GITHUB_REPO']}")
                                        else:
                                            st.error("❌ Erro no backup. Verifique as configurações.")
                                    except Exception as e:
                                        st.error(f"❌ Erro: {e}")
                        
                        with col2:
                            # Mostrar última data de backup se disponível
                            ultima_config = obter_configuracao("_backup_timestamp", "")
                            if ultima_config:
                                try:
                                    from datetime import datetime
                                    data_backup = datetime.fromisoformat(ultima_config)
                                    data_formatada = data_backup.strftime("%d/%m/%Y às %H:%M")
                                    st.info(f"📅 Último backup: {data_formatada}")
                                except:
                                    st.info("📅 Backup disponível no GitHub")
                            else:
                                st.info("📅 Primeiro backup será feito automaticamente")
                    
                    else:
                        st.info("💡 Ative o backup automático para nunca perder suas configurações quando o Streamlit reiniciar!")
                        
                        # Botão para fazer backup mesmo com função desativada
                        if st.button("💾 Fazer Backup Único", help="Fazer backup sem ativar função automática"):
                            with st.spinner("Enviando backup..."):
                                try:
                                    if backup_configuracoes_github():
                                        st.success("✅ Backup enviado com sucesso!")
                                        st.info(f"🔗 Confira em: https://github.com/{st.secrets['GITHUB_REPO']}")
                                    else:
                                        st.error("❌ Erro no backup. Verifique token GitHub.")
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
                
                else:
                    st.info("📧 Sistema de email desativado. Ative acima para configurar o envio automático.")            
            # Botão para salvar todas as configurações
            st.markdown("---")
            if st.button("💾 Salvar Todas as Configurações", type="primary", use_container_width=True):
                # Salvar configurações da tab 1
                salvar_configuracao("dias_futuros", dias_futuros)
                salvar_configuracao("antecedencia_minima", antecedencia_opcoes[antecedencia_selecionada])
                salvar_configuracao("horario_inicio", horario_inicio.strftime("%H:%M"))
                salvar_configuracao("horario_fim", horario_fim.strftime("%H:%M"))
                salvar_configuracao("intervalo_consultas", intervalo_opcoes[intervalo_selecionado])
                salvar_configuracao("confirmacao_automatica", confirmacao_automatica)
                                
                # Salvar configurações da tab 2
                salvar_configuracao("nome_profissional", nome_profissional)
                salvar_configuracao("especialidade", especialidade)
                salvar_configuracao("registro_profissional", registro_profissional)
                salvar_configuracao("nome_clinica", nome_clinica)
                salvar_configuracao("telefone_contato", telefone_contato)
                salvar_configuracao("whatsapp", whatsapp)
                salvar_configuracao("endereco_rua", endereco_rua)
                salvar_configuracao("endereco_bairro", endereco_bairro)
                salvar_configuracao("endereco_cidade", endereco_cidade)
                salvar_configuracao("instrucoes_chegada", instrucoes_chegada)
                
                # Salvar configurações da tab 3
                salvar_configuracao("envio_automatico", envio_automatico)
                salvar_configuracao("email_teste", email_teste if envio_automatico else "")
                if envio_automatico:
                    salvar_configuracao("email_sistema", email_sistema)
                    salvar_configuracao("senha_email", senha_email)
                    salvar_configuracao("servidor_smtp", servidor_smtp)
                    salvar_configuracao("porta_smtp", porta_smtp)
                    salvar_configuracao("enviar_confirmacao", enviar_confirmacao)
                    salvar_configuracao("enviar_cancelamento", enviar_cancelamento)
                    salvar_configuracao("template_confirmacao", template_confirmacao)
                    salvar_configuracao("verificacao_codigo_ativa", verificacao_codigo if envio_automatico else False)
                
                # NOVO: Salvar configuração de backup GitHub
                try:
                    salvar_configuracao("backup_github_ativo", backup_github_ativo)
                except NameError:
                    # Primeira execução - usar valor padrão
                    salvar_configuracao("backup_github_ativo", obter_configuracao("backup_github_ativo", False))
                
                st.success("✅ Todas as configurações foram salvas com sucesso!")
                
                # NOVO: Backup automático no GitHub (se ativado)
                if backup_github_ativo:
                    try:
                        with st.spinner("📤 Fazendo backup no GitHub..."):
                            if backup_configuracoes_github():
                                st.success("☁️ Backup automático enviado para GitHub!")
                            else:
                                st.warning("⚠️ Erro no backup automático. Configurações salvas localmente.")
                    except Exception as e:
                        st.warning(f"⚠️ Erro no backup automático: {e}")
                
                # Mostrar resumo
                st.markdown("**📋 Resumo das configurações salvas:**")
                st.info(f"""
                📅 **Agendamento:** {intervalo_selecionado} de {horario_inicio.strftime('%H:%M')} às {horario_fim.strftime('%H:%M')}
                ⏰ **Antecedência:** {antecedencia_selecionada}
                🔄 **Confirmação:** {'Automática' if confirmacao_automatica else 'Manual'}
                📧 **Email:** {'Ativado' if envio_automatico else 'Desativado'}
                ☁️ **Backup:** {'Ativado' if backup_github_ativo else 'Desativado'}
                👨‍⚕️ **Profissional:** {nome_profissional} - {especialidade}
                🏥 **Local:** {nome_clinica}
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif opcao == "📅 Configurar Agenda":
            
            dias_pt = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
            dias_atuais = obter_dias_uteis()
            
            st.markdown("Selecione os dias da semana:")
            
            cols = st.columns(4)
            dias_selecionados = []
            
            for i, (dia_en, dia_pt) in enumerate(dias_pt.items()):
                with cols[i % 4]:
                    if st.checkbox(dia_pt, value=(dia_en in dias_atuais), key=f"dia_{dia_en}"):
                        dias_selecionados.append(dia_en)
            
            if st.button("💾 Salvar Dias", type="primary", use_container_width=True):
                salvar_dias_uteis(dias_selecionados)
                st.success("✅ Dias salvos!")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        elif opcao == "🗓️ Gerenciar Bloqueios":
                    
                    # Tabs para diferentes tipos de bloqueio
                    tab1, tab2, tab3, tab4 = st.tabs(["📅 Dias Específicos", "📆 Períodos", "🕐 Horários Específicos", "⏰ Bloqueios Permanentes"])
                    
                    with tab1:
                        st.subheader("📅 Bloquear Dias Específicos")
                        st.info("💡 Use esta opção para bloquear poucos dias isolados (ex: feriados, faltas pontuais)")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📌 Bloquear Data Individual**")
                            data_bloqueio = st.date_input("Data para bloquear:", min_value=datetime.today())
                            
                            if st.button("🚫 Bloquear Dia", type="primary", key="btn_bloquear_dia"):
                                if adicionar_bloqueio(data_bloqueio.strftime("%Y-%m-%d")):
                                    st.success("✅ Dia bloqueado!")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Data já bloqueada.")
                        
                        with col2:
                            st.markdown("**ℹ️ Dias Específicos vs Períodos:**")
                            st.markdown("""
                            **🎯 Use "Dias Específicos" para:**
                            • Feriados isolados
                            • Faltas pontuais  
                            • 1-3 dias não consecutivos
                            
                            **🎯 Use "Períodos" para:**
                            • Férias (vários dias seguidos)
                            • Viagens longas
                            • Congressos/cursos
                            """)
                        
                        # Lista de datas bloqueadas (dias inteiros)
                        st.subheader("🚫 Dias Individuais Bloqueados")
                        bloqueios = obter_bloqueios()
                        
                        if bloqueios:
                            for data in bloqueios:
                                data_obj = datetime.strptime(data, "%Y-%m-%d")
                                data_formatada = data_obj.strftime("%d/%m/%Y - %A")
                                data_formatada = data_formatada.replace('Monday', 'Segunda-feira')\
                                    .replace('Tuesday', 'Terça-feira').replace('Wednesday', 'Quarta-feira')\
                                    .replace('Thursday', 'Quinta-feira').replace('Friday', 'Sexta-feira')\
                                    .replace('Saturday', 'Sábado').replace('Sunday', 'Domingo')
                                
                                col_data, col_btn = st.columns([4, 1])
                                with col_data:
                                    st.markdown(f"""
                                    <div style="background: #fee2e2; border: 1px solid #fecaca; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                                        <span style="color: #991b1b; font-weight: 500;">🚫 {data_formatada}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_btn:
                                    if st.button("🗑️", key=f"remove_dia_{data}", help="Remover bloqueio"):
                                        remover_bloqueio(data)
                                        st.rerun()
                        else:
                            st.info("📅 Nenhum dia individual bloqueado atualmente.")
                    
                    with tab2:
                        st.subheader("📆 Bloquear Períodos")
                        st.info("💡 Use esta opção para bloquear vários dias consecutivos (ex: férias, viagens)")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**➕ Criar Novo Período Bloqueado**")
                            
                            data_inicio_periodo = st.date_input(
                                "Data inicial:", 
                                min_value=datetime.today().date(), 
                                key="periodo_inicio"
                            )

                            data_fim_periodo = st.date_input(
                                "Data final:", 
                                key="periodo_fim"
                            )

                            # Validação manual das datas
                            if data_inicio_periodo and data_fim_periodo:
                                if data_fim_periodo < data_inicio_periodo:
                                    st.error("❌ A data final deve ser posterior à data inicial!")
                                    datas_validas = False
                                else:
                                    datas_validas = True
                            else:
                                datas_validas = False

                            descricao_periodo = st.text_input(
                                "Descrição:",
                                placeholder="Ex: Férias de Janeiro, Viagem Europa, Congresso...",
                                key="desc_periodo"
                            )

                            if st.button("🚫 Bloquear Período", type="primary", key="btn_bloquear_periodo_novo"):
                                if datas_validas:
                                    if descricao_periodo.strip():
                                        periodo_id = adicionar_bloqueio_periodo(
                                            data_inicio_periodo.strftime("%Y-%m-%d"),
                                            data_fim_periodo.strftime("%Y-%m-%d"),
                                            descricao_periodo
                                        )
                                        
                                        if periodo_id:
                                            dias_total = (data_fim_periodo - data_inicio_periodo).days + 1
                                            st.success(f"✅ Período bloqueado com sucesso! ({dias_total} dias)")
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao bloquear período.")
                                    else:
                                        st.warning("⚠️ Digite uma descrição para o período.")
                                else:
                                    st.warning("⚠️ Verifique se as datas estão corretas.")
                        
                        with col2:
                            st.markdown("**ℹ️ Vantagens dos Períodos:**")
                            st.success("""
                            ✅ **Organizado:** Um período = uma linha na lista
                            ✅ **Fácil remoção:** Exclui tudo de uma vez  
                            ✅ **Visual limpo:** Sem poluição na tela
                            ✅ **Informativo:** Mostra status e duração
                            """)
                        
                        # Lista de períodos bloqueados
                        st.markdown("---")
                        st.subheader("📋 Períodos Bloqueados")
                        
                        periodos = obter_bloqueios_periodos()
                        
                        if periodos:
                            for periodo in periodos:
                                periodo_id, data_inicio, data_fim, descricao, criado_em = periodo
                                
                                # Calcular informações do período
                                try:
                                    inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
                                    fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
                                    dias_total = (fim_obj - inicio_obj).days + 1
                                    
                                    inicio_formatado = inicio_obj.strftime("%d/%m/%Y")
                                    fim_formatado = fim_obj.strftime("%d/%m/%Y")
                                    
                                    # Verificar se período já passou, está ativo ou é futuro
                                    hoje = datetime.now().date()
                                    if fim_obj.date() < hoje:
                                        status_cor = "#6b7280"  # Cinza para passado
                                        status_texto = "Finalizado"
                                        status_icon = "✅"
                                    elif inicio_obj.date() <= hoje <= fim_obj.date():
                                        status_cor = "#f59e0b"  # Amarelo para ativo
                                        status_texto = "Ativo"
                                        status_icon = "🟡"
                                    else:
                                        status_cor = "#3b82f6"  # Azul para futuro
                                        status_texto = "Agendado"
                                        status_icon = "📅"
                                    
                                except:
                                    inicio_formatado = data_inicio
                                    fim_formatado = data_fim
                                    dias_total = "?"
                                    status_cor = "#6b7280"
                                    status_texto = "Indefinido"
                                    status_icon = "❓"
                                
                                col_info, col_btn = st.columns([5, 1])
                                
                                with col_info:
                                    st.markdown(f"""
                                    <div style="background: white; border-left: 4px solid {status_cor}; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                            <h4 style="color: #1f2937; margin: 0; font-size: 1.1rem;">📆 {descricao}</h4>
                                            <span style="background: {status_cor}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                                                {status_icon} {status_texto}
                                            </span>
                                        </div>
                                        <div style="color: #374151; font-size: 0.95rem; line-height: 1.4;">
                                            <strong>📅 Período:</strong> {inicio_formatado} até {fim_formatado}<br>
                                            <strong>📊 Duração:</strong> {dias_total} dia(s)
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col_btn:
                                    st.markdown("<br><br>", unsafe_allow_html=True)  # Espaçamento para alinhar
                                    if st.button("🗑️", key=f"remove_periodo_{periodo_id}", help="Remover período completo"):
                                        if remover_bloqueio_periodo(periodo_id):
                                            st.success(f"✅ Período '{descricao}' removido!")
                                            st.rerun()
                                        else:
                                            st.error("❌ Erro ao remover período.")
                        else:
                            st.info("📅 Nenhum período bloqueado.")
                    
                    with tab3:
                        st.subheader("🕐 Bloquear Horários Específicos")
                        
                        # Sub-abas para organizar melhor
                        subtab1, subtab2 = st.tabs(["📅 Por Data Específica", "📆 Por Dia da Semana"])
                        
                        # =====================================================
                        # SUBTAB 1: BLOQUEIO POR DATA ESPECÍFICA (código atual)
                        # =====================================================
                        with subtab1:
                            st.markdown("**📅 Bloqueio para uma data específica**")
                            
                            # Seleção de data
                            data_horario = st.date_input("Selecionar data:", min_value=datetime.today(), key="data_horario_especifico")
                            data_horario_str = data_horario.strftime("%Y-%m-%d")
                            
                            # Obter configurações de horários
                            horario_inicio_config = obter_configuracao("horario_inicio", "09:00")
                            horario_fim_config = obter_configuracao("horario_fim", "18:00")
                            intervalo_consultas = obter_configuracao("intervalo_consultas", 60)
                            
                            # Gerar horários possíveis
                            try:
                                hora_inicio = datetime.strptime(horario_inicio_config, "%H:%M").time()
                                hora_fim = datetime.strptime(horario_fim_config, "%H:%M").time()
                                
                                inicio_min = hora_inicio.hour * 60 + hora_inicio.minute
                                fim_min = hora_fim.hour * 60 + hora_fim.minute
                                
                                horarios_possiveis = []
                                horario_atual = inicio_min
                                
                                while horario_atual + intervalo_consultas <= fim_min:
                                    h = horario_atual // 60
                                    m = horario_atual % 60
                                    horarios_possiveis.append(f"{str(h).zfill(2)}:{str(m).zfill(2)}")
                                    horario_atual += intervalo_consultas
                                    
                            except:
                                horarios_possiveis = [f"{str(h).zfill(2)}:00" for h in range(9, 18)]
                            
                            # Verificar quais horários já estão bloqueados
                            bloqueios_dia = obter_bloqueios_horarios()
                            horarios_bloqueados_dia = [h for d, h in bloqueios_dia if d == data_horario_str]
                            
                            st.markdown("**Selecione os horários que deseja bloquear:**")
                            
                            # Layout em colunas para os horários
                            cols = st.columns(4)
                            horarios_selecionados = []
                            
                            for i, horario in enumerate(horarios_possiveis):
                                with cols[i % 4]:
                                    ja_bloqueado = horario in horarios_bloqueados_dia
                                    if ja_bloqueado:
                                        st.markdown(f"""
                                        <div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 8px; padding: 8px; text-align: center; margin: 4px 0;">
                                            <span style="color: #991b1b; font-weight: 600;">🚫 {horario}</span><br>
                                            <small style="color: #991b1b;">Bloqueado</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        if st.checkbox(f"🕐 {horario}", key=f"horario_especifico_{horario}"):
                                            horarios_selecionados.append(horario)
                            
                            # Botões de ação
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("🚫 Bloquear Horários Selecionados", type="primary", key="btn_bloquear_horarios_data"):
                                    if horarios_selecionados:
                                        bloqueados = 0
                                        for horario in horarios_selecionados:
                                            if adicionar_bloqueio_horario(data_horario_str, horario):
                                                bloqueados += 1
                                        
                                        if bloqueados > 0:
                                            st.success(f"✅ {bloqueados} horário(s) bloqueado(s) com sucesso!")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Horários já estavam bloqueados.")
                                    else:
                                        st.warning("⚠️ Selecione pelo menos um horário para bloquear.")
                            
                            with col2:
                                if st.button("🔓 Desbloquear Todos os Horários do Dia", type="secondary", key="btn_desbloquear_dia_data"):
                                    if horarios_bloqueados_dia:
                                        for horario in horarios_bloqueados_dia:
                                            remover_bloqueio_horario(data_horario_str, horario)
                                        
                                        st.success(f"✅ Todos os horários do dia {data_horario.strftime('%d/%m/%Y')} foram desbloqueados!")
                                        st.rerun()
                                    else:
                                        st.info("ℹ️ Nenhum horário bloqueado neste dia.")
                        
                        # =====================================================
                        # SUBTAB 2: BLOQUEIO POR DIA DA SEMANA (NOVO)
                        # =====================================================
                        with subtab2:
                            st.markdown("**📆 Bloqueio recorrente por dia da semana**")
                            st.info("💡 Configure horários que ficam sempre bloqueados em determinados dias da semana (ex: sábados das 12h às 18h)")
                            
                            # Seleção do dia da semana
                            dias_opcoes = {
                                "Monday": "Segunda-feira",
                                "Tuesday": "Terça-feira", 
                                "Wednesday": "Quarta-feira",
                                "Thursday": "Quinta-feira",
                                "Friday": "Sexta-feira",
                                "Saturday": "Sábado",
                                "Sunday": "Domingo"
                            }
                            
                            dia_semana_selecionado = st.selectbox(
                                "Selecione o dia da semana:",
                                list(dias_opcoes.keys()),
                                format_func=lambda x: dias_opcoes[x],
                                key="dia_semana_bloqueio"
                            )
                            
                            # Obter horários possíveis (mesmo cálculo da outra aba)
                            horario_inicio_config = obter_configuracao("horario_inicio", "09:00")
                            horario_fim_config = obter_configuracao("horario_fim", "18:00")
                            intervalo_consultas = obter_configuracao("intervalo_consultas", 60)
                            
                            try:
                                hora_inicio = datetime.strptime(horario_inicio_config, "%H:%M").time()
                                hora_fim = datetime.strptime(horario_fim_config, "%H:%M").time()
                                
                                inicio_min = hora_inicio.hour * 60 + hora_inicio.minute
                                fim_min = hora_fim.hour * 60 + hora_fim.minute
                                
                                horarios_possiveis = []
                                horario_atual = inicio_min
                                
                                while horario_atual + intervalo_consultas <= fim_min:
                                    h = horario_atual // 60
                                    m = horario_atual % 60
                                    horarios_possiveis.append(f"{str(h).zfill(2)}:{str(m).zfill(2)}")
                                    horario_atual += intervalo_consultas
                                    
                            except:
                                horarios_possiveis = [f"{str(h).zfill(2)}:00" for h in range(9, 18)]
                            
                            st.markdown(f"**Selecione os horários para bloquear todas as {dias_opcoes[dia_semana_selecionado].lower()}:**")
                            
                            # Layout em colunas para os horários
                            cols = st.columns(4)
                            horarios_selecionados_semanal = []
                            
                            for i, horario in enumerate(horarios_possiveis):
                                with cols[i % 4]:
                                    if st.checkbox(f"🕐 {horario}", key=f"horario_semanal_{horario}"):
                                        horarios_selecionados_semanal.append(horario)
                            
                            # Descrição opcional
                            descricao_semanal = st.text_input(
                                "Descrição (opcional):",
                                placeholder=f"Ex: {dias_opcoes[dia_semana_selecionado]} - meio período",
                                key="desc_bloqueio_semanal"
                            )
                            
                            # Botão para salvar bloqueio semanal
                            if st.button("💾 Salvar Bloqueio Semanal", type="primary", key="btn_salvar_semanal"):
                                if horarios_selecionados_semanal:
                                    if adicionar_bloqueio_semanal(dia_semana_selecionado, horarios_selecionados_semanal, descricao_semanal):
                                        st.success(f"✅ Bloqueio semanal para {dias_opcoes[dia_semana_selecionado]} criado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Esse bloqueio semanal já existe ou ocorreu um erro.")
                                else:
                                    st.warning("⚠️ Selecione pelo menos um horário para bloquear.")
                            
                            # Lista de bloqueios semanais existentes
                            st.markdown("---")
                            st.subheader("📋 Bloqueios Semanais Ativos")
                            
                            bloqueios_semanais = obter_bloqueios_semanais()
                            
                            if bloqueios_semanais:
                                for bloqueio in bloqueios_semanais:
                                    bloqueio_id, dia_semana, horarios_str, descricao = bloqueio
                                    
                                    horarios_lista = horarios_str.split(",")
                                    horarios_texto = ", ".join(horarios_lista)
                                    
                                    col1, col2 = st.columns([4, 1])
                                    
                                    with col1:
                                        st.markdown(f"""
                                        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                                            <h4 style="color: #92400e; margin: 0 0 0.5rem 0;">📅 {dias_opcoes[dia_semana]}</h4>
                                            <p style="margin: 0; color: #92400e;">
                                                <strong>Horários bloqueados:</strong> {horarios_texto}<br>
                                                {f'<strong>Descrição:</strong> {descricao}' if descricao else ''}
                                            </p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with col2:
                                        if st.button("🗑️", key=f"remove_semanal_{bloqueio_id}", help="Remover bloqueio semanal"):
                                            if remover_bloqueio_semanal(bloqueio_id):
                                                st.success("Bloqueio semanal removido!")
                                                st.rerun()
                            else:
                                st.info("📅 Nenhum bloqueio semanal configurado.")
                        
                        # Lista de horários bloqueados por data específica
                        st.subheader("🕐 Horários Específicos Bloqueados")
                        bloqueios_horarios = obter_bloqueios_horarios()
                        
                        if bloqueios_horarios:
                            # Agrupar por data
                            bloqueios_por_data = {}
                            for data, horario in bloqueios_horarios:
                                if data not in bloqueios_por_data:
                                    bloqueios_por_data[data] = []
                                bloqueios_por_data[data].append(horario)
                            
                            for data, horarios in sorted(bloqueios_por_data.items()):
                                data_obj = datetime.strptime(data, "%Y-%m-%d")
                                data_formatada = data_obj.strftime("%d/%m/%Y - %A")
                                data_formatada = data_formatada.replace('Monday', 'Segunda-feira')\
                                    .replace('Tuesday', 'Terça-feira').replace('Wednesday', 'Quarta-feira')\
                                    .replace('Thursday', 'Quinta-feira').replace('Friday', 'Sexta-feira')\
                                    .replace('Saturday', 'Sábado').replace('Sunday', 'Domingo')
                                
                                st.markdown(f"**📅 {data_formatada}**")
                                
                                # Mostrar horários bloqueados em colunas
                                cols = st.columns(6)
                                for i, horario in enumerate(sorted(horarios)):
                                    with cols[i % 6]:
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.markdown(f"🚫 **{horario}**")
                                        with col2:
                                            if st.button("🗑️", key=f"remove_horario_{data}_{horario}", help="Remover bloqueio"):
                                                remover_bloqueio_horario(data, horario)
                                                st.rerun()
                                
                                st.markdown("---")
                        else:
                            st.info("🕐 Nenhum horário específico bloqueado atualmente.")
                    
                    with tab4:
                        st.subheader("⏰ Bloqueios Permanentes")
                        
                        st.markdown("""
                        <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                            ℹ️ <strong>Bloqueios Permanentes:</strong><br>
                            Configure horários que ficam sempre bloqueados (ex: almoço, intervalos, etc.)
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Formulário para novo bloqueio
                        st.markdown("### ➕ Criar Novo Bloqueio Permanente")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            horario_inicio_perm = st.time_input("Horário de início:", key="inicio_permanente")
                            
                        with col2:
                            horario_fim_perm = st.time_input("Horário de fim:", key="fim_permanente")
                        
                        # Seleção de dias da semana
                        st.markdown("**Dias da semana:**")
                        
                        dias_opcoes = {
                            "Monday": "Segunda-feira",
                            "Tuesday": "Terça-feira", 
                            "Wednesday": "Quarta-feira",
                            "Thursday": "Quinta-feira",
                            "Friday": "Sexta-feira",
                            "Saturday": "Sábado",
                            "Sunday": "Domingo"
                        }
                        
                        cols = st.columns(4)
                        dias_selecionados_perm = []
                        
                        for i, (dia_en, dia_pt) in enumerate(dias_opcoes.items()):
                            with cols[i % 4]:
                                if st.checkbox(dia_pt, key=f"dia_perm_{dia_en}"):
                                    dias_selecionados_perm.append(dia_en)
                        
                        # Descrição
                        descricao_perm = st.text_input("Descrição:", placeholder="Ex: Horário de Almoço", key="desc_permanente")
                        
                        # Botão para salvar
                        if st.button("💾 Salvar Bloqueio Permanente", type="primary", key="btn_salvar_permanente"):
                            if horario_inicio_perm and horario_fim_perm and dias_selecionados_perm and descricao_perm:
                                if horario_fim_perm > horario_inicio_perm:
                                    inicio_str = horario_inicio_perm.strftime("%H:%M")
                                    fim_str = horario_fim_perm.strftime("%H:%M")
                                    
                                    if adicionar_bloqueio_permanente(inicio_str, fim_str, dias_selecionados_perm, descricao_perm):
                                        st.success("✅ Bloqueio permanente criado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erro ao criar bloqueio.")
                                else:
                                    st.warning("⚠️ Horário de fim deve ser posterior ao horário de início.")
                            else:
                                st.warning("⚠️ Preencha todos os campos obrigatórios.")
                        
                        # Lista de bloqueios permanentes existentes
                        st.markdown("---")
                        st.subheader("📋 Bloqueios Permanentes Ativos")
                        
                        bloqueios_permanentes = obter_bloqueios_permanentes()
                        
                        if bloqueios_permanentes:
                            for bloqueio in bloqueios_permanentes:
                                bloqueio_id, inicio, fim, dias, descricao = bloqueio
                                
                                # Converter dias de volta para português
                                dias_lista = dias.split(",")
                                dias_pt = [dias_opcoes.get(dia, dia) for dia in dias_lista]
                                dias_texto = ", ".join(dias_pt)
                                
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                                        <h4 style="color: #856404; margin: 0 0 0.5rem 0;">⏰ {descricao}</h4>
                                        <p style="margin: 0; color: #856404;">
                                            <strong>Horário:</strong> {inicio} às {fim}<br>
                                            <strong>Dias:</strong> {dias_texto}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    if st.button("🗑️", key=f"remove_perm_{bloqueio_id}", help="Remover bloqueio permanente"):
                                        if remover_bloqueio_permanente(bloqueio_id):
                                            st.success("Bloqueio removido!")
                                            st.rerun()
                        else:
                            st.info("📅 Nenhum bloqueio permanente configurado.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        elif opcao == "👥 Lista de Agendamentos":
            
            # Obter todos os agendamentos
            agendamentos = buscar_agendamentos()
            
            if agendamentos:
                
                # CSS para cards super compactos
                st.markdown("""
                <style>
                .header-data {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    margin: 1.5rem 0 0.5rem 0;
                    font-weight: 700;
                    font-size: 1.1rem;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(102,126,234,0.3);
                }
                
                .card-compacto {
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 0.5rem 0.75rem !important;
                    margin: 0.25rem 0 !important;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    transition: all 0.2s ease;
                }
                
                .card-compacto:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                }
                
                .card-pendente {
                    border-left: 4px solid #f59e0b;
                    background: #fffbeb;
                }
                
                .card-confirmado {
                    border-left: 4px solid #3b82f6;
                    background: #eff6ff;
                }
                
                .card-atendido {
                    border-left: 4px solid #10b981;
                    background: #ecfdf5;
                }
                
                .card-cancelado {
                    border-left: 4px solid #ef4444;
                    background: #fef2f2;
                }
                
                .nome-compacto {
                    font-size: 1rem !important;
                    font-weight: 600 !important;
                    color: #1f2937 !important;
                    margin: 0 !important;
                    line-height: 1.2 !important;
                }
                
                .info-compacta {
                    font-size: 0.8rem !important;
                    color: #6b7280 !important;
                    margin: 0.25rem 0 0 0 !important;
                    line-height: 1.3 !important;
                }
                
                .horario-destaque {
                    color: #3b82f6 !important;
                    font-weight: 600 !important;
                    font-size: 0.9rem !important;
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 0.7rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    margin-top: 0.25rem;
                }
                
                .badge-pendente {
                    background: #fbbf24;
                    color: #fef3c7;
                }
                
                .badge-confirmado {
                    background: #60a5fa;
                    color: #eff6ff;
                }
                
                .badge-atendido {
                    background: #34d399;
                    color: #ecfdf5;
                }
                
                .badge-cancelado {
                    background: #f87171;
                    color: #fef2f2;
                }
                
                /* Botões menores */
                .stButton > button {
                    padding: 0.25rem 0.5rem !important;
                    font-size: 0.8rem !important;
                    min-height: 2rem !important;
                    margin: 0.1rem 0 !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # ========================================
                # FILTROS-ESTATÍSTICAS UNIFICADOS
                # ========================================
                
                # Calcular dados
                hoje = datetime.now().date()
                amanha = hoje + timedelta(days=1)
                agendamentos_hoje = [a for a in agendamentos if a[1] == hoje.strftime("%Y-%m-%d")]
                agendamentos_amanha = [a for a in agendamentos if a[1] == amanha.strftime("%Y-%m-%d")]
                pendentes_total = len([a for a in agendamentos if len(a) > 6 and a[6] == "pendente"])
                confirmados_total = len([a for a in agendamentos if len(a) > 6 and a[6] == "confirmado"])
                
                # Inicializar estado
                if 'dia_selecionado' not in st.session_state:
                    st.session_state.dia_selecionado = None
                
                # FILTROS QUE SÃO ESTATÍSTICAS
                st.subheader("🔍 Filtros")
                
                col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
                
                with col_f1:
                    if st.button(f"📅 Hoje\n({len(agendamentos_hoje)})", key="filtro_hoje", use_container_width=True):
                        st.session_state.dia_selecionado = hoje.strftime("%Y-%m-%d")
                        st.rerun()
                
                with col_f2:
                    if st.button(f"➡️ Amanhã\n({len(agendamentos_amanha)})", key="filtro_amanha", use_container_width=True):
                        st.session_state.dia_selecionado = amanha.strftime("%Y-%m-%d")
                        st.rerun()
                
                with col_f3:
                    if st.button(f"⏳ Pendentes\n({pendentes_total})", key="filtro_pendentes", use_container_width=True):
                        st.session_state.dia_selecionado = "FILTRO_PENDENTES"
                        st.rerun()
                
                with col_f4:
                    if st.button(f"✅ Confirmados\n({confirmados_total})", key="filtro_confirmados", use_container_width=True):
                        st.session_state.dia_selecionado = "FILTRO_CONFIRMADOS"
                        st.rerun()
                
                with col_f5:
                    if st.button(f"🔄 Todos\n({len(agendamentos)})", key="filtro_todos", use_container_width=True):
                        st.session_state.dia_selecionado = None
                        st.rerun()
                
                # ========================================
                # FILTRAR AGENDAMENTOS
                # ========================================
                
                # Determinar agendamentos a mostrar
                if st.session_state.dia_selecionado == "FILTRO_PENDENTES":
                    agendamentos_filtrados = [a for a in agendamentos if len(a) > 6 and a[6] == "pendente"]
                    titulo_secao = "⏳ Agendamentos Pendentes"
                elif st.session_state.dia_selecionado == "FILTRO_CONFIRMADOS":
                    agendamentos_filtrados = [a for a in agendamentos if len(a) > 6 and a[6] == "confirmado"]
                    titulo_secao = "✅ Agendamentos Confirmados"
                elif st.session_state.dia_selecionado:
                    agendamentos_filtrados = [a for a in agendamentos if a[1] == st.session_state.dia_selecionado]
                    if agendamentos_filtrados:
                        data_obj = datetime.strptime(st.session_state.dia_selecionado, "%Y-%m-%d")
                        data_formatada = data_obj.strftime("%d/%m/%Y - %A").replace('Monday', 'Segunda-feira')\
                            .replace('Tuesday', 'Terça-feira').replace('Wednesday', 'Quarta-feira')\
                            .replace('Thursday', 'Quinta-feira').replace('Friday', 'Sexta-feira')\
                            .replace('Saturday', 'Sábado').replace('Sunday', 'Domingo')
                        titulo_secao = f"📅 {data_formatada}"
                    else:
                        titulo_secao = "📅 Dia selecionado"
                else:
                    agendamentos_filtrados = agendamentos
                    titulo_secao = "📋 Todos os Agendamentos"
                
                # ========================================
                # AGRUPAR POR DATA E MOSTRAR
                # ========================================
                
                st.markdown("---")
                st.subheader(titulo_secao)
                
                if agendamentos_filtrados:
                    st.markdown(f"**📊 {len(agendamentos_filtrados)} agendamento(s)**")
                    
                    # Ordenar por data e horário
                    agendamentos_filtrados.sort(key=lambda x: (x[1], x[2]))
                    
                    # Agrupar por data
                    agendamentos_por_data = {}
                    for agendamento in agendamentos_filtrados:
                        data = agendamento[1]
                        if data not in agendamentos_por_data:
                            agendamentos_por_data[data] = []
                        agendamentos_por_data[data].append(agendamento)
                    
                    # Mostrar cada data com seus agendamentos
                    for data_str, agendamentos_do_dia in agendamentos_por_data.items():
                        
                        # CABEÇALHO DA DATA
                        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
                        
                        # Formatação: 18/07 - SEX
                        dia_mes = data_obj.strftime("%d/%m")
                        dia_semana = data_obj.strftime("%a").upper()
                        
                        # Traduzir dia da semana
                        traducao_dias = {
                            'MON': 'SEG', 'TUE': 'TER', 'WED': 'QUA', 
                            'THU': 'QUI', 'FRI': 'SEX', 'SAT': 'SAB', 'SUN': 'DOM'
                        }
                        dia_semana_pt = traducao_dias.get(dia_semana, dia_semana)
                        
                        # Mostrar header da data
                        st.markdown(f"""
                        <div class="header-data">
                            📅 {dia_mes} - {dia_semana_pt} ({len(agendamentos_do_dia)} agendamento{'s' if len(agendamentos_do_dia) != 1 else ''})
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # CARDS DOS AGENDAMENTOS DO DIA
                        for agendamento in agendamentos_do_dia:
                            if len(agendamento) == 7:
                                agendamento_id, data, horario, nome, telefone, email, status = agendamento
                            elif len(agendamento) == 6:
                                agendamento_id, data, horario, nome, telefone, email = agendamento
                                status = "pendente"
                            else:
                                agendamento_id, data, horario, nome, telefone = agendamento
                                email = "Não informado"
                                status = "pendente"
                            
                            # Definir configurações por status
                            status_config = {
                                'pendente': {
                                    'icon': '⏳', 
                                    'card_class': 'card-pendente',
                                    'badge_class': 'badge-pendente',
                                    'text': 'Pendente',
                                    'actions': ['confirm', 'reject']
                                },
                                'confirmado': {
                                    'icon': '✅', 
                                    'card_class': 'card-confirmado',
                                    'badge_class': 'badge-confirmado',
                                    'text': 'Confirmado',
                                    'actions': ['attend', 'cancel']
                                },
                                'atendido': {
                                    'icon': '🎉', 
                                    'card_class': 'card-atendido',
                                    'badge_class': 'badge-atendido',
                                    'text': 'Atendido',
                                    'actions': ['delete']
                                },
                                'cancelado': {
                                    'icon': '❌', 
                                    'card_class': 'card-cancelado',
                                    'badge_class': 'badge-cancelado',
                                    'text': 'Cancelado',
                                    'actions': ['delete']
                                }
                            }
                            
                            config = status_config.get(status, status_config['pendente'])
                            
                            # Card super compacto
                            col_info, col_actions = st.columns([5, 1])
                            
                            with col_info:
                                st.markdown(f"""
                                <div class="card-compacto {config['card_class']}">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div class="nome-compacto">
                                            {config['icon']} {nome}
                                        </div>
                                        <div class="horario-destaque">
                                            🕐 {horario}
                                        </div>
                                    </div>
                                    <div class="info-compacta">
                                        📱 {telefone} | 📧 {email if email else 'Não informado'}
                                    </div>
                                    <div>
                                        <span class="status-badge {config['badge_class']}">{config['text']}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_actions:
                                # Ações baseadas no status
                                if 'confirm' in config['actions']:
                                    if st.button("✅", key=f"confirm_{agendamento_id}", help="Confirmar", use_container_width=True):
                                        atualizar_status_agendamento(agendamento_id, 'confirmado')
                                        st.success(f"✅ {nome} confirmado!")
                                        st.rerun()
                                
                                if 'reject' in config['actions']:
                                    if st.button("❌", key=f"reject_{agendamento_id}", help="Recusar", use_container_width=True):
                                        atualizar_status_agendamento(agendamento_id, 'cancelado')
                                        st.success(f"❌ {nome} recusado!")
                                        st.rerun()
                                
                                if 'attend' in config['actions']:
                                    if st.button("🎉", key=f"attend_{agendamento_id}", help="Atender", use_container_width=True):
                                        atualizar_status_agendamento(agendamento_id, 'atendido')
                                        st.success(f"🎉 {nome} atendido!")
                                        st.rerun()
                                
                                if 'cancel' in config['actions']:
                                    if st.button("❌", key=f"cancel_{agendamento_id}", help="Cancelar", use_container_width=True):
                                        atualizar_status_agendamento(agendamento_id, 'cancelado')
                                        st.success(f"❌ {nome} cancelado!")
                                        st.rerun()
                                
                                if 'delete' in config['actions']:
                                    if st.button("🗑️", key=f"delete_{agendamento_id}", help="Excluir", use_container_width=True):
                                        if st.session_state.get(f"confirm_delete_{agendamento_id}", False):
                                            deletar_agendamento(agendamento_id)
                                            st.success(f"🗑️ {nome} excluído!")
                                            st.rerun()
                                        else:
                                            st.session_state[f"confirm_delete_{agendamento_id}"] = True
                                            st.warning("⚠️ Clique novamente")
                
                else:
                    if st.session_state.dia_selecionado:
                        st.info("📅 Nenhum agendamento encontrado para o filtro selecionado.")
                    else:
                        st.info("📅 Nenhum agendamento encontrado.")
            
            else:
                # Mensagem quando não há agendamentos
                st.markdown("""
                <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 12px; padding: 2rem; text-align: center; margin: 2rem 0;">
                    <h3 style="color: #1d4ed8; margin-bottom: 1rem;">📅 Nenhum agendamento encontrado</h3>
                    <p style="color: #1e40af; margin-bottom: 1.5rem;">
                        Os agendamentos aparecerão aqui conforme forem sendo realizados pelos clientes.
                    </p>
                    <p style="color: #64748b; font-size: 0.9rem;">
                        💡 <strong>Dica:</strong> Compartilhe o link do sistema com seus clientes para começar a receber agendamentos!
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        elif opcao == "💾 Backup & Restauração":
            
            # Informações gerais
            st.info("""
            🛡️ **Centro de Backup e Restauração**
            
            Mantenha seus dados sempre seguros com nosso sistema completo de backup e restauração.
            Exporte seus agendamentos, configure backups automáticos e restaure dados quando necessário.
            """)
            
            # Separar em tabs para melhor organização
            tab_export, tab_import, tab_auto = st.tabs(["📤 Exportar Dados", "📥 Importar Dados", "🔄 Backup Automático"])

            # ============================================
            # ABA 1: EXPORTAR DADOS
            # ============================================
            
            with tab_export:
                st.subheader("📤 Exportar Agendamentos")
                
                col_info, col_action = st.columns([2, 1])
                
                with col_info:
                    st.markdown("""
                    **📋 O que será exportado:**
                    • Todos os agendamentos (confirmados, pendentes, atendidos, cancelados)
                    • Informações completas: nome, telefone, email, data, horário, status
                    • Formato CSV compatível com Excel e outras planilhas
                    • Dados organizados cronologicamente
                    """)
                
                with col_action:
                    if st.button("📥 Gerar Backup CSV", 
                                type="primary",
                                use_container_width=True,
                                help="Baixar todos os agendamentos em formato CSV"):
                        
                        csv_data = exportar_agendamentos_csv()
                        
                        if csv_data:
                            # Gerar nome do arquivo com data atual
                            from datetime import datetime
                            data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nome_arquivo = f"agendamentos_backup_{data_atual}.csv"
                            
                            # Estatísticas
                            total_agendamentos = len(buscar_agendamentos())
                            tamanho_kb = len(csv_data.encode('utf-8')) / 1024
                            
                            st.success(f"✅ Backup gerado com sucesso!")
                            
                            # Métricas do backup
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Total de Registros", total_agendamentos)
                            with col2:
                                st.metric("📏 Tamanho", f"{tamanho_kb:.1f} KB")
                            with col3:
                                st.metric("📅 Data/Hora", datetime.now().strftime("%d/%m %H:%M"))
                            
                            # Botão de download
                            st.download_button(
                                label="⬇️ Baixar Arquivo de Backup",
                                data=csv_data,
                                file_name=nome_arquivo,
                                mime="text/csv",
                                use_container_width=True,
                                type="primary"
                            )
                            
                            st.info(f"💾 **Arquivo:** {nome_arquivo}")
                            
                        else:
                            st.warning("⚠️ Nenhum agendamento encontrado para exportar")
                
                # Instruções
                with st.expander("ℹ️ Como usar o arquivo de backup"):
                    st.markdown("""
                    **📖 Instruções de uso:**
                    
                    1. **💾 Salvar arquivo:** Guarde o arquivo CSV em local seguro
                    2. **📁 Organização:** Recomendamos criar uma pasta "Backups_Agendamento"
                    3. **📊 Abrir no Excel:** O arquivo abre diretamente no Excel ou Google Sheets
                    4. **🔄 Restaurar:** Use a aba "Importar Dados" para restaurar os agendamentos
                    5. **⏰ Frequência:** Recomendamos backup semanal ou antes de mudanças importantes
                    
                    **🔒 Segurança:**
                    • O arquivo contém dados pessoais dos clientes
                    • Mantenha-o em local seguro e protegido
                    • Não compartilhe sem necessidade
                    """)
            
            # ============================================
            # ABA 2: IMPORTAR DADOS
            # ============================================
            
            with tab_import:
                st.subheader("📥 Restaurar Agendamentos")
                
                col_info_import, col_upload = st.columns([2, 3])

                with col_info_import:
                    st.markdown("""
                    **📂 Restaurar Backup:**
                    
                    • Importe um arquivo CSV exportado anteriormente
                    • Formato deve ser idêntico ao exportado
                    • Duplicatas serão ignoradas automaticamente
                    • Colunas obrigatórias: ID, Data, Horário, Nome, Telefone
                    """)
                    
                    st.warning("""
                    ⚠️ **Atenção:**
                    Esta operação irá adicionar os agendamentos do arquivo ao sistema atual.
                    Agendamentos duplicados serão ignorados automaticamente.
                    """)

                with col_upload:
                    uploaded_file = st.file_uploader(
                        "Escolha um arquivo CSV de backup:",
                        type=['csv'],
                        help="Selecione um arquivo CSV exportado anteriormente do sistema"
                    )
                    
                    if uploaded_file is not None:
                        # Mostrar informações do arquivo
                        file_size = uploaded_file.size
                        st.info(f"📄 **Arquivo:** {uploaded_file.name} ({file_size} bytes)")
                        
                        if st.button("📤 Restaurar Dados do Backup", 
                                    type="primary", 
                                    use_container_width=True):
                            
                            # Ler conteúdo do arquivo
                            csv_content = uploaded_file.getvalue().decode('utf-8')
                            
                            # Importar dados
                            resultado = importar_agendamentos_csv(csv_content)
                            
                            if resultado['sucesso']:
                                st.success("🎉 Restauração realizada com sucesso!")
                                
                                # Mostrar estatísticas sem colunas aninhadas
                                if resultado['importados'] > 0:
                                    st.info(f"✅ **{resultado['importados']}** agendamento(s) restaurado(s)")
                                
                                if resultado['duplicados'] > 0:
                                    st.warning(f"⚠️ **{resultado['duplicados']}** registro(s) já existiam (ignorados)")
                                
                                if resultado['erros'] > 0:
                                    st.error(f"❌ **{resultado['erros']}** registro(s) com erro nos dados")
                                
                                # Atualizar a página para mostrar os novos dados
                                if resultado['importados'] > 0:
                                     st.rerun()
                                    
                            else:
                                st.error(f"❌ Erro na restauração: {resultado.get('erro', 'Erro desconhecido')}")
                
                # Formato esperado
                with st.expander("📋 Formato esperado do arquivo CSV"):
                    st.code("""
        ID,Data,Horário,Nome,Telefone,Email,Status
        1,2024-12-20,09:00,João Silva,(11) 99999-9999,joao@email.com,confirmado
        2,2024-12-20,10:00,Maria Santos,(11) 88888-8888,maria@email.com,pendente
        3,2024-12-21,14:00,Pedro Costa,(11) 77777-7777,pedro@email.com,atendido
                    """, language="csv")
                    
                    st.markdown("""
                    **📝 Observações importantes:**
                    - Use exatamente os mesmos cabeçalhos mostrados acima
                    - Formato de data: AAAA-MM-DD (ex: 2024-12-20)
                    - Formato de horário: HH:MM (ex: 09:00)
                    - Status válidos: pendente, confirmado, atendido, cancelado
                    - Email é opcional (pode ficar em branco)
                    - ID será ignorado (sistema gera automaticamente)
                    """)
            
            # ============================================
            # ABA 3: BACKUP AUTOMÁTICO (placeholder)
            # ============================================
            
            with tab_auto:
                interface_backup_email()

            st.markdown('</div>', unsafe_allow_html=True)

        elif opcao == "🔗 Integrações":
            
            st.markdown("""
            <div class="main-card">
                <div class="card-header">
                    <h2 class="card-title">🔗 Integrações Externas</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ========================================
            # SEÇÃO TODOIST
            # ========================================
            
            st.subheader("📝 Integração com Todoist")
            
            todoist_ativo = st.checkbox(
                "Ativar sincronização com Todoist",
                value=obter_configuracao("todoist_ativo", False),
                help="Cria tarefas automaticamente no Todoist para cada agendamento confirmado"
            )
            
            if todoist_ativo:
                st.success("✅ Integração com Todoist ativada")
                
                # Tabs para organizar melhor
                tab_config, tab_teste, tab_opcoes = st.tabs(["🔑 Configuração", "🧪 Teste", "⚙️ Opções"])
                
                with tab_config:
                    st.markdown("**🔑 Token da API Todoist**")
                    
                    todoist_token = st.text_input(
                        "Digite seu token:",
                        value=obter_configuracao("todoist_token", ""),
                        type="password",
                        placeholder="Token de 40 caracteres do Todoist",
                        help="Obtenha em: https://todoist.com/app/settings/integrations"
                    )
                    
                    # Instruções
                    with st.expander("📖 Como obter o token do Todoist"):
                        instrucoes = gerar_instrucoes_todoist()
                        st.markdown(instrucoes)
                    
                    # Link direto
                    st.markdown("**🔗 Links úteis:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.link_button("🔑 Obter Token", "https://todoist.com/app/settings/integrations")
                    with col2:
                        st.link_button("📱 Baixar App", "https://todoist.com/downloads")
                
                with tab_teste:
                    st.markdown("**🧪 Testar Integração**")
                    
                    # Teste de conexão
                    if st.button("🔍 Testar Conexão", type="primary", use_container_width=True):
                        if todoist_token:
                            # Salvar temporariamente para teste
                            salvar_configuracao("todoist_token", todoist_token)
                            salvar_configuracao("todoist_ativo", True)
                            
                            with st.spinner("Testando conexão com Todoist..."):
                                sucesso, mensagem = testar_conexao_todoist()
                                
                            if sucesso:
                                st.success(mensagem)
                                
                                # Verificar projeto
                                projeto_id = obter_projeto_agendamentos()
                                if projeto_id:
                                    st.info(f"📁 Projeto 'Agendamentos' ID: {projeto_id}")
                                
                            else:
                                st.error(mensagem)
                                salvar_configuracao("todoist_ativo", False)
                        else:
                            st.warning("⚠️ Digite o token primeiro")
                    
                    # Criar tarefa de teste
                    st.markdown("---")
                    if st.button("📝 Criar Tarefa de Teste", type="secondary", use_container_width=True):
                        if todoist_ativo and todoist_token:
                            salvar_configuracao("todoist_ativo", todoist_ativo)
                            salvar_configuracao("todoist_token", todoist_token)
                            
                            with st.spinner("Criando tarefa de teste..."):
                                from datetime import datetime
                                agora = datetime.now()
                                
                                sucesso = criar_tarefa_todoist(
                                    9999,  # ID de teste
                                    "TESTE - Sistema Agendamento",
                                    "(00) 0000-0000", 
                                    "teste@exemplo.com",
                                    agora.strftime("%Y-%m-%d"),
                                    agora.strftime("%H:%M")
                                )
                                
                                if sucesso:
                                    st.success("✅ Tarefa criada! Verifique seu Todoist.")
                                else:
                                    st.error("❌ Erro ao criar tarefa.")
                        else:
                            st.warning("⚠️ Configure a integração primeiro")
                
                with tab_opcoes:
                    st.markdown("**⚙️ Configurações Avançadas**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        criar_para_pendentes = st.checkbox(
                            "Criar tarefas para agendamentos pendentes",
                            value=obter_configuracao("todoist_incluir_pendentes", True),
                            help="Se desmarcado, só cria para confirmados"
                        )
                        
                        marcar_concluido = st.checkbox(
                            "Marcar como concluído quando atendido",
                            value=obter_configuracao("todoist_marcar_concluido", True),
                            help="Marca tarefa como concluída automaticamente"
                        )
                    
                    with col2:
                        remover_cancelados = st.checkbox(
                            "Remover tarefas canceladas",
                            value=obter_configuracao("todoist_remover_cancelados", True),
                            help="Remove tarefa quando agendamento é cancelado"
                        )
                        
                        # Estatísticas
                        total_tarefas = 0
                        try:
                            conn = conectar()
                            c = conn.cursor()
                            c.execute("SELECT COUNT(*) FROM configuracoes WHERE chave LIKE 'todoist_task_%'")
                            total_tarefas = c.fetchone()[0]
                            conn.close()
                        except:
                            total_tarefas = 0
                        
                        st.metric("📊 Tarefas Criadas", total_tarefas)

                    st.markdown("**📁 Configuração do Projeto**")
                    
                    nome_projeto_atual = obter_configuracao("todoist_nome_projeto", "📅 Agendamentos")
                    
                    col_proj1, col_proj2 = st.columns(2)
                    
                    with col_proj1:
                        nome_projeto_config = st.text_input(
                            "Nome do projeto no Todoist:",
                            value=nome_projeto_atual,
                            placeholder="📅 Agendamentos",
                            help="Nome do projeto onde as tarefas serão criadas"
                        )
                    
                    with col_proj2:
                        # Mostrar projeto atual se configurado
                        projeto_id_atual = obter_configuracao("todoist_projeto_id", "")
                        if projeto_id_atual:
                            st.info(f"📁 **Projeto atual:**\nID: {projeto_id_atual}")
                        else:
                            st.info("📁 **Projeto:** Será criado automaticamente")
                    
                    # Botão para recriar projeto
                    if st.button("🔄 Atualizar/Recriar Projeto", help="Força a busca/criação do projeto"):
                        if nome_projeto_config.strip():
                            # Salvar novo nome
                            salvar_configuracao("todoist_nome_projeto", nome_projeto_config.strip())
                            
                            # Limpar ID antigo para forçar nova busca
                            conn = conectar()
                            c = conn.cursor()
                            c.execute("DELETE FROM configuracoes WHERE chave = 'todoist_projeto_id'")
                            conn.commit()
                            conn.close()
                            
                            # Buscar/criar projeto
                            with st.spinner("Procurando/criando projeto..."):
                                projeto_id = obter_projeto_agendamentos()
                                
                            if projeto_id:
                                st.success(f"✅ Projeto configurado: {nome_projeto_config} (ID: {projeto_id})")
                            else:
                                st.error("❌ Erro ao configurar projeto")
                            
                            st.rerun()
                        else:
                            st.warning("⚠️ Digite um nome para o projeto")
                
                # Salvar configurações
                st.markdown("---")
                if st.button("💾 Salvar Configurações Todoist", type="primary", use_container_width=True):
                    salvar_configuracao("todoist_ativo", todoist_ativo)
                    if todoist_ativo:
                        salvar_configuracao("todoist_token", todoist_token)
                        salvar_configuracao("todoist_incluir_pendentes", criar_para_pendentes)
                        salvar_configuracao("todoist_marcar_concluido", marcar_concluido)
                        salvar_configuracao("todoist_remover_cancelados", remover_cancelados)
                        salvar_configuracao("todoist_nome_projeto", nome_projeto_config.strip() if nome_projeto_config.strip() else "📅 Agendamentos")                    
                    st.success("✅ Configurações do Todoist salvas!")
                    
                    if todoist_ativo and todoist_token:
                        st.info("🎯 **Todoist configurado!** Novos agendamentos criarão tarefas automaticamente.")
                    
                    st.rerun()
            
            else:
                st.info("💡 A integração com Todoist transforma cada agendamento em uma tarefa na sua lista de afazeres")
                
                # Benefícios
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **🎯 Benefícios:**
                    • 📱 **Notificações** no celular
                    • 🔄 **Sincronização** automática  
                    • ✅ **Marcação** de concluídas
                    • 📊 **Organização** por projeto
                    """)
                
                with col2:
                    st.markdown("""
                    **📱 Compatibilidade:**
                    • iPhone e Android
                    • Windows e Mac
                    • Navegador web
                    • Conta gratuita OK
                    """)
            
            # ========================================
            # FUTURAS INTEGRAÇÕES
            # ========================================
            
            st.markdown("---")
            st.subheader("🔮 Próximas Integrações")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **📅 Google Calendar**
                🔧 Em desenvolvimento
                
                • Eventos automáticos
                • Sincronização bidirecional
                """)
            
            with col2:
                st.markdown("""
                **💬 WhatsApp Business**
                🔧 Planejado
                
                • Mensagens automáticas
                • Confirmações por WhatsApp
                """)
            
            with col3:
                st.markdown("""
                **📊 Notion**
                🔧 Planejado
                
                • Base de dados de clientes
                • Relatórios automatizados
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # INTERFACE DO CLIENTE
    # Obter configurações dinâmicas atualizadas
    nome_profissional = obter_configuracao("nome_profissional", "Dr. João Silva")
    especialidade = obter_configuracao("especialidade", "Clínico Geral")
    nome_clinica = obter_configuracao("nome_clinica", "Clínica São Lucas")
    telefone_contato = obter_configuracao("telefone_contato", "(11) 3333-4444")
    whatsapp = obter_configuracao("whatsapp", "(11) 99999-9999")
    
    # Endereço completo
    endereco_rua = obter_configuracao("endereco_rua", "Rua das Flores, 123")
    endereco_bairro = obter_configuracao("endereco_bairro", "Centro")
    endereco_cidade = obter_configuracao("endereco_cidade", "São Paulo - SP")
    endereco_completo = f"{endereco_rua}, {endereco_bairro}, {endereco_cidade}"
    
    instrucoes_chegada = obter_configuracao("instrucoes_chegada", "Favor chegar 10 minutos antes do horário agendado.")

    st.markdown(f"""
    <div class="main-header">
        <h5>{nome_clinica}</h5>
        <p>{nome_profissional} - {especialidade}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        tab_agendar, tab_cancelar = st.tabs(["📅 Agendar Horário", "❌ Cancelar Agendamento"])
        
        with tab_agendar:
            # Obter configurações dinâmicas para agendamento
            hoje = datetime.today()
            dias_futuros_config = obter_configuracao("dias_futuros", 30)
            antecedencia_minima = obter_configuracao("antecedencia_minima", 2)
            horario_inicio = obter_configuracao("horario_inicio", "09:00")
            horario_fim = obter_configuracao("horario_fim", "18:00")
            intervalo_consultas = obter_configuracao("intervalo_consultas", 60)  # AGORA USA A CONFIGURAÇÃO!
            
            dias_uteis = obter_dias_uteis()
            datas_bloqueadas = obter_datas_bloqueadas()
            datas_bloqueadas_dt = [datetime.strptime(d, "%Y-%m-%d").date() for d in datas_bloqueadas]
            
            agora = datetime.now()
            data_limite_antecedencia = agora + timedelta(hours=antecedencia_minima)
            
            datas_validas = []
            for i in range(1, dias_futuros_config + 1):
                data = hoje + timedelta(days=i)
                dia_semana = data.strftime("%A")
                data_str = data.strftime("%Y-%m-%d")  # Formato para verificar períodos
                
                # Verificar todas as condições:
                # 1. Dia da semana permitido
                # 2. Não está na lista de bloqueios individuais  
                # 3. Não está em nenhum período bloqueado
                # 4. Respeita antecedência mínima
                if (dia_semana in dias_uteis and 
                    data.date() not in datas_bloqueadas_dt and 
                    not data_em_periodo_bloqueado(data_str) and  # NOVA VERIFICAÇÃO!
                    data.date() > data_limite_antecedencia.date()):
                    datas_validas.append(data.date())
            
            if not datas_validas:
                st.warning("⚠️ Nenhuma data disponível no momento.")
            else:
                st.markdown('<h4 style="font-size: 18px;">📋 Dados do Cliente</h4>', unsafe_allow_html=True)
                
                nome = st.text_input("Nome completo *", placeholder="Digite seu nome")
                
                telefone = st.text_input("Telefone *", placeholder="(11) 99999-9999")
                
                email = st.text_input("E-mail *", placeholder="seu@email.com")
                                                              
                # Inicializar estado do calendário
                if 'data_selecionada_cal' not in st.session_state:
                    st.session_state.data_selecionada_cal = datas_validas[0] if datas_validas else None
                if 'mes_atual' not in st.session_state:
                    hoje = datetime.now()
                    st.session_state.mes_atual = hoje.month
                    st.session_state.ano_atual = hoje.year

                # Criar lista de meses disponíveis
                meses_disponiveis = {}
                for data in datas_validas:
                    chave_mes = f"{data.year}-{data.month:02d}"
                    nome_mes = f"{calendar.month_name[data.month]} {data.year}"
                    if chave_mes not in meses_disponiveis:
                        meses_disponiveis[chave_mes] = nome_mes

                # Navegação em linha única: Data [◀️] Mês Ano [▶️]
                col_data, col_prev, col_mes, col_next = st.columns([1, 1, 3, 1])

                with col_data:
                    st.markdown('<p style="font-size: 18px; font-weight: 600; margin: 0; padding-top: 0.3rem;">📅 Data</p>', unsafe_allow_html=True)

                with col_prev:
                    if st.button("◀️", key="prev_month", help="Mês anterior", use_container_width=True):
                        chave_atual = f"{st.session_state.ano_atual}-{st.session_state.mes_atual:02d}"
                        chaves_ordenadas = sorted(meses_disponiveis.keys())
                        try:
                            indice_atual = chaves_ordenadas.index(chave_atual)
                            if indice_atual > 0:
                                nova_chave = chaves_ordenadas[indice_atual - 1]
                                ano, mes = nova_chave.split("-")
                                st.session_state.ano_atual = int(ano)
                                st.session_state.mes_atual = int(mes)
                                st.rerun()
                        except ValueError:
                            pass

                with col_mes:
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 1.1rem; font-weight: 600; color: #1f2937; padding-top: 0.3rem; margin: 0;">
                       {calendar.month_name[st.session_state.mes_atual]} {st.session_state.ano_atual}
                    </div>
                    """, unsafe_allow_html=True)

                with col_next:
                    if st.button("▶️", key="next_month", help="Próximo mês", use_container_width=True):
                        chave_atual = f"{st.session_state.ano_atual}-{st.session_state.mes_atual:02d}"
                        chaves_ordenadas = sorted(meses_disponiveis.keys())
                        try:
                            indice_atual = chaves_ordenadas.index(chave_atual)
                            if indice_atual < len(chaves_ordenadas) - 1:
                                nova_chave = chaves_ordenadas[indice_atual + 1]
                                ano, mes = nova_chave.split("-")
                                st.session_state.ano_atual = int(ano)
                                st.session_state.mes_atual = int(mes)
                                st.rerun()
                        except ValueError:
                            pass

                # Forçar colunas a não empilhar usando CSS
                st.markdown("""
                <style>
                /* Forçar TODAS as colunas do Streamlit a ficarem lado a lado no calendário */
                div[data-testid="stHorizontalBlock"] {
                    display: flex !important;
                    flex-direction: row !important;
                    flex-wrap: nowrap !important;
                    gap: 2px !important;
                    width: 100% !important;
                }

                div[data-testid="stHorizontalBlock"] > div {
                    flex: 1 1 14.28% !important;
                    max-width: 14.28% !important;
                    min-width: 0 !important;
                    padding: 0 1px !important;
                }

                /* Forçar também pela classe */
                .row-widget.stColumns {
                    display: flex !important;
                    flex-direction: row !important;
                    flex-wrap: nowrap !important;
                    gap: 2px !important;
                    width: 100% !important;
                }

                .row-widget.stColumns > div {
                    flex: 1 1 14.28% !important;
                    max-width: 14.28% !important;
                    min-width: 0 !important;
                    padding: 0 1px !important;
                }

                /* Prevenir quebra em qualquer nível */
                div[data-testid="column"] {
                    flex: 1 1 14.28% !important;
                    max-width: 14.28% !important;
                    min-width: 0 !important;
                }

                /* Container do calendário */
                .calendar-container {
                    width: 100%;
                    max-width: 400px;
                    margin: 1rem auto;
                    background: white;
                    border-radius: 12px;
                    padding: 0.5rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                /* Ajustar botões para serem menores em mobile */
                .stButton > button {
                    width: 100% !important;
                    padding: 0.25rem !important;
                    min-height: 2rem !important;
                    font-size: 0.8rem !important;
                    margin: 1px 0 !important;
                }

                /* Em telas muito pequenas, ajustar ainda mais */
                @media (max-width: 400px) {
                    .stButton > button {
                        font-size: 0.75rem !important;
                        padding: 0.2rem !important;
                        min-height: 1.8rem !important;
                    }
                    
                    .calendar-container {
                        padding: 0.3rem;
                    }
                }

                /* Forçar layout horizontal mesmo em mobile */
                @media (max-width: 768px) {
                    div[data-testid="stHorizontalBlock"] {
                        display: flex !important;
                        flex-direction: row !important;
                    }
                    
                    div[data-testid="column"] {
                        flex: 1 1 14.28% !important;
                        max-width: 14.28% !important;
                    }
                }
                </style>
                """, unsafe_allow_html=True)

                # Container do calendário
                st.markdown('<div class="calendar-container">', unsafe_allow_html=True)

                # Gerar calendário do mês
                cal = calendar.monthcalendar(st.session_state.ano_atual, st.session_state.mes_atual)

                # Dias da semana - bem curtos para mobile
                st.markdown("""
                <div style="display: flex; gap: 2px; margin-bottom: 6px;">
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">SEG</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">TER</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">QUA</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">QUI</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">SEX</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">SAB</div>
                    <div style="flex: 1; text-align: center; font-size: 0.8rem; font-weight: 700; color: #374151; background: #f1f5f9; padding: 6px 3px; border-radius: 4px; border: 1px solid #e2e8f0;">DOM</div>
                </div>
                """, unsafe_allow_html=True)

                # Gerar cada semana do calendário
                for semana_idx, semana in enumerate(cal):
                    cols = st.columns(7)
                    for dia_idx, dia in enumerate(semana):
                        with cols[dia_idx]:
                            if dia == 0:
                                # Célula vazia
                                st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
                            else:
                                # Verificar se data está disponível
                                try:
                                    data_atual = datetime(st.session_state.ano_atual, st.session_state.mes_atual, dia).date()
                                    data_disponivel = data_atual in datas_validas
                                    data_selecionada_atual = st.session_state.data_selecionada_cal == data_atual
                                    
                                    if data_disponivel:
                                        # Data disponível - botão clicável
                                        button_type = "primary" if data_selecionada_atual else "secondary"
                                        
                                        if st.button(
                                            str(dia),
                                            key=f"cal_{semana_idx}_{dia_idx}_{dia}",
                                            type=button_type,
                                            use_container_width=True
                                        ):
                                            st.session_state.data_selecionada_cal = data_atual
                                            st.rerun()
                                    else:
                                        # Data indisponível
                                        st.markdown(f"""
                                        <div style="
                                            height: 2rem; 
                                            display: flex; 
                                            align-items: center; 
                                            justify-content: center;
                                            color: #cbd5e1;
                                            font-size: 0.8rem;
                                        ">{dia}</div>
                                        """, unsafe_allow_html=True)
                                        
                                except ValueError:
                                    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # Mostrar data selecionada
                if st.session_state.data_selecionada_cal:
                    data_formatada = st.session_state.data_selecionada_cal.strftime("%A, %d de %B de %Y").replace("Monday", "Segunda-feira")\
                        .replace("Tuesday", "Terça-feira").replace("Wednesday", "Quarta-feira")\
                        .replace("Thursday", "Quinta-feira").replace("Friday", "Sexta-feira")\
                        .replace("Saturday", "Sábado").replace("Sunday", "Domingo")\
                        .replace("January", "Janeiro").replace("February", "Fevereiro").replace("March", "Março")\
                        .replace("April", "Abril").replace("May", "Maio").replace("June", "Junho")\
                        .replace("July", "Julho").replace("August", "Agosto").replace("September", "Setembro")\
                        .replace("October", "Outubro").replace("November", "Novembro").replace("December", "Dezembro")
                    
                    st.success(f"📅 **Data selecionada:** {data_formatada}")

                # Definir data selecionada para o resto do código
                data_selecionada = st.session_state.data_selecionada_cal
                
                if data_selecionada:
                    st.markdown('<h4 style="font-size: 18px;">⏰ Horários Disponíveis</h4>', unsafe_allow_html=True)
                    
                    data_str = data_selecionada.strftime("%Y-%m-%d")
                    
                    # Gerar horários baseados nas configurações ATUALIZADAS
                    try:
                        hora_inicio = datetime.strptime(horario_inicio, "%H:%M").time()
                        hora_fim = datetime.strptime(horario_fim, "%H:%M").time()
                        
                        inicio_min = hora_inicio.hour * 60 + hora_inicio.minute
                        fim_min = hora_fim.hour * 60 + hora_fim.minute
                        
                        horarios_possiveis = []
                        horario_atual = inicio_min
                        
                        # USAR O INTERVALO CONFIGURADO!
                        while horario_atual + intervalo_consultas <= fim_min:
                            h = horario_atual // 60
                            m = horario_atual % 60
                            horarios_possiveis.append(f"{str(h).zfill(2)}:{str(m).zfill(2)}")
                            horario_atual += intervalo_consultas
                            
                    except:
                        horarios_possiveis = [f"{str(h).zfill(2)}:00" for h in range(9, 18)]
                    
                    horarios_disponiveis = [h for h in horarios_possiveis if horario_disponivel(data_str, h)]
                    
                    if horarios_disponiveis:
                        horario = st.selectbox("Escolha o horário:", horarios_disponiveis)
                        
                        if horario and nome and telefone and email:
                            email_valido = "@" in email and "." in email.split("@")[-1]
                            
                            if not email_valido:
                                st.warning("⚠️ Digite um e-mail válido.")
                            else:
                                st.markdown(f"""
                                <div class="appointment-summary">
                                    <h3>📋 Resumo do Agendamento</h3>
                                    <div class="summary-item">
                                        <span>👤 Nome:</span>
                                        <strong>{nome}</strong>
                                    </div>
                                    <div class="summary-item">
                                        <span>📱 Telefone:</span>
                                        <strong>{telefone}</strong>
                                    </div>
                                    <div class="summary-item">
                                        <span>📧 E-mail:</span>
                                        <strong>{email}</strong>
                                    </div>
                                    <div class="summary-item">
                                        <span>📅 Data:</span>
                                        <strong>{data_selecionada.strftime('%d/%m/%Y')}</strong>
                                    </div>
                                    <div class="summary-item">
                                        <span>⏰ Horário:</span>
                                        <strong>{horario}</strong>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Mostrar instruções se existirem
                                if instrucoes_chegada:
                                    st.markdown(f"""
                                    <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
                                        <strong>📝 Instruções importantes:</strong><br>
                                        {instrucoes_chegada}
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                verificacao_ativa = obter_configuracao("verificacao_codigo_ativa", False)

                                if verificacao_ativa and obter_configuracao("envio_automatico", False):
                                    # Sistema com verificação
                                    
                                    # Gerenciar estado da verificação
                                    if 'codigo_enviado' not in st.session_state:
                                        st.session_state.codigo_enviado = False
                                    if 'email_verificacao' not in st.session_state:
                                        st.session_state.email_verificacao = ""
                                    if 'dados_agendamento' not in st.session_state:
                                        st.session_state.dados_agendamento = {}
                                    
                                    if not st.session_state.codigo_enviado:
                                        # PASSO 1: Enviar código
                                        st.markdown("""
                                        <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                                            <h4 style="color: #0369a1; margin: 0 0 0.5rem 0;">🔐 Verificação de Segurança</h4>
                                            <p style="color: #0c4a6e; margin: 0;">Vamos enviar um código para confirmar seu email.</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if st.button("📧 Enviar Código de Verificação", type="primary", use_container_width=True):
                                            # Validar dados primeiro
                                            if not nome or not telefone or not email:
                                                st.error("❌ Preencha todos os campos obrigatórios!")
                                            elif "@" not in email or "." not in email.split("@")[-1]:
                                                st.error("❌ Digite um email válido!")
                                            else:
                                                with st.spinner("Enviando código..."):
                                                    # Gerar e enviar código
                                                    codigo = gerar_codigo_verificacao()
                                                    salvar_codigo_verificacao(email, codigo)
                                                    
                                                    if enviar_codigo_verificacao(email, nome, codigo):
                                                        st.success(f"✅ Código enviado para {email}")
                                                        st.info("📧 Verifique sua caixa de entrada (pode estar no spam)")
                                                        
                                                        # Salvar dados temporariamente
                                                        st.session_state.codigo_enviado = True
                                                        st.session_state.email_verificacao = email
                                                        st.session_state.dados_agendamento = {
                                                            'nome': nome,
                                                            'telefone': telefone,
                                                            'email': email,
                                                            'data': data_str,
                                                            'horario': horario
                                                        }
                                                        time.sleep(1)  # Dar tempo para ler a mensagem
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Erro ao enviar código. Verifique o email e tente novamente.")
                                    
                                    else:
                                        # PASSO 2: Verificar código
                                        st.markdown("""
                                        <div style="background: #f0fdf4; border: 1px solid #10b981; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                                            <h4 style="color: #047857; margin: 0 0 0.5rem 0;">✅ Código Enviado!</h4>
                                            <p style="color: #064e3b; margin: 0;">Enviamos um código de 4 dígitos para:</p>
                                            <p style="color: #047857; font-weight: bold; margin: 0.5rem 0 0 0;">📧 {}</p>
                                        </div>
                                        """.format(st.session_state.email_verificacao), unsafe_allow_html=True)
                                        
                                        # Verificar se mudou o email
                                        if email != st.session_state.email_verificacao:
                                            st.warning(f"⚠️ Você alterou o email. O código foi enviado para: {st.session_state.email_verificacao}")
                                            if st.button("📧 Usar novo email e reenviar código", use_container_width=True):
                                                st.session_state.codigo_enviado = False
                                                st.session_state.email_verificacao = ""
                                                st.rerun()
                                            st.markdown("---")
                                        
                                        # Campo para código
                                        codigo_digitado = st.text_input(
                                            "Digite o código de 4 dígitos:",
                                            max_chars=4,
                                            placeholder="0000",
                                            help="Código enviado para seu email"
                                        )
                                        
                                        # Informação sobre validade
                                        st.caption("⏱️ Código válido por 30 minutos • 5 tentativas disponíveis")
                                        
                                        # Container para ações
                                        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
                                        
                                        # Botão principal de confirmar
                                        if st.button("✅ Confirmar Agendamento", type="primary", use_container_width=True, disabled=(len(codigo_digitado) != 4)):
                                            if len(codigo_digitado) == 4:
                                                with st.spinner("Verificando código..."):
                                                    # Verificar código
                                                    valido, mensagem = verificar_codigo(st.session_state.email_verificacao, codigo_digitado)
                                                    
                                                    if valido:
                                                        # Código correto - fazer agendamento
                                                        dados = st.session_state.dados_agendamento
                                                        conn = conectar()
                                                        c = conn.cursor()
                                                        c.execute("SELECT COUNT(*) FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=? AND status IN ('pendente', 'confirmado')", (dados['nome'], dados['telefone'], dados['data']))

                                                        if c.fetchone()[0] > 0:
                                                            st.error("❌ Você já tem agendamento para esta data!")
                                                            conn.close()
                                                        else:
                                                            conn.close()                                                        
                                                            try:
                                                                status_inicial = adicionar_agendamento(
                                                                    dados['nome'], 
                                                                    dados['telefone'], 
                                                                    dados['email'], 
                                                                    dados['data'], 
                                                                    dados['horario']
                                                                )
                                                                
                                                                # Limpar estado
                                                                st.session_state.codigo_enviado = False
                                                                st.session_state.email_verificacao = ""
                                                                st.session_state.dados_agendamento = {}
                                                                
                                                                # Mensagens de sucesso
                                                                if status_inicial == "confirmado":
                                                                    st.success("✅ Agendamento confirmado com sucesso!")
                                                                else:
                                                                    st.success("✅ Agendamento solicitado! Aguarde confirmação.")
                                                                
                                                                # Resumo do agendamento
                                                                st.markdown(f"""
                                                                <div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 8px; padding: 1.5rem; margin: 1rem 0;">
                                                                    <h3 style="color: #047857; margin: 0 0 1rem 0;">📅 Seu Agendamento</h3>
                                                                    <p style="margin: 0.5rem 0;"><strong>Data:</strong> {data_selecionada.strftime('%d/%m/%Y')}</p>
                                                                    <p style="margin: 0.5rem 0;"><strong>Horário:</strong> {horario}</p>
                                                                    <p style="margin: 0.5rem 0;"><strong>Local:</strong> {nome_clinica}</p>
                                                                    <p style="margin: 0.5rem 0;"><strong>Endereço:</strong> {endereco_completo}</p>
                                                                </div>
                                                                """, unsafe_allow_html=True)
                                                                
                                                                # Informações de contato
                                                                st.markdown(f"""
                                                                <div style="background: #f8f9fa; border-left: 4px solid #0ea5e9; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
                                                                    <strong>📞 Em caso de dúvidas:</strong><br>
                                                                    📱 Telefone: {telefone_contato}<br>
                                                                    💬 WhatsApp: {whatsapp}
                                                                </div>
                                                                """, unsafe_allow_html=True)
                                                                
                                                            except Exception as e:
                                                                st.error(f"❌ Erro ao agendar: {str(e)}")
                                                    else:
                                                        st.error(f"❌ {mensagem}")
                                            else:
                                                st.warning("⚠️ Digite o código de 4 dígitos")
                                        
                                        # Espaçamento
                                        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
                                        
                                        # Ações secundárias em linha única
                                        col1, col2 = st.columns([1, 1])
                                        
                                        
                                        if st.button("🔄 Reenviar Código", use_container_width=True, type="secondary"):
                                            with st.spinner("Enviando novo código..."):
                                                codigo = gerar_codigo_verificacao()
                                                salvar_codigo_verificacao(st.session_state.email_verificacao, codigo)
                                                
                                                if enviar_codigo_verificacao(st.session_state.email_verificacao, nome, codigo):
                                                    st.success("✅ Novo código enviado!")
                                                    st.info("📧 Verifique seu email novamente")
                                                else:
                                                    st.error("❌ Erro ao reenviar código")
                                    
                                    
                                        if st.button("❌ Cancelar", use_container_width=True, type="secondary"):
                                            st.session_state.codigo_enviado = False
                                            st.session_state.email_verificacao = ""
                                            st.session_state.dados_agendamento = {}
                                            st.rerun()
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)

                                else:
                                    # Sistema sem verificação (código original)
                                    if st.button("✅ Confirmar Agendamento"):
                                        # ADICIONAR AQUI (antes do try):
                                        conn = conectar()
                                        c = conn.cursor()
                                        c.execute("SELECT COUNT(*) FROM agendamentos WHERE nome_cliente=? AND telefone=? AND data=? AND status IN ('pendente', 'confirmado')", (nome, telefone, data_str))                                        
                                        if c.fetchone()[0] > 0:
                                            st.error("❌ Você já tem agendamento para esta data!")
                                            conn.close()
                                        else:
                                            conn.close()
                                            try:
                                                status_inicial = adicionar_agendamento(nome, telefone, email, data_str, horario)
                                                
                                                if status_inicial == "confirmado":
                                                    st.success("✅ Agendamento confirmado automaticamente!")
                                                   
                                                else:
                                                    st.success("✅ Agendamento solicitado! Aguarde confirmação.")
                                                    
                                                    
                                                st.info(f"💡 Seu agendamento: {data_selecionada.strftime('%d/%m/%Y')} às {horario}")
                                                
                                                
                                                # Mostrar informações de contato
                                                st.markdown(f"""
                                                <div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 1rem; margin: 1rem 0; border-radius: 8px;">
                                                    <strong>📞 Em caso de dúvidas:</strong><br>
                                                    📱 Telefone: {telefone_contato}<br>
                                                    💬 WhatsApp: {whatsapp}
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                            except Exception as e:
                                                st.error(f"❌ Erro ao agendar: {str(e)}")
                        
                        elif nome or telefone or email:
                            campos_faltando = []
                            if not nome: campos_faltando.append("Nome")
                            if not telefone: campos_faltando.append("Telefone") 
                            if not email: campos_faltando.append("E-mail")
                            
                            if campos_faltando:
                                st.info(f"📝 Para continuar, preencha: {', '.join(campos_faltando)}")
                    else:
                        st.warning("⚠️ Nenhum horário disponível para esta data.")
        
        with tab_cancelar:
            st.subheader("❌ Cancelar Agendamento")
            
            st.info("ℹ️ Informe os mesmos dados utilizados no agendamento.")
            
            nome_cancel = st.text_input(
                "Nome cadastrado:",
                placeholder="Digite o nome usado no agendamento",
                help="Informe exatamente o mesmo nome usado no agendamento"
            )
            
            telefone_cancel = st.text_input(
                "Telefone cadastrado:",
                placeholder="(11) 99999-9999",
                help="Informe exatamente o mesmo telefone usado no agendamento"
            )
            
            data_cancel = st.date_input(
                "Data do agendamento:",
                min_value=datetime.today().date(),
                help="Selecione a data do agendamento que deseja cancelar"
            )
            
            if st.button("🗑️ Cancelar Agendamento", type="secondary", use_container_width=True):
                if nome_cancel and telefone_cancel and data_cancel:
                    data_str = data_cancel.strftime("%Y-%m-%d")
                    sucesso = cancelar_agendamento(nome_cancel, telefone_cancel, data_str)
                    
                    if sucesso:
                        st.success("✅ Agendamento cancelado com sucesso!")
                    else:
                        st.error("❌ Agendamento não encontrado! Verifique os dados.")
                else:
                    st.warning("⚠️ Preencha todos os campos.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer dinâmico com configurações atualizadas
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; color: rgba(102, 126, 234, 0.8);">
        <p><strong>{nome_clinica}</strong></p>
        <p>📍 {endereco_completo}</p>
        <div style="margin: 1rem 0;">
            <p>📞 {telefone_contato} | 💬 WhatsApp: {whatsapp}</p>
        </div>
        <hr style="margin: 1.5rem 0; border: none; height: 1px; background: #e9ecef;">
        <p>💡 <strong>Dica:</strong> Mantenha seus dados atualizados</p>
        <p style="font-size: 0.9rem; opacity: 0.7;">Sistema de Agendamento Online</p>
    </div>
    """, unsafe_allow_html=True)
