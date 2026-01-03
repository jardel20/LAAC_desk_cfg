"""
manual_completo.py
Manual completo do Sistema de Calibração de Bancadas LAAC - Spectral Int
Versão 1.0 - Documentação Técnica Completa
"""

import streamlit as st
import pandas as pd


def exibir_manual_completo():
    """
    Exibe o manual completo do sistema em uma interface organizada por abas
    Esta função deve ser chamada quando st.session_state.show_full_manual = True
    """

    # Cabeçalho do manual
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.markdown(
            "<h3 style='text-align: center; color: #2c3e50; margin-bottom: 20px;'>📚 MANUAL COMPLETO DO SISTEMA DE CALIBRAÇÃO</h3>",
            unsafe_allow_html=True
        )

    # Botão de fechar no topo
    col_close1, col_close2, col_close3 = st.columns([8, 2, 8])
    with col_close2:
        if st.button("❌ Fechar", use_container_width=True, type="primary"):
            st.session_state.show_full_manual = False
            st.rerun()

    st.markdown("---")

    # Conteúdo em um expander grande
    with st.expander("📖 ABRIR/FECHAR MANUAL COMPLETO", expanded=True):

        # Tabs para organizar o conteúdo
        tabs = st.tabs([
            "🏠 INTRODUÇÃO GERAL",
            "⚙️ CONFIGURAÇÃO DO SISTEMA",
            "📈 PARÂMETROS FOTOMÉTRICOS",
            "🧪 CALIBRAÇÃO DA BANCADA",
            "📁 ARQUIVOS LAMP",
            "📊 INTERPRETAÇÃO DE GRÁFICOS",
            "⚠️ BOAS PRÁTICAS",
            "🔍 TROUBLESHOOTING",
            "📖 REFERÊNCIAS"
        ])

        # Chamar cada função de conteúdo
        with tabs[0]:
            _conteudo_introducao_geral()

        with tabs[1]:
            _conteudo_configuracao_sistema()

        with tabs[2]:
            _conteudo_parametros_fotometricos()

        with tabs[3]:
            _conteudo_calibracao_bancada()

        with tabs[4]:
            _conteudo_arquivos_lamp()

        with tabs[5]:
            _conteudo_interpretacao_graficos()

        with tabs[6]:
            _conteudo_boas_praticas()

        with tabs[7]:
            _conteudo_troubleshooting()

        with tabs[8]:
            _conteudo_referencias()

    st.markdown("---")


# ============================================================================
# FUNÇÕES DE CONTEÚDO - CADA ABA DO MANUAL
# ============================================================================

def _conteudo_introducao_geral():
    """Conteúdo da aba 'INTRODUÇÃO GERAL'"""

    col_intro1, col_intro2 = st.columns([2, 1])

    with col_intro1:
        st.markdown("""
        #### 🎯 OBJETIVO DO SISTEMA
        O **Sistema de Calibração de Bancadas LAAC** é uma ferramenta especializada para calibrar, configurar e otimizar bancadas de LEDs para experimentos com plantas. O sistema permite ajustar precisamente a intensidade luminosa de cada canal de LED (Vermelho, Azul, Branco) e gerar arquivos de configuração para controladores de iluminação.
        
        #### 👥 PÚBLICO-ALVO
        - **Pesquisadores** em fisiologia vegetal
        - **Técnicos** de laboratório
        - **Engenheiros agrícolas e Agrônomos**
        - **Estudantes** de pós-graduação
        """)

    with col_intro2:
        st.markdown("""
        #### 🔧 FUNCIONALIDADES PRINCIPAIS
        1. **Calibração individual** por canal com regressão linear
        2. **Configuração de proporções** entre canais de LED
        3. **Geração automática** de arquivos de configuração (formato LAMP)
        4. **Visualização em tempo real** de parâmetros fotométricos
        5. **Simulação de distribuições gaussianas** de intensidade
        
        #### 📋 CARACTERÍSTICAS TÉCNICAS
        - **Versão:** 1.0
        - **Desenvolvido para:** Laboratório LAAC
        - **Compatibilidade:** Controle de bancadas Spectral Int
        """)

    st.markdown("---")

    # Seção de fluxo de trabalho
    st.markdown("#### 🔄 FLUXO DE TRABALHO TÍPICO")
    flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)

    with flow_col1:
        st.markdown("""
        **1. CALIBRAR**
        - Medir PPFD em 5 níveis
        - Inserir dados no sistema
        - Validar R² > 0.95
        """)

    with flow_col2:
        st.markdown("""
        **2. CONFIGURAR**
        - Definir proporções
        - Ajustar gaussianas
        - Estabelecer fotoperíodo
        """)

    with flow_col3:
        st.markdown("""
        **3. VISUALIZAR**
        - Verificar DLI total
        - Analisar curvas
        - Validar ICE
        """)

    with flow_col4:
        st.markdown("""
        **4. EXPORTAR**
        - Gerar arquivos LAMP
        - Baixar configurações
        - Implementar na bancada
        """)


