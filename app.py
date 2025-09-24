import pandas as pd
import streamlit as st
import json
import os
from pathlib import Path

# Configuração da página (deve ser a primeira coisa)
st.set_page_config(
    page_title="Análise de Mercados Subsidiários", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="📊"
)

# Função para carregar usuários do arquivo JSON
def carregar_usuarios():
    arquivo_json = "usuarios.json"
    
    # Se o arquivo não existe, cria um com usuário padrão
    if not os.path.exists(arquivo_json):
        usuarios_padrao = {
            "admin": {
                "senha": "admin123",
                "nome": "Administrador"
            }
        }
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(usuarios_padrao, f, ensure_ascii=False, indent=4)
        return usuarios_padrao
    
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de usuários: {e}")
        return {}

# Função para verificar login
def verificar_login(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario in usuarios and usuarios[usuario]["senha"] == senha:
        return True
    return False

# Função para cadastrar novo usuário (apenas admin pode acessar)
def cadastrar_usuario(novo_usuario, nova_senha, nome_completo):
    usuarios = carregar_usuarios()
    
    if novo_usuario in usuarios:
        return False, "Usuário já existe!"
    
    usuarios[novo_usuario] = {
        "senha": nova_senha,
        "nome": nome_completo
    }
    
    try:
        with open("usuarios.json", 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
        return True, "Usuário cadastrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar usuário: {e}"

# Função para criar filtros com opção "Tudo"
def criar_filtro_com_tudo(label, coluna, df):
    opcoes = ['Tudo'] + list(df[coluna].unique())
    selecionados = st.sidebar.multiselect(
        label, 
        opcoes, 
        default=['Tudo']
    )
    
    if 'Tudo' in selecionados or len(selecionados) == 0:
        return df[coluna].unique()
    else:
        return selecionados

# Sistema de autenticação
def mostrar_pagina_login():
    st.title("🔐 Login - Análise de Mercados Subsidiários")
    
    # Container para o formulário de login
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.subheader("Acesso ao Sistema")
                
                usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
                senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                
                submitted = st.form_submit_button("Entrar")
                
                if submitted:
                    if not usuario or not senha:
                        st.error("Por favor, preencha todos os campos!")
                    elif verificar_login(usuario, senha):
                        st.session_state.autenticado = True
                        st.session_state.usuario = usuario
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")
            
            # Link para recuperação de senha (simples)
            st.markdown("---")
            st.caption("Problemas para acessar? Entre em contato com o administrador.")

# Página principal da aplicação
def mostrar_aplicacao_principal():
    # Barra superior com informações do usuário
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.title("📊 Análise de Dados de Mercados Subsidiários")
    
    with col2:
        st.write(f"👤 {st.session_state.usuario}")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.session_state.usuario = None
            st.rerun()
    
    st.markdown("---")
    
    # Carregar e exibir dados
    try:
        diretorio = r"mercados subsidiários.csv"
        
        # Tentar diferentes codificações
        codificacoes = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
        df = None
        
        for encoding in codificacoes:
            try:
                df = pd.read_csv(diretorio, encoding=encoding, sep=';')
                st.success(f"Arquivo carregado com sucesso usando encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        if df is None:
            # Se nenhuma codificação funcionar, tentar com tratamento de erros
            try:
                df = pd.read_csv(diretorio, encoding='latin-1', errors='ignore', sep=';')
                st.warning("Arquivo carregado com tratamento de erros (alguns caracteres podem estar incorretos)")
            except Exception as e:
                st.error(f"Erro ao carregar arquivo: {e}")
                return
        
        # Processamento dos dados
        df = df.astype(str)
        df.dropna(how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Exibir informações do dataset
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Registros", len(df))
        
        with col2:
            st.metric("Total de Colunas", len(df.columns))
        
        with col3:
            st.metric("Usuário Logado", st.session_state.usuario)
        
        # FILTROS NA SIDEBAR
        st.sidebar.header("Filtros")
        
        # Filtros com opção "Tudo"
        mercado_options = criar_filtro_com_tudo('Origem', 'Origem', df)
        uf_origem_options = criar_filtro_com_tudo('UF Origem', 'UF_Origem', df)
        uf_destino_options = criar_filtro_com_tudo('UF Destino', 'UF_Destino', df)
        destino_options = criar_filtro_com_tudo('Destino', 'Destino', df)
        
        # Aplicar filtros ao dataframe
        df_filtrado = df[
            (df['Origem'].isin(mercado_options)) &
            (df['UF_Origem'].isin(uf_origem_options)) &
            (df['UF_Destino'].isin(uf_destino_options)) &
            (df['Destino'].isin(destino_options))
        ]
        
        # Mostrar resultado dos filtros na sidebar
        st.sidebar.markdown("---")
        st.sidebar.metric("Registros Filtrados", len(df_filtrado))
        st.sidebar.metric("Total de Registros", len(df))
        
        # Exibir dataframe filtrado
        st.subheader("Dados Filtrados")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Estatísticas básicas (apenas para colunas numéricas)
        st.subheader("Estatísticas Básicas")
        # Tentar converter colunas para numérico onde possível
        df_numeric = df_filtrado.copy()
        for col in df_numeric.columns:
            try:
                df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce')
            except:
                pass
        
        # Mostrar apenas colunas que foram convertidas com sucesso
        numeric_cols = df_numeric.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            st.dataframe(df_numeric[numeric_cols].describe())
        else:
            st.info("Não foram encontradas colunas numéricas para análise estatística.")
        
        # Seção de gerenciamento de usuários (apenas para admin)
        if st.session_state.usuario == "admin":
            st.markdown("---")
            st.subheader("👥 Gerenciamento de Usuários (Admin)")
            
            with st.expander("Cadastrar Novo Usuário"):
                with st.form("novo_usuario_form"):
                    novo_usuario = st.text_input("Novo Usuário")
                    nova_senha = st.text_input("Nova Senha", type="password")
                    confirmar_senha = st.text_input("Confirmar Senha", type="password")
                    nome_completo = st.text_input("Nome Completo")
                    
                    submitted = st.form_submit_button("Cadastrar Usuário")
                    
                    if submitted:
                        if not all([novo_usuario, nova_senha, confirmar_senha, nome_completo]):
                            st.error("Por favor, preencha todos os campos!")
                        elif nova_senha != confirmar_senha:
                            st.error("As senhas não coincidem!")
                        else:
                            sucesso, mensagem = cadastrar_usuario(novo_usuario, nova_senha, nome_completo)
                            if sucesso:
                                st.success(mensagem)
                            else:
                                st.error(mensagem)
            
            # Listar usuários existentes
            with st.expander("Usuários Cadastrados"):
                usuarios = carregar_usuarios()
                if usuarios:
                    for user, info in usuarios.items():
                        st.write(f"**{user}** - {info['nome']}")
                else:
                    st.info("Nenhum usuário cadastrado.")
    
    except Exception as e:
        st.error(f"Erro na aplicação: {e}")

# Inicializar estado da sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# Mostrar página apropriada baseada no estado de autenticação
if st.session_state.autenticado:
    mostrar_aplicacao_principal()
else:
    mostrar_pagina_login()