def _conteudo_configuracao_sistema():
    """Conteúdo da aba 'CONFIGURAÇÃO DO SISTEMA'"""

    st.markdown("""
    #### 📊 PROPORÇÕES ENTRE CANAIS
    As proporções definem a **intensidade relativa** entre os diferentes canais de LED:
    """)

    # Tabela de proporções
    proporcoes_data = {
        "Parâmetro": ["Azul", "Vermelho", "Branco"],
        "Faixa": ["0.15 - 5.0", "0.15 - 5.0", "0.15 - 5.0"],
        "Valor Padrão": ["1.0", "1.0", "1.0"],
        "Descrição": [
            "Intensidade do canal azul (450nm)",
            "Intensidade do canal vermelho (660nm)",
            "Intensidade do LED branco (full spectrum)"
        ]
    }

    df_proporcoes = pd.DataFrame(proporcoes_data)
    st.dataframe(df_proporcoes, use_container_width=True, hide_index=True)

    st.markdown("""
    **📝 EXEMPLOS PRÁTICOS:**
    - `Azul=2.0, Vermelho=1.0, Branco=0.5` → Canal azul tem o dobro da intensidade do vermelho
    - `Todos=1.0` → Intensidades balanceadas (padrão)
    - `Azul=0.5, Vermelho=2.0` → Mais vermelho, menos azul (ideal para floração)
    
    ---
    
    #### 📐 PARÂMETROS GAUSSIANOS
    Controlam a **forma da curva de intensidade** ao longo do dia:
    """)

    gaussianas_data = {
        "Parâmetro": ["Sigma (σ)", "Mi (μ)"],
        "Símbolo": ["σ", "μ"],
        "Faixa": ["0.1 - 1.0", "-1.0 - 1.0"],
        "Descrição": ["Largura da distribuição", "Posição do pico da curva"]
    }

    df_gaussianas = pd.DataFrame(gaussianas_data)
    st.dataframe(df_gaussianas, use_container_width=True, hide_index=True)

    st.markdown("""
    **📝 INTERPRETAÇÃO:**
    - **σ pequeno (0.1-0.3):** Curva "afiada", transição rápida entre intensidades
    - **σ grande (0.7-1.0):** Curva "suave", transição gradual
    - **μ negativo (-0.5):** Pico da intensidade no início do fotoperíodo
    - **μ positivo (+0.5):** Pico no final do fotoperíodo  
    - **μ zero (0.0):** Pico no meio do dia (padrão recomendado)
    
    ---
    
    #### ⏰ CONFIGURAÇÃO TEMPORAL
    Define o **fotoperíodo** e resolução temporal:
    """)

    tempo_data = {
        "Parâmetro": ["Hora Início", "Hora Fim", "Nº de Pontos"],
        "Faixa": ["0-23h", "0-23h", "10-60"],
        "Padrão": ["6h", "18h", "60"],
        "Descrição": [
            "Início do fotoperíodo",
            "Fim do fotoperíodo",
            "Resolução temporal (mais pontos = curva mais suave)"
        ]
    }

    df_tempo = pd.DataFrame(tempo_data)
    st.dataframe(df_tempo, use_container_width=True, hide_index=True)

    st.markdown("""
    **💡 DICA IMPORTANTE:** 
    - Mais pontos = curva mais suave, mas arquivo de configuração maior
    - 30-40 pontos geralmente fornecem um bom equilíbrio entre suavidade e tamanho
    
    ---
    
    #### ⚡ INTENSIDADES TOTAIS
    Define os **limites absolutos** de intensidade para a bancada inteira:
    """)

    intensidade_data = {
        "Parâmetro": ["Máx. Total", "Mín. Total"],
        "Faixa": ["0-2000 μmol/m²/s", "0-1000 μmol/m²/s"],
        "Padrão": ["650 μmol/m²/s", "120 μmol/m²/s"],
        "Descrição": [
            "Soma máxima de todos os canais combinados",
            "Soma mínima de todos os canais combinados (intensidade basal)"
        ]
    }

    df_intensidade = pd.DataFrame(intensidade_data)
    st.dataframe(df_intensidade, use_container_width=True, hide_index=True)

    st.warning("""
    **⚠️ ATENÇÃO:** 
    Estes são valores **combinados** de todos os canais. 
    A intensidade real de cada canal será proporcional às configurações de proporção.
    """)


def _conteudo_parametros_fotometricos():
    """Conteúdo da aba 'PARÂMETROS FOTOMÉTRICOS' com LaTeX"""

    st.markdown("#### 🔍 GLOSSÁRIO DE TERMOS TÉCNICOS")

    # Criar tabela em HTML/Markdown
    st.markdown("""
    | Termo | Símbolo | Unidade | Descrição | Explicação |
    |-------|---------|---------|-----------|------------|
    | **PPFD** | $\Phi_{PPFD}$ | μmol·m⁻²·s⁻¹ | Densidade de fluxo de fótons fotossintéticos | Densidade de fluxo de fótons fotossintéticos na faixa 400-700nm |
    | **DLI** | $Q_{DLI}$ | mol·m⁻² | Integral diário de luz fotossintética | Total de fótons acumulados em 24 horas por unidade de área |
    | **ICE** | $I_{ICE}$ | μmol·m⁻²·s⁻¹ | Irradiação constante equivalente | Intensidade constante que produziria o mesmo DLI da curva variável |
    """)

    st.markdown("#### 🧮 FORMULÁRIO TÉCNICO")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### **DLI - Daily Light Integral**")
        st.latex(r'''
        Q_{DLI} = \frac{1}{10^6} \int_{t_0}^{t_f} \Phi_{PPFD}(t) \, dt
        ''', width="content")
        st.markdown("""
        **Variáveis:**
        - $Q_{DLI}$: DLI total [mol·m⁻²]
        - $\Phi_{PPFD}(t)$: PPFD em função do tempo [μmol·m⁻²·s⁻¹]
        - $t_0, t_f$: Início e fim do fotoperíodo [s]
        """)

    with col2:
        st.markdown("#### **ICE - Irradiação Constante Equivalente**")
        st.latex(r'''
        I_{ICE} = \frac{Q_{DLI} \times 10^6}{t_f - t_0}
        ''', width="content")
        st.markdown("""
        **Variáveis:**
        - $I_{ICE}$: ICE [μmol·m⁻²·s⁻¹]
        - $Q_{DLI}$: DLI calculado [mol·m⁻²]
        - $\Delta t = t_f - t_0$: Duração do fotoperíodo [s]
        """)

    st.markdown("---")

    st.markdown("#### 📐 DISTRIBUIÇÃO GAUSSIANA NORMALIZADA")

    st.latex(r'''
    \Phi(x) = \Phi_{\min} + (\Phi_{\max} - \Phi_{\min}) \cdot 
    \exp\left[-\frac{(x - \mu)^2}{2\sigma^2}\right]
    ''', width="content")

    st.markdown("""
    **Parâmetros:**
    
    | Símbolo | Nome | Domínio | Descrição |
    |---------|------|---------|-----------|
    | $\Phi(x)$ | Intensidade | $\mathbb{R}$ | PPFD no ponto $x$ |
    | $\Phi_{\min}$ | Intensidade mínima | $[0, \infty)$ | Valor basal |
    | $\Phi_{\max}$ | Intensidade máxima | $[0, \infty)$ | Valor de pico |
    | $\mu$ | Posição média | $[-1, 1]$ | Centro da distribuição |
    | $\sigma$ | Desvio padrão | $(0, \infty)$ | Largura da curva |
    | $x$ | Variável normalizada | $[-1, 1]$ | Tempo normalizado |
    """)

    st.markdown("---")

    st.markdown("#### 🔄 CONVERSÕES E TRANSFORMAÇÕES")

    st.markdown("#### **Conversão de Unidades**")

    col_conv1, col_conv2 = st.columns(2)

    with col_conv1:
        st.latex(r'''
        1 \text{ mol de fótons} = N_A \text{ fótons}
        ''', width="content")
        st.caption(
            "$N_A = 6.022 \times 10^{23} \text{ mol}^{-1}$ (Número de Avogadro)")

    with col_conv2:
        st.latex(r'''
                 1\ \mu\text{mol}\ \text{m}^{-2}\ \text{s}^{-1} = N_A \times 10^{-6}\ \text{fótons}\ \text{m}^{-2}\ \text{s}^{-1}
                 ''', width="content")

    st.markdown("#### **Eficiência Quântica**")
    st.latex(r'''
    \Phi_{\text{PPFD}} \approx 4.6 \times E_{\text{PAR}}
    ''', width="content")

    st.markdown(r"""
    **Onde:**

    - $\Phi_{\text{PPFD}}$: Photosynthetic Photon Flux Density [μmol·m⁻²·s⁻¹]
    - $E_{\text{PAR}}$: Photosynthetically Active Radiation [W·m⁻²]
    - 4.6: Fator de conversão aproximado para espectro solar

    **Equivalência de unidades:**

    $$
    1\ \text{W}\cdot\text{m}^{-2}\ \text{(PAR)} \approx 4.6\ \mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}
    $$
    """, width="content")
    st.caption("Conversão aproximada para LEDs de espectro branco")


def _conteudo_calibracao_bancada():
    """Conteúdo da aba 'CALIBRAÇÃO DA BANCADA'"""

    st.markdown("""
    #### 📋 PROCEDIMENTO DE CALIBRAÇÃO PASSO A PASSO
    """)

    # Passos numerados
    st.markdown("""
    **Passo 1: Preparação do Equipamento**
    1. Posicione o spectômetro no centro da área de cultivo, na altura das plantas
    2. Certifique-se de que não há sombreamento ou reflexos
    
    **Passo 2: Coleta de Dados por Canal**
    Para cada canal (Vermelho, Azul, Branco):
    1. Selecione apenas o canal a ser calibrado (desligue outros)
    2. Ajuste a intensidade para os níveis: 0%, 30%, 50%, 70%, 100%
    3. Em cada nível:
       - Aguarde 30 segundos para estabilização
       - Registre 5 medições consecutivas (repetições)
       - Anote os valores em uma planilha
    4. Repita para todos os canais
    
    **Passo 3: Inserção de Dados no Sistema**
    1. Acesse a aba "🧪 Calibração Bancada"
    2. Selecione o canal correspondente
    3. Insira os valores medidos na tabela interativa
    4. O sistema calcula automaticamente:
       - Média e mediana das repetições
       - Regressão linear (valor medido vs referência)
       - Coeficiente de determinação (R²)
       - Erro padrão da estimativa
    
    **Passo 4: Validação da Calibração**
    - **R² > 0.98:** ✅ Calibração excelente
    - **R² 0.95-0.98:** ⚠️ Calibração aceitável (verificar possíveis melhorias)
    - **R² < 0.95:** ❌ Recalibrar necessária
    """)

    st.markdown("---")

    st.markdown("""
    #### 🔄 RESTAURAÇÃO DE VALORES PADRÃO
    
    Cada canal possui valores de calibração padrão pré-carregados baseados em medições de referência.
    
    **QUANDO USAR O BOTÃO "🔄 Restaurar Valores Padrão":**
    - Para voltar aos valores de fábrica/referência
    - Para corrigir entradas incorretas acidentais
    - Para reiniciar o processo de calibração
    - Após manutenção ou substituição de componentes
    
    **VALORES PADRÃO INCLUÍDOS:**
    - **5 níveis** de intensidade (0%, 30%, 50%, 70%, 100%)
    - **5 repetições** por nível
    - Dados coletados em condições controladas de laboratório
    """)


def _conteudo_arquivos_lamp():
    """Conteúdo da aba 'ARQUIVOS LAMP'"""

    st.markdown("""
    #### 🔌 FORMATOS DE ARQUIVO DISPONÍVEIS
    
    O sistema gera arquivos no formato compatível com controladores LAMP (Lighting Automation and Management Protocol).
    """)

    col_format1, col_format2 = st.columns(2)

    with col_format1:
        st.markdown("""
        #### **1. ⚡ CURVA COMPLETA**
        ```
          HH MM SS INTENSIDADE
          06 00 00 120
          07 12 00 185
          08 24 00 245
          ... (múltiplas linhas)
          17 48 00 165
          18 00 00 120
        ```
        
        **CARACTERÍSTICAS:**
        - Representação fiel da curva gaussiana configurada
        - Múltiplos pontos ao longo do fotoperíodo
        - Controle preciso da intensidade em cada momento
        - Arquivo maior, mas mais preciso
        
        **USO RECOMENDADO:**
        - Experimentos que requerem precisão temporal
        - Sistemas com capacidade de processamento adequada
        - Quando a forma da curva é crítica
        """)

    with col_format2:
        st.markdown("""
        #### **2. 📊 LINEAR (ICE SIMPLIFICADO)**
        ```
          HH_INICIO 00 00 ICE
          HH_FIM 00 00 ICE
        ```
        
        **EXEMPLO:**
        ```
          06 00 00 245
          18 00 00 245
        ```
        
        **CARACTERÍSTICAS:**
        - Apenas 2 linhas (início e fim do fotoperíodo)
        - Usa o valor ICE (média equivalente)
        - Intensidade constante ao longo do dia
        - Arquivo mínimo e simples
        
        **USO RECOMENDADO:**
        - Sistemas com capacidade limitada de armazenamento
        - Quando apenas intensidade constante é necessária
        - Para testes rápidos ou configurações básicas
        """)

    st.markdown("---")

    st.markdown("""
    #### 🗂️ ESTRUTURA DE ARQUIVOS POR CANAL
    
    O sistema gera 4 arquivos correspondentes aos canais da bancada:
    """)

    arquivos_data = {
        "Arquivo": ["LAMP_CH1.txt", "LAMP_CH2.txt", "LAMP_CH3.txt", "LAMP_CH4.txt"],
        "Canal": ["Vermelho", "Azul", "Branco", "Branco (cópia)"],
        "Emoji": ["🔴", "🔵", "⚪", "⚪"],
        "Uso Típico": [
            "Fotossíntese, floração, desenvolvimento reprodutivo",
            "Morfogênese, controle de estiolamento, fototropismo",
            "Crescimento vegetativo geral, desenvolvimento completo",
            "Reserva/backup, duplicação para sistemas com 4 canais"
        ],
        "Comprimento de Onda": ["660nm ±20nm", "450nm ±20nm", "Full Spectrum 400-700nm", "Full Spectrum 400-700nm"]
    }

    df_arquivos = pd.DataFrame(arquivos_data)
    st.dataframe(df_arquivos, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.markdown("""
    #### 📦 PACOTE COMPLETO (ARQUIVO ZIP)
    
    O botão **"📦 Todos"** gera um arquivo ZIP contendo todas as configurações em ambos formatos:
    
    ```
    lamp_config_completo.zip/
    ├── 📁 curva_completa/           # Arquivos con curva gaussiana completa
    │   ├── LAMP_CH1.txt            # Canal Vermelho
    │   ├── LAMP_CH2.txt            # Canal Azul
    │   ├── LAMP_CH3.txt            # Canal Branco
    │   └── LAMP_CH4.txt            # Cópia do Branco
    │
    ├── 📁 ice_simplificado/        # Arquivos simplificados con ICE
    │   ├── LAMP_CH1_ICE.txt       # Vermelho (ICE)
    │   ├── LAMP_CH2_ICE.txt       # Azul (ICE)
    │   ├── LAMP_CH3_ICE.txt       # Branco (ICE)
    │   └── LAMP_CH4_ICE.txt       # Branco cópia (ICE)
    │
    ├── 📄 README.txt               # Documentação do pacote
    └── 📊 valores_ice.csv          # Tabela com valores calculados
    ```
    
    **CONTEÚDO DO README.txt:**
    - Data e hora de geração
    - Parâmetros utilizados
    - Valores de ICE por canal
    - Instruções de uso
    - Configurações aplicadas
    
    **CONTEÚDO DO valores_ice.csv:**
    - ICE de cada canal (μmol/m²/s)
    - DLI final (mol/m²)
    - Intensidades máxima e mínima
    - Proporções configuradas
    """)

    st.info("""
    **💡 DICA DE ORGANIZAÇÃO:**
    Renomeie o arquivo ZIP incluindo data e descrição, por exemplo:
    `Config_LAMP_2024_03_15_Tomate_AltaLuz.zip`
    """)


def _conteudo_interpretacao_graficos():
    """Conteúdo da aba 'INTERPRETAÇÃO DE GRÁFICOS'"""

    st.markdown("""
    #### 📊 GUIA DE INTERPRETAÇÃO VISUAL
    
    O sistema gera diversos gráficos que permitem analisar e validar as configurações.
    """)

    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        st.markdown("""
        #### **📉 GRÁFICO DE REGRESSÃO LINEAR**
        
        **ELEMENTOS VISUAIS:**
        - **Eixo X:** Valor de referência (0.0 a 1.0 = 0% a 100% de intensidade)
        - **Eixo Y:** PPFD medido (μmol/m²/s)
        - **Pontos coloridos:** Medições individuais (5 repetições por nível)
        - **Linha tracejada:** Modelo de regressão linear ajustado
        - **Área sombreada:** Intervalo de confiança (quando aplicável)
        
        **INDICADORES DE QUALIDADE:**
        - **R² próximo de 1.0:** Ajuste excelente
        - **Pontos próximos à linha:** Precisão nas medições
        - **Distribuição uniforme:** Calibração consistente
        """)

    with col_graph2:
        st.markdown("""
        #### **🌈 COMPARAÇÃO DE INTENSIDADES**
        
        **ELEMENTOS VISUAIS:**
        - **Curvas coloridas:** Evolução temporal de cada canal individual
        - **Área sombreada abaixo:** Intensidade acumulada ao longo do tempo
        - **Linha preta tracejada:** Soma total de todos os canais combinados
        - **Eixo X:** Hora do dia em formato 24 horas
        - **Barra de zoom:** Controle deslizante para ampliar períodos específicos
        
        **ANÁLISE SUGERIDA:**
        - Verifique sobreposição de picos entre canais
        - Analise a suavidade das transições
        - Confirme que a soma total está dentro dos limites
        """)

    st.markdown("---")

    col_graph3, col_graph4 = st.columns(2)

    with col_graph3:
        st.markdown("""
        #### **📊 GRÁFICOS DE BARRAS (DLI e ICE)**
        
        **ELEMENTOS VISUAIS:**
        - **Altura da barra:** Valor acumulado (DLI) ou valor médio (ICE)
        - **Cores das barras:** Correspondem aos canais individuais
        - **Barra "Total":** Soma combinada de todos os canais
        - **Valores no topo:** Valores numéricos exatos para referência
        - **Grade de fundo:** Auxilia na leitura dos valores
        
        **INTERPRETAÇÃO:**
        - Compare DLI entre canais
        - Verifique contribuição relativa de cada cor
        - Valide DLI total dentro da faixa desejada
        """)

    with col_graph4:
        st.markdown("""
        #### **🔔 DISTRIBUIÇÃO GAUSSIANA**
        
        **ELEMENTOS VISUAIS:**
        - **Curva principal:** Forma da distribuição normal de intensidade
        - **Área azul clara:** Região ±σ (68% da área total sob a curva)
        - **Linha vertical tracejada:** Posição de μ (pico da distribuição)
        - **Marcadores horizontais:** Valores de máximo e mínimo calculados
        - **Eixo X:** Domínio normalizado (-1 a +1) correspondente ao fotoperíodo
        
        **PARÂMETROS VISÍVEIS:**
        - **Largura da curva:** Controlada por σ
        - **Posição do pico:** Controlada por μ
        - **Altura máxima:** Intensidade máxima do canal
        - **Altura mínima:** Intensidade basal do canal
        """)

    st.markdown("---")

    st.markdown("""
    #### 🎨 LEGENDA DE CORES PADRÃO
    
    | Canal | Cor Hex | Uso | Significado |
    |-------|---------|-----|-------------|
    | Vermelho | `#ee6666` | Gráficos, barras, pontos | Canal vermelho (660nm) |
    | Azul | `#5470c6` | Gráficos, barras, pontos | Canal azul (450nm) |
    | Branco | `#b3b3b3` | Gráficos, barras, pontos | Canal branco (full spectrum) |
    | Soma Total | `#363636` | Linha tracejada | Combinação de todos os canais |
    | Regressão | `#73c0de` | Linhas de ajuste | Modelos matemáticos |
    | Grade | `#e0e6f1` | Fundo dos gráficos | Elementos de referência |
    
    **CONVENÇÃO:** As cores são consistentes em todos os gráficos para facilitar a interpretação.
    """)


def _conteudo_boas_praticas():
    """Conteúdo da aba 'BOAS PRÁTICAS'"""

    st.markdown("""
    #### ✅ CHECKLIST DE CONFIGURAÇÃO RECOMENDADA
    
    **ANTES DE INICIAR QUALQUER EXPERIMENTO:**
    
    1. **CALIBRAÇÃO DO SISTEMA**
       - [ ] Calibrar cada canal individualmente
       - [ ] Verificar R² > 0.95 em todas as regressões
       - [ ] Documentar valores obtidos e data da calibração
    
    2. **CONFIGURAÇÃO DOS PARÂMETROS**
       - [ ] Ajustar proporções conforme necessidade das plantas
       - [ ] Validar DLI total dentro da faixa recomendada para a espécie
       - [ ] Verificar que a soma máxima não excede a capacidade da bancada
       - [ ] Ajustar fotoperíodo conforme fase de desenvolvimento
    
    3. **VALIDAÇÃO VISUAL**
       - [ ] Analisar curvas de intensidade para suavidade adequada
       - [ ] Verificar que não há descontinuidades ou picos abruptos
       - [ ] Confirmar que os valores de ICE são realistas
       - [ ] Validar distribuição temporal adequada
    
    4. **TESTE PRÁTICO**
       - [ ] Gerar arquivos de configuração
       - [ ] Testar arquivos no controlador real
       - [ ] Verificar resposta dos LEDs
       - [ ] Medir PPFD real na bancada para validação final
    
    5. **DOCUMENTAÇÃO**
       - [ ] Salvar configurações com nome descritivo
       - [ ] Anotar parâmetros utilizados
       - [ ] Registrar data e finalidade da configuração
       - [ ] Salvar backup dos arquivos gerados
    """)

    st.markdown("---")

    st.markdown("""
    #### 🚫 ERROS COMUNIS A EVITAR
    
    **1. INTENSIDADE EXCESSIVA**
    - **Sintoma:** Folhas queimadas, clorose, fotoinibição
    - **Prevenção:** Não exceder PPFD máximo recomendado para a espécie
    - **Solução:** Reduzir intensidade máxima total ou proporções
    
    **2. FOTOPERÍODO INADEQUADO**
    - **Sintoma:** Estiolamento, floração precoce/tardia, baixo crescimento
    - **Prevenção:** Pesquisar necessidades fotoperiódicas da espécie
    - **Solução:** Ajustar horas de início e fim conforme fase de desenvolvimento
    
    **3. PROPORÇÕES DESBALANCEADAS**
    - **Sintoma:** Morfologia anormal, crescimento assimétrico
    - **Prevenção:** Usar proporções baseadas em literatura científica
    - **Solução:** Ajustar proporções para melhorar qualidade espectral
    
    **4. CALIBRAÇÃO NEGLIGENCIADA**
    - **Sintoma:** Diferenças entre valores configurados e medidos
    - **Prevenção:** Estabelecer cronograma de calibração regular
    - **Solução:** Recalibrar seguindo procedimento padrão
    
    **5. ARQUIVOS DE CONFIGURAÇÃO INCORRETOS**
    - **Sintoma:** Comportamento inesperado dos LEDs
    - **Prevenção:** Sempre testar arquivos gerados
    - **Solução:** Verificar formato, valores e compatibilidade
    """)

    st.markdown("---")

    st.markdown("""
    #### 🔄 CRONOGRAMA DE MANUTENÇÃO
    
    **MANUTENÇÃO DIÁRIA:**
    - Verificar funcionamento básico dos LEDs
    - Observar comportamento das plantas
    - Anotar anomalias visuais
    
    **MANUTENÇÃO ENTRE EXPERIMENTOS:**
    - Limpeza mais profunda do sistema
    - Verificação rápida do sensor PAR (se disponível)
    - Calibração do sensor PAR (se aplicável)
    - Verificação de degradação dos LEDs
    - Verificação de todos os parâmetros configurados
    - Backup dos arquivos de configuração
    - Atualização de registros
    - Substituição de componentes se necessário
    - Recalibração de todo o sistema
    - Auditoria de desempenho
    - Atualização de procedimentos
    """)


def _conteudo_troubleshooting():
    """Conteúdo da aba 'TROUBLESHOOTING'"""

    st.markdown("""
    #### 🔍 GUIA DE SOLUÇÃO DE PROBLEMAS
    
    Problemas comuns e como resolvê-los passo a passo.
    """)

    # Acordeão de problemas
    with st.expander("**PROBLEMA: Valores de DLI calculados muito baixos**", expanded=False):
        st.markdown("""
        **SINTOMAS:**
        - DLI total abaixo do recomendado para a espécie
        - Plantas com crescimento lento ou estiolamento
        - Valores de ICE muito baixos
        
        **CAUSAS POSSÍVEIS:**
        1. Intensidade máxima total configurada muito baixa
        2. Fotoperíodo muito curto
        3. Proporções desbalanceadas reduzindo intensidade efetiva
        4. Parâmetros gaussianos com pico muito estreito
        
        **SOLUÇÃO PASSO A PASSO:**
        1. **Verifique "Máx. Total":** Aumente gradualmente (ex: 650 → 660 μmol/m²/s)
        2. **Ajuste fotoperíodo:** Extenda em 1-2 horas se possível
        3. **Revise proporções:** Certifique-se de que não há valores muito baixos
        4. **Aumente σ:** Alargue a distribuição (ex: 0.3 → 0.5)
        5. **Recalcule e valide** novos valores de DLI
        
        **VALIDAÇÃO:** DLI total deve estar na faixa recomendada para a espécie.
        """)

    with st.expander("**PROBLEMA: Curva de intensidade muito 'afiada' ou muito 'suave'**", expanded=False):
        st.markdown("""
        **SINTOMAS:**
        - Transições muito abruptas entre intensidades
        - Curva quase plana sem variação significativa
        - Picos muito estreitos ou muito largos
        
        **CAUSAS POSSÍVEIS:**
        1. Parâmetro σ muito pequeno (curva afiada)
        2. Parâmetro σ muito grande (curva suave)
        3. Diferença muito pequena entre máximo e mínimo
        
        **SOLUÇÃO PASSO A PASSO:**
        1. **Para curvas muito afiadas:** Aumente σ (0.2 → 0.4)
        2. **Para curvas muito suaves:** Diminua σ (0.8 → 0.5)
        3. **Valores recomendados:** σ entre 0.3 e 0.6 para maioria das aplicações
        4. **Ajuste máximo-mínimo:** Aumente diferença se curva muito plana
        
        **TESTE VISUAL:** A curva deve mostrar transição suave mas perceptível.
        """)

    with st.expander("**PROBLEMA: Arquivo LAMP não é reconhecido pelo controlador**", expanded=False):
        st.markdown("""
        **SINTOMAS:**
        - Controlador mostra erro ao carregar arquivo
        - LEDs não respondem conforme esperado
        - Comportamento aleatório ou inesperado
        
        **CAUSAS POSSÍVEIS:**
        1. Formato de arquivo incompatível
        2. Valores fora da faixa aceita pelo controlador
        3. Estrutura de arquivo incorreta
        4. Codificação de caracteres problemática
        
        **SOLUÇÃO PASSO A PASSO:**
        1. **Use formato "Linear (ICE)":** Mais compatível com sistemas limitados
        2. **Verifique valores máximos:** Não exceda capacidade do controlador
        3. **Inspecione formato:** Use visualização prévia para verificar estrutura
        4. **Teste com arquivo simples:** Comece com configuração básica
        5. **Consulte manual do controlador:** Verifique especificações exatas
        
        **FORMATO CORRETO:** `HH MM SS INTENSIDADE` com espaços simples.
        """)

    with st.expander("**PROBLEMA: Diferença entre valores configurados e medidos**", expanded=False):
        st.markdown("""
        **SINTOMAS:**
        - PPFD medido difere significativamente do calculado
        - Inconsistências entre canais
        - Deriva temporal nas medições
        
        **CAUSAS POSSÍVEIS:**
        1. Calibração desatualizada ou incorreta
        2. Degradação dos LEDs
        3. Problemas no sensor de medição
        4. Efeitos térmicos ou ambientais
        
        **SOLUÇÃO PASSO A PASSO:**
        1. **Recalibre o canal específico:** Siga procedimento padrão
        2. **Verifique sensor:** Calibre ou substitua se necessário
        3. **Avalie degradação:** LEDs perdem intensidade com o tempo
        4. **Considere condições:** Temperatura afecta output dos LEDs
        5. **Documente diferenças:** Para correções futuras
        
        **TOLERÂNCIA ACEITÁVEL:** Diferenças até 10% podem ser normais.
        """)

    with st.expander("**PROBLEMA: Sistema lento ou não responsivo**", expanded=False):
        st.markdown("""
        **SINTOMAS:**
        - Atualizações lentas nos gráficos
        - Atraso na resposta a mudanças
        - Congelamento temporário
        
        **CAUSAS POSSÍVEIS:**
        1. Número muito alto de pontos de interpolação
        2. Limitações do hardware ou navegador
        3. Cálculos intensivos em tempo real
        
        **SOLUÇÃO PASSO A PASSO:**
        1. **Reduza "Nº de Pontos":** 30-40 geralmente é suficiente
        2. **Atualize navegador:** Use versões recentes
        3. **Reinicie aplicação:** Limpa cache e estado temporário
        4. **Use modo simplificado:** Algumas funcionalidades podem ser desabilitadas      
        """)


def _conteudo_referencias():
    """Conteúdo da aba 'REFERÊNCIAS' com LaTeX consistente, ABNT e links"""

    st.markdown("""
    #### 📖 REFERÊNCIAS TÉCNICAS E BIBLIOGRÁFICAS
    """)

    # --- SEÇÃO 1: FÓRMULAS E CÁLCULOS (CONSISTENTE com _conteudo_parametros_fotometricos) ---
    st.markdown("#### 🧮 FÓRMULAS E CÁLCULOS")

    # Fórmula 1: DLI - MESMOS SÍMBOLOS (Q_DLI, Φ_PPFD, t₀, t_f)
    st.markdown("**1. Cálculo do DLI (Daily Light Integral):**")
    st.latex(r'''
    Q_{DLI} = \frac{1}{10^6} \int_{t_0}^{t_f} \Phi_{PPFD}(t) \, dt
    ''')
    st.markdown("""
    **Variáveis (consistente com glossário):**
    - $Q_{DLI}$: DLI total [mol·m⁻²] (*Integral diário de luz fotossintética*)
    - $\Phi_{PPFD}(t)$: PPFD em função do tempo [μmol·m⁻²·s⁻¹] (*Densidade de fluxo de fótons fotossintéticos*)
    - $t_0, t_f$: Início e fim do fotoperíodo [s]
    - $10^6$: Fator de conversão de μmol para mol
    """)

    # Fórmula 2: ICE - MESMOS SÍMBOLOS (I_ICE, Q_DLI)
    st.markdown("**2. Cálculo do ICE (Irradiação Constante Equivalente):**")
    st.latex(r'''
    I_{ICE} = \frac{Q_{DLI} \times 10^6}{t_f - t_0}
    ''')
    st.markdown("""
    **Variáveis (consistente com glossário):**
    - $I_{ICE}$: ICE [μmol·m⁻²·s⁻¹] (*Irradiação constante equivalente*)
    - $Q_{DLI}$: DLI calculado [mol·m²]
    - $t_f - t_0$: Duração da iluminação (Fotoperíodo em segundos)
    """)

    # Fórmula 3: Gaussiana - MESMOS SÍMBOLOS (Φ(x), Φ_min, Φ_max, μ, σ, x)
    st.markdown("**3. Distribuição Gaussiana Normalizada:**")
    st.latex(r'''
    \Phi(x) = \Phi_{\min} + (\Phi_{\max} - \Phi_{\min}) \cdot \exp\!\left( -\frac{(x - \mu)^2}{2\sigma^2} \right)
    ''')
    st.markdown("""
    **Parâmetros (totalmente consistente):**
    
    | Símbolo | Nome | Domínio | Descrição |
    |---------|------|---------|-----------|
    | $\Phi(x)$ | Intensidade | $\mathbb{R}$ | **PPFD no ponto $x$** |
    | $\Phi_{\min}$ | Intensidade mínima | $[0, \infty)$ | Valor basal (PPFD mínimo) |
    | $\Phi_{\max}$ | Intensidade máxima | $[0, \infty)$ | Valor de pico (PPFD máximo) |
    | $\mu$ | Posição média | $[-1, 1]$ | Centro da distribuição |
    | $\sigma$ | Desvio padrão | $(0, \infty)$ | Largura da curva |
    | $x$ | Variável normalizada | $[-1, 1]$ | Tempo normalizado |
    
    *Nota: $\Phi(x)$ representa PPFD ao longo do tempo, consistente com $\Phi_{PPFD}$ do glossário.*
    """)

    # Fórmula 4: Conversão de Hora - MANTIDO igual
    st.markdown("**4. Conversão Hora Decimal para HH:MM:SS:**")
    st.latex(r'''
    \begin{aligned}
    h &= \lfloor H \rfloor \\
    m &= \lfloor (H - h) \times 60 \rfloor \\
    s &= \operatorname{round}\!\left( ((H - h) \times 60 - m) \times 60 \right)
    \end{aligned}
    ''')

    st.markdown("---")

    # --- SEÇÃO 2: CONVERSÕES E CONSTANTES (CONSISTENTE) ---
    st.markdown("#### 🔬 CONVERSÕES E CONSTANTES")

    st.markdown(
        "**CONVERSÕES DE UNIDADE (consistentes com formulário anterior):**")
    st.latex(r'''
    \begin{aligned}
    1 \text{ mol de fótons} &= N_A \text{ fótons} \\
    1\ \mu\text{mol}\ \text{m}^{-2}\ \text{s}^{-1} &= N_A \times 10^{-6}\ \text{fótons}\ \text{m}^{-2}\ \text{s}^{-1} \\
    \Phi_{\text{PPFD}} &\approx 4.6 \times E_{\text{PAR}} \\
    1\ \text{lux (luz solar)} &\approx 0.0185\ \mu\text{mol}\cdot\text{m}^{-2}\cdot\text{s}^{-1}
    \end{aligned}
    ''')
    st.markdown("""
    **Onde:**
    - $N_A = 6.02214076 \times 10^{23} \text{ mol}^{-1}$ (Número de Avogadro)
    - $\Phi_{\text{PPFD}}$: Photosynthetic Photon Flux Density [μmol·m⁻²·s⁻¹]
    - $E_{\text{PAR}}$: Photosynthetically Active Radiation [W·m⁻²]
    - *Conversão lux/PPFD varia significativamente com o espectro*
    """)

    st.markdown("**EFICIÊNCIAS ESPECTRAIS:**")
    st.markdown("""
    - **Eficiência quântica máxima:** $\lambda \\approx 680\\ \\text{nm}$ (Fotossistema II)
    - **Absorção clorofila *a*:** Picos em $\lambda \\approx 430\\ \\text{nm}$ e $662\\ \\text{nm}$
    - **Absorção clorofila *b*:** Picos em $\lambda \\approx 453\\ \\text{nm}$ e $642\\ \\text{nm}$
    - **PAR (400-700 nm):** Representa $\eta \\approx 45\\text{-}50\\%$ da radiação total em LEDs brancos
    """)

    st.markdown("**RELAÇÕES ESPECTRAIS RECOMENDADAS (mesma notação):**")
    st.markdown("""
    - **Vermelho:Azul (R:B):** $3:1$ a $5:1$ para maioria das plantas
    - **Vermelho:Vermelho-distante (R:FR):** $1:0.1$ a $1:0.3$ para controle morfogenético
    - **Azul:Verde (B:G):** $1:0.5$ a $1:1$ para melhor penetração no dossel
    """)

    st.markdown("---")

    # --- SEÇÃO 3: BIBLIOGRAFIA (FORMATO ABNT) ---
    st.markdown("#### 📚 BIBLIOGRAFIA RECOMENDADA")

    st.markdown("**ARTIGOS CIENTÍFICOS FUNDAMENTAIS:**")
    st.markdown("""
    1. **MCCREE, K. J.** The action spectrum, absorptance and quantum yield of photosynthesis in crop plants. *Agricultural Meteorology*, v. 9, p. 191-216, 1972. *(Fundamental para espectro de ação fotossintética)*
    2. **SAGER, J. C.; SMITH, W. O.; EDWARDS, J. L.; CYR, K. L.** Photosynthetic efficiency and phytochrome photoequilibria determination using spectral data. *Transactions of the ASAE*, v. 31, n. 6, p. 1882-1889, 1988. *(Base para cálculos de $\Phi_{PPFD}$ e equilíbrio fitocromo)*
    3. **BUGBEE, B.** Toward an optimal spectral quality for plant growth and development: LED lighting. In: **KOZAI, T.; NUCA, G.; TAKAGAKI, M.** (Ed.). *Plant Factory: An Indoor Vertical Farming System for Efficient Quality Food Production*. 2nd ed. London: Academic Press, 2020. p. 129-144. *(Otimização espectral para $Q_{DLI}$ e $I_{ICE}$)*
    """)

    st.markdown("**LIVROS E MANUAIS:**")
    st.markdown("""
    4. **TAIZ, L.; ZEIGER, E.; MOLLER, I. M.; MURPHY, A.** *Fisiologia e Desenvolvimento Vegetal*. 6. ed. Porto Alegre: Artmed, 2017. *(Referência completa em fisiologia vegetal)*
    5. **NELSON, J. A.; BUGBEE, B.** Economic analysis of greenhouse lighting: light emitting diodes vs. high intensity discharge fixtures. *PLOS ONE*, v. 9, n. 6, e99010, 2014. *(Análise técnica e econômica de iluminação)*
    6. **KOZAI, T.; NUCA, G.; TAKAGAKI, M.** (Ed.). *Plant Factory: An Indoor Vertical Farming System for Efficient Quality Food Production*. 2nd ed. London: Academic Press, 2020. *(Sistemas completos de agricultura indoor)*
    """)

    st.markdown("**GUIAS PRÁTICOS E RELATÓRIOS TÉCNICOS:**")
    st.markdown("""
    7. **NATIONAL AERONAUTICS AND SPACE ADMINISTRATION (NASA).** *Lighting Guidelines for Plant Growth in Controlled Environments*. Kennedy Space Center, FL: NASA, 2020. *(Diretrizes para $\Phi_{PPFD}$, $Q_{DLI}$ e espectro)*
    8. **University of Arizona, Controlled Environment Agriculture Center (CEAC).** *Greenhouse Lighting Guide: An Introductory Guide for Lighting Greenhouses*. Tucson, AZ: University of Arizona, 2019. *(Guia prático para cálculos de iluminação)*
    9. **LED GROW LIGHTS DIRECTORY.** *Spectral Optimization for Different Crops: A Practical Guide*. 2021. Disponível em: [ledgrowlightsdirectory.com/guides](https://ledgrowlightsdirectory.com/guides). Acesso em: 3 jan. 2026. *(Otimização de relações espectrais R:B, R:FR, B:G)*
    """)

    st.markdown("---")

    # --- SEÇÃO 4: RECURSOS ONLINE (COM LINKS) ---
    st.markdown("#### 🌐 RECURSOS ONLINE (Apenas exemplo)")

    st.markdown(
        "**CALCULADORAS E FERRAMENTAS (para $Q_{DLI}$, $\Phi_{PPFD}$, etc.):**")
    st.markdown("""
    - **[DLI Calculator](https://www.usu.edu/nautilus/dli-calculator)** – Utah State University *(Cálculo de $Q_{DLI}$)*
    - **[PPFD Map Generator](https://hydrobuilder.com/ppfd-map-generator/)** – Hydrobuilder *(Visualização de $\Phi_{PPFD}$)*
    - **[Spectral Distribution Analyzer](https://www.led-professional.com/resources-1/tools/spectral-distribution-analyzer)** – LED professional *(Análise espectral $\lambda$)*
    """)

    st.markdown("**BANCOS DE DADOS TÉCNICOS:**")
    st.markdown("""
    - **[Plant Lighting Database](https://www.purdue.edu/hla/sites/cea/plant-lighting-database/)** – Purdue University *(Dados de $\Phi_{PPFD}$ e $Q_{DLI}$ por espécie)*
    - **[Spectral Library of Plants](https://www.ars.usda.gov/northeast-area/beltsville-md-barc/beltsville-agricultural-research-center/hydrology-and-remote-sensing-laboratory/docs/spectral-library-of-plants/)** – USDA *(Espectros de absorção $\lambda$)*
    - **[LED Spectral Database](https://www.led.com/spectral-database)** – LED manufacturers consortium *(Dados espectrais de LEDs)*
    """)

    st.markdown("**FÓRUNS E COMUNIDADES TÉCNICAS:**")
    st.markdown("""
    - **[International Light Association (ILA) Forum](https://www.internationallightassociation.org/forum)** – Discussões técnicas sobre $\Phi_{PPFD}$, $Q_{DLI}$, espectro
    - **[Controlled Environment Agriculture (CEA) Forum](https://www.ceaforum.org/)** – Agricultura em ambiente controlado
    - **[Plant Physiology Researchers Network](https://www.plantphysiology.org/community)** – ASPB, fisiologia vegetal avançada
    """)

    st.markdown("---")

    # --- SEÇÃO 5: HISTÓRICO DO SISTEMA ---
    st.markdown("#### 📜 HISTÓRICO DE VERSÕES DO SISTEMA")

    st.markdown("**VERSÃO 1.0 (ATUAL):**")
    st.markdown("""
    - Sistema completo de calibração multicanal (Vermelho, Azul, Branco)
    - Geração de arquivos `LAMP_CHx.txt` em dois formatos (Curva Gaussiana $\Phi(x)$ e ICE Linear $I_{ICE}$)
    - Visualização gráfica avançada com ECharts (Regressão, $\Phi_{PPFD}(t)$, $Q_{DLI}$, $I_{ICE}$, Gaussiana)
    - Controle de parâmetros gaussianos ($\\sigma$, $\\mu$) por canal
    - Cálculos automáticos de $Q_{DLI}$ e $I_{ICE}$
    - Interface Streamlit com navegação por abas
    """)

    st.markdown("**RECURSOS FUTUROS PLANEJADOS:**")
    st.markdown("""
    - Banco de dados de configurações por espécie (valores ótimos de $\Phi_{PPFD}$, $Q_{DLI}$, R:B)
    - Exportação em formatos adicionais (JSON, XML, CSV)
    - Relatórios automáticos de calibração em PDF
    """)

    st.markdown("---")

    # --- SEÇÃO 6: CRÉDITOS ---
    st.markdown("#### 🏆 CRÉDITOS E AGRADECIMENTOS")

    st.markdown("**DESENVOLVIMENTO E PESQUISA:**")
    st.markdown("""
    - Laboratória de Agricultura em Ambiente Controlado (LAAC)
    - Departamento de Solos
    - Universiade Federal de Viçosa (UFV)
    - EspectralInt Team 2025
                   """)

    st.markdown("**COLABORADORES:**")
    st.markdown("""
    - Jardel de Moura Fialho
    """)

    st.markdown("**APOIO INSTITUCIONAL:**")
    st.markdown("""
    - Universidade Federal de Viçosa (UFV)
    - FAPEMIG
    - CNPq
    - CAPES
    """)

    st.markdown("**CONTATO INSTITUCIONAL:**")
    st.markdown("""
    - **E-mail:** laac@ufv.br
    """)

    st.markdown("**LICENÇA DE USO:**")
    st.markdown("""
    - Uso acadêmico e de pesquisa: Livre, com citação
    - Uso comercial: Requer autorização
    - Documentação: Creative Commons Attribution 4.0
    """)

    st.markdown("**CITAÇÃO DO SISTEMA:**")
    st.code('''SISTEMA de Calibração de Bancadas LAAC - Spectral Int v1.0. 
    [Software para cálculo de PPFD, LI, ICE e curvas Gaussianas]. 
    Laboratório LAAC, Universidade Federal de Viçosa (UFV), 2026.''', language='text')

# Função auxiliar para verificação


def deve_exibir_manual():
    """
    Verifica se o manual completo deve ser exibido
    Retorna: bool - True se deve exibir, False caso contrário
    """
    return st.session_state.get('show_full_manual', False)


# Teste simples se executado diretamente
if __name__ == "__main__":
    print("📚 Manual do Sistema de Calibração de Bancadas LAAC")
    print("Este arquivo contém as funções para exibir o manual completo.")
    print("Para usar, importe e chame exibir_manual_completo()")
