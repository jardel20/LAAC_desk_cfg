import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import io
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats

# Configurar página
st.set_page_config(
    page_title="Sistema de Calibração de Bancadas",
    page_icon="🔬",
    layout="wide"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin: 5px;
        border-left: 4px solid #4CAF50;
    }
    .input-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .input-cell {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        text-align: center;
    }
    .input-label {
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


class SistemaCalibracao:
    def __init__(self):
        self.inicializar_dados()

    def inicializar_dados(self):
        """Inicializa ou carrega os dados da sessão"""
        if 'dados_bancada' not in st.session_state:
            # Dados padrão da bancada
            st.session_state.dados_bancada = {
                'azul': {
                    'dados': np.array([
                        [24.86, 29.3, 27.6, 22.53, 29.51],
                        [76.45, 74.32, 73.75, 58.78, 66.12],
                        [114.8, 106.9, 114.6, 102.9, 100.9],
                        [135.5, 127.1, 138.0, 120.2, 119.8],
                        [175.7, 177.0, 164.1, 145.0, 170.0]
                    ]).T,  # Transpor para ter 5 repetições x 5 intensidades
                    'valores_referencia': np.array([0, 0.3, 0.5, 0.7, 1.0])
                },
                'vermelho': {
                    'dados': np.array([
                        [58.12, 57.3, 54.3, 55.9, 52.0],
                        [143.9, 168.3, 160.4, 147.6, 158.1],
                        [235.3, 227.2, 198.0, 233.5, 224.5],
                        [279.5, 293.3, 272.2, 302.7, 281.7],
                        [360.5, 354.2, 407.3, 398.5, 367.8]
                    ]).T,
                    'valores_referencia': np.array([0, 0.3, 0.5, 0.7, 1.0])
                },
                'branco': {
                    'dados': np.array([
                        [20.61, 24.51, 24.24, 22.42, 23.14],
                        [62.13, 67.69, 58.93, 59.12, 55.09],
                        [69.18, 92.19, 91.02, 86.68, 84.73],
                        [109.8, 104.6, 117.0, 113.7, 110.3],
                        [120.8, 150.9, 143.3, 130.7, 143.9]
                    ]).T,
                    'valores_referencia': np.array([0, 0.3, 0.5, 0.7, 1.0])
                }
            }

        if 'parametros_canais' not in st.session_state:
            st.session_state.parametros_canais = {
                'intensidade_max_total': 650.0,
                'intensidade_min_total': 120.0,
                'proporcao_azul': 1.0,
                'proporcao_vermelho': 1.0,
                'proporcao_branco': 1.0
            }

        if 'parametros_gaussianos' not in st.session_state:
            st.session_state.parametros_gaussianos = {
                'canal_vermelho': {'sigma': 0.30, 'mi': 0.5},
                'canal_azul': {'sigma': 0.30, 'mi': -0.5},
                'canal_branco': {'sigma': 0.30, 'mi': 0.0}
            }

        if 'parametros_temporais' not in st.session_state:
            st.session_state.parametros_temporais = {
                'hora_inicio': 6,
                'hora_fim': 18,
                'n_pontos': 30
            }

        self.calcular_regressoes()

    def calcular_mediana(self, dados):
        """Calcula a mediana dos dados"""
        return np.median(dados, axis=0)

    def calcular_regressao(self, x, y):
        """Calcula regressão linear"""
        if len(x) < 2 or len(y) < 2:
            return {'a': 0, 'b': 0, 'r2': 0, 'r': 0, 'p_value': 1, 'std_err': 0}

        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return {
            'a': slope,
            'b': intercept,
            'r2': r_value**2,
            'r': r_value,
            'p_value': p_value,
            'std_err': std_err
        }

    def calcular_regressoes(self):
        """Calcula todas as regressões"""
        self.regressoes = {}

        for canal in ['azul', 'vermelho', 'branco']:
            dados = st.session_state.dados_bancada[canal]
            medianas = self.calcular_mediana(dados['dados'])
            x = dados['valores_referencia']

            regressao = self.calcular_regressao(x, medianas)
            valores_previstos = regressao['a'] * x + regressao['b']

            self.regressoes[canal] = {
                'medianas': medianas,
                'regressao': regressao,
                'valores_previstos': valores_previstos
            }

    def calcular_gaussiana(self, x, sigma, mi, intensidade_max, intensidade_min):
        """Calcula a distribuição gaussiana"""
        return intensidade_min + (intensidade_max - intensidade_min) * np.exp(-((x - mi)**2) / (2 * sigma**2))

    def gerar_dados_canal(self, canal, sigma, mi):
        """Gera dados para um canal específico"""
        params = st.session_state.parametros_canais
        tempo = st.session_state.parametros_temporais

        # Calcular intensidades por canal
        max_proporcao = max(
            params['proporcao_azul'], params['proporcao_vermelho'], params['proporcao_branco'])

        if canal == 'vermelho':
            proporcao_norm = params['proporcao_vermelho'] / max_proporcao
        elif canal == 'azul':
            proporcao_norm = params['proporcao_azul'] / max_proporcao
        else:
            proporcao_norm = params['proporcao_branco'] / max_proporcao

        soma_proporcoes = (params['proporcao_azul'] + params['proporcao_vermelho'] +
                           params['proporcao_branco']) / max_proporcao

        intensidade_max = params['intensidade_max_total'] / \
            soma_proporcoes * proporcao_norm
        intensidade_min = params['intensidade_min_total'] / \
            soma_proporcoes * proporcao_norm

        # Gerar pontos
        x_vals = np.linspace(-1, 1, tempo['n_pontos'])
        horas_decimais = np.linspace(
            tempo['hora_inicio'], tempo['hora_fim'], tempo['n_pontos'])

        # Calcular intensidades
        intensidades = self.calcular_gaussiana(
            x_vals, sigma, mi, intensidade_max, intensidade_min)

        # Calcular integral
        delta_t_segundos = (
            tempo['hora_fim'] - tempo['hora_inicio']) * 3600 / (tempo['n_pontos'] - 1)
        integral = np.cumsum(intensidades) * delta_t_segundos / 1_000_000

        # Calcular ICE e DLI
        dli_final = integral[-1]
        fotoperiodo_segundos = (
            tempo['hora_fim'] - tempo['hora_inicio']) * 3600
        ice = dli_final * 1_000_000 / fotoperiodo_segundos if fotoperiodo_segundos > 0 else 0

        return {
            'x': x_vals,
            'hora_decimal': horas_decimais,
            'Intensidade': intensidades,
            'Integral': integral,
            'DLI_final': dli_final,
            'ICE': ice,
            'intensidade_max': intensidade_max,
            'intensidade_min': intensidade_min
        }

    def get_dados_canal(self, canal):
        """Obtém dados de um canal específico"""
        params_gauss = st.session_state.parametros_gaussianos[f'canal_{canal}']
        return self.gerar_dados_canal(canal, params_gauss['sigma'], params_gauss['mi'])

    def exportar_para_excel(self):
        """Exporta todos os dados para Excel"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Planilha bancada
            self.exportar_bancada(writer)

            # Planilhas dos canais
            for canal in ['vermelho', 'azul', 'branco']:
                self.exportar_canal(writer, canal)

            # Planilha configurar canais
            self.exportar_configurar_canais(writer)

        output.seek(0)
        return output

    def exportar_bancada(self, writer):
        """Exporta dados da bancada"""
        bancada_data = []

        for canal in ['azul', 'vermelho', 'branco']:
            # Cabeçalho
            nome_canal = canal.capitalize()
            bancada_data.append(
                ['', f'PPFD medidos {nome_canal}', '', '', '', '', 'f(x) = aX+b', ''])

            dados = st.session_state.dados_bancada[canal]
            reg = self.regressoes[canal]

            # Dados das repetições
            for i in range(5):
                row = [f'Repetição {i+1}'] + list(dados['dados'][i]) + [
                    '', '', f"{reg['regressao']['a']:.6f}" if i == 0 else '']
                bancada_data.append(row)

            bancada_data.append(
                ['', '', '', '', '', '', '', f"{reg['regressao']['b']:.6f}"])
            bancada_data.append([''])

        bancada_df = pd.DataFrame(bancada_data)
        bancada_df.to_excel(writer, sheet_name='bancada',
                            index=False, header=False)

    def exportar_canal(self, writer, canal_nome):
        """Exporta dados de um canal"""
        dados = self.get_dados_canal(canal_nome)
        params_gauss = st.session_state.parametros_gaussianos[f'canal_{canal_nome}']
        tempo = st.session_state.parametros_temporais

        # Cabeçalho
        header_data = [
            ['sigma', params_gauss['sigma']],
            ['mi', params_gauss['mi']],
            ['Intensidade Maxima (umol/m2/s)', dados['intensidade_max']],
            ['Intensidade Minima (umol/m2/s)', dados['intensidade_min']],
            ['Hora Inicio', f"{tempo['hora_inicio']:02d}:00:00"],
            ['Hora Fim', f"{tempo['hora_fim']:02d}:00:00"],
            ['Quantidade de pontos', tempo['n_pontos']]
        ]

        # Dados
        table_data = []
        for i in range(tempo['n_pontos']):
            table_data.append([
                dados['x'][i],
                dados['hora_decimal'][i],
                f"{dados['hora_decimal'][i]:.2f}",
                dados['Intensidade'][i],
                dados['Integral'][i]
            ])

        # Combinar
        full_data = header_data + [['']] + table_data

        canal_df = pd.DataFrame(full_data)
        canal_df.to_excel(
            writer, sheet_name=f'canal_{canal_nome}', index=False, header=False)

    def exportar_configurar_canais(self, writer):
        """Exporta configuração dos canais"""
        params = st.session_state.parametros_canais

        config_data = [
            ['', 'Intensidade total (umol/m2/s)', '',
             'proporção entre canais', '', '', '', 'LEGENDA'],
            ['', 'máxima', 'mínima', 'azul', 'vermelho',
                'branco', '', 'CH1 - vermelho'],
            ['escolhido', params['intensidade_max_total'], params['intensidade_min_total'],
             params['proporcao_azul'], params['proporcao_vermelho'], params['proporcao_branco'],
             max(params['proporcao_azul'], params['proporcao_vermelho'],
                 params['proporcao_branco']),
             'CH2 - azul'],
            ['', '', '', '', '', '', '', 'CH3 - branco']
        ]

        config_df = pd.DataFrame(config_data)
        config_df.to_excel(
            writer, sheet_name='configurar canais', index=False, header=False)


# Inicializar sistema
sistema = SistemaCalibracao()

# Título principal
st.title("🔬 Sistema de Calibração de Bancadas")
st.markdown("---")

# Barra lateral
with st.sidebar:
    st.header("⚙️ Navegação")

    # Usar tabs para navegação
    aba_selecionada = st.radio(
        "Selecione a seção:",
        ["📊 Visão Geral",
         "🧪 Calibração Bancada",
         "🔴 Canal Vermelho",
         "🔵 Canal Azul",
         "⚪ Canal Branco",
         "🔄 Configurar Canais",
         "📈 Gráficos Comparativos",
         "💾 Exportar Dados"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if aba_selecionada != "🧪 Calibração Bancada":
        st.header("⚡ Configurações Rápidas")

        with st.expander("⏰ Horários"):
            hora_inicio = st.number_input("Hora Início", 0, 23,
                                          st.session_state.parametros_temporais['hora_inicio'],
                                          key="hora_inicio_sidebar")
            hora_fim = st.number_input("Hora Fim", 0, 23,
                                       st.session_state.parametros_temporais['hora_fim'],
                                       key="hora_fim_sidebar")
            n_pontos = st.number_input("Nº de Pontos", 10, 200,
                                       st.session_state.parametros_temporais['n_pontos'],
                                       key="n_pontos_sidebar")

            if (hora_inicio != st.session_state.parametros_temporais['hora_inicio'] or
                hora_fim != st.session_state.parametros_temporais['hora_fim'] or
                    n_pontos != st.session_state.parametros_temporais['n_pontos']):
                st.session_state.parametros_temporais.update({
                    'hora_inicio': hora_inicio,
                    'hora_fim': hora_fim,
                    'n_pontos': n_pontos
                })
                st.rerun()

        with st.expander("📐 Gaussianas"):
            col1, col2 = st.columns(2)
            with col1:
                sigma_vermelho = st.slider("σ Vermelho", 0.1, 1.0,
                                           st.session_state.parametros_gaussianos['canal_vermelho']['sigma'],
                                           0.05, key="sigma_v_sidebar")
                sigma_azul = st.slider("σ Azul", 0.1, 1.0,
                                       st.session_state.parametros_gaussianos['canal_azul']['sigma'],
                                       0.05, key="sigma_a_sidebar")
                sigma_branco = st.slider("σ Branco", 0.1, 1.0,
                                         st.session_state.parametros_gaussianos['canal_branco']['sigma'],
                                         0.05, key="sigma_b_sidebar")

            with col2:
                mi_vermelho = st.slider("μ Vermelho", -1.0, 1.0,
                                        st.session_state.parametros_gaussianos['canal_vermelho']['mi'],
                                        0.1, key="mi_v_sidebar")
                mi_azul = st.slider("μ Azul", -1.0, 1.0,
                                    st.session_state.parametros_gaussianos['canal_azul']['mi'],
                                    0.1, key="mi_a_sidebar")
                mi_branco = st.slider("μ Branco", -1.0, 1.0,
                                      st.session_state.parametros_gaussianos['canal_branco']['mi'],
                                      0.1, key="mi_b_sidebar")

            if (sigma_vermelho != st.session_state.parametros_gaussianos['canal_vermelho']['sigma'] or
                sigma_azul != st.session_state.parametros_gaussianos['canal_azul']['sigma'] or
                sigma_branco != st.session_state.parametros_gaussianos['canal_branco']['sigma'] or
                mi_vermelho != st.session_state.parametros_gaussianos['canal_vermelho']['mi'] or
                mi_azul != st.session_state.parametros_gaussianos['canal_azul']['mi'] or
                    mi_branco != st.session_state.parametros_gaussianos['canal_branco']['mi']):

                st.session_state.parametros_gaussianos.update({
                    'canal_vermelho': {'sigma': sigma_vermelho, 'mi': mi_vermelho},
                    'canal_azul': {'sigma': sigma_azul, 'mi': mi_azul},
                    'canal_branco': {'sigma': sigma_branco, 'mi': mi_branco}
                })
                st.rerun()

# Funções para cada aba


def exibir_visao_geral():
    """Exibe a visão geral do sistema"""

    # Métricas principais
    st.header("📊 Visão Geral do Sistema")

    # Obter dados dos canais
    dados_vermelho = sistema.get_dados_canal('vermelho')
    dados_azul = sistema.get_dados_canal('azul')
    dados_branco = sistema.get_dados_canal('branco')

    # Métricas em tempo real
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "DLI Vermelho",
            f"{dados_vermelho['DLI_final']:.2f} mol/m²",
            delta=f"ICE: {dados_vermelho['ICE']:.1f} μmol/m²/s"
        )

    with col2:
        st.metric(
            "DLI Azul",
            f"{dados_azul['DLI_final']:.2f} mol/m²",
            delta=f"ICE: {dados_azul['ICE']:.1f} μmol/m²/s"
        )

    with col3:
        st.metric(
            "DLI Branco",
            f"{dados_branco['DLI_final']:.2f} mol/m²",
            delta=f"ICE: {dados_branco['ICE']:.1f} μmol/m²/s"
        )

    with col4:
        params = st.session_state.parametros_canais
        st.metric(
            "Intensidade Máx Total",
            f"{params['intensidade_max_total']:.0f} μmol/m²/s",
            delta=f"Mín: {params['intensidade_min_total']:.0f} μmol/m²/s"
        )

    st.markdown("---")

    # Regressões da bancada
    st.header("📐 Regressões Lineares da Bancada")

    tabs = st.tabs(["Azul", "Vermelho", "Branco"])

    for idx, (canal_nome, tab) in enumerate(zip(['azul', 'vermelho', 'branco'], tabs)):
        with tab:
            reg = sistema.regressoes[canal_nome]

            col1, col2 = st.columns([2, 1])

            with col1:
                # Gráfico de regressão com Plotly
                x = st.session_state.dados_bancada[canal_nome]['valores_referencia']
                y_medido = reg['medianas']
                y_previsto = reg['valores_previstos']

                fig = go.Figure()

                # Pontos medidos
                fig.add_trace(go.Scatter(
                    x=x, y=y_medido,
                    mode='markers',
                    name='Dados medidos',
                    marker=dict(
                        size=10,
                        color='red' if canal_nome == 'vermelho' else
                              'blue' if canal_nome == 'azul' else 'gray',
                        line=dict(width=1, color='DarkSlateGrey')
                    )
                ))

                # Linha de regressão
                fig.add_trace(go.Scatter(
                    x=x, y=y_previsto,
                    mode='lines',
                    name='Regressão linear',
                    line=dict(color='black', width=2)
                ))

                # Configurações do gráfico
                fig.update_layout(
                    title=f'Regressão Linear - Canal {canal_nome.capitalize()}',
                    xaxis_title='Valor de Referência',
                    yaxis_title='PPFD Medido (μmol/m²/s)',
                    hovermode='x unified',
                    height=400,
                    showlegend=True,
                    template='plotly_white'
                )

                # Adicionar equação no gráfico
                eq_text = f"y = {reg['regressao']['a']:.3f}x + {reg['regressao']['b']:.3f}<br>R² = {reg['regressao']['r2']:.4f}"
                fig.add_annotation(
                    x=0.05, y=0.95,
                    xref="paper", yref="paper",
                    text=eq_text,
                    showarrow=False,
                    font=dict(size=12),
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1,
                    borderpad=4
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Estatísticas da regressão
                st.subheader("Estatísticas")

                stats_data = {
                    'Parâmetro': ['Coef. Angular (a)', 'Coef. Linear (b)',
                                  'R²', 'R', 'p-value', 'Erro Padrão'],
                    'Valor': [
                        f"{reg['regressao']['a']:.4f}",
                        f"{reg['regressao']['b']:.4f}",
                        f"{reg['regressao']['r2']:.4f}",
                        f"{reg['regressao']['r']:.4f}",
                        f"{reg['regressao']['p_value']:.4e}" if reg['regressao']['p_value'] > 0 else "0.0000",
                        f"{reg['regressao']['std_err']:.4f}"
                    ]
                }

                st.dataframe(pd.DataFrame(stats_data),
                             hide_index=True, use_container_width=True)

                # Informações adicionais
                st.info(f"""
                **Canal {canal_nome.capitalize()}**
                - **Mediana máxima:** {max(reg['medianas']):.1f} μmol/m²/s
                - **Mediana mínima:** {min(reg['medianas']):.1f} μmol/m²/s
                - **Amplitude:** {max(reg['medianas']) - min(reg['medianas']):.1f} μmol/m²/s
                """)

    st.markdown("---")

    # Gráfico comparativo de intensidades
    st.header("⚡ Comparação de Intensidades dos Canais")

    fig = go.Figure()

    for canal_nome, cor, nome in [('vermelho', 'red', 'Vermelho'),
                                  ('azul', 'blue', 'Azul'),
                                  ('branco', 'gray', 'Branco')]:
        dados = sistema.get_dados_canal(canal_nome)

        fig.add_trace(go.Scatter(
            x=dados['hora_decimal'],
            y=dados['Intensidade'],
            mode='lines',
            name=nome,
            line=dict(color=cor, width=2),
            hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
        ))

    fig.update_layout(
        title='Intensidade dos Canais ao Longo do Dia',
        xaxis_title='Hora do Dia',
        yaxis_title='Intensidade (μmol/m²/s)',
        hovermode='x unified',
        height=500,
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)


def exibir_calibracao_bancada():
    """Exibe a interface de calibração da bancada"""
    st.header("🧪 Calibração da Bancada")

    # Selecionar canal
    canal_selecionado = st.selectbox(
        "Selecione o canal para calibração:",
        ["Azul", "Vermelho", "Branco"],
        key="canal_calibracao"
    )

    canal_key = canal_selecionado.lower()
    dados_canal = st.session_state.dados_bancada[canal_key]

    st.subheader(f"📋 Entrada de Dados - Canal {canal_selecionado}")
    st.markdown(
        "**Instruções:** Insira os valores de PPFD medidos para cada repetição e intensidade.")

    # Criar interface de entrada de dados
    col1, col2 = st.columns([3, 1])

    with col1:
        # Valores de referência
        st.markdown("**Valores de Referência:**")
        ref_vals = dados_canal['valores_referencia']

        # Grid de entrada
        st.markdown("<div class='input-grid'>", unsafe_allow_html=True)

        # Cabeçalho
        cols = st.columns(6)
        with cols[0]:
            st.markdown("<div class='input-label'>Repetição</div>",
                        unsafe_allow_html=True)
        for i in range(5):
            with cols[i+1]:
                st.markdown(f"<div class='input-label'>Intensidade {i+1}<br>(Ref: {ref_vals[i]})</div>",
                            unsafe_allow_html=True)

        # Linhas de dados
        for rep in range(5):
            cols = st.columns(6)
            with cols[0]:
                st.markdown(
                    f"<div class='input-label'>Repetição {rep+1}</div>", unsafe_allow_html=True)

            for intens in range(5):
                with cols[intens+1]:
                    # Criar chave única para cada campo
                    key = f"input_{canal_key}_{rep}_{intens}"

                    # Usar st.number_input com formatação
                    valor = st.number_input(
                        "",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(dados_canal['dados'][rep, intens]),
                        step=0.1,
                        format="%.2f",
                        key=key,
                        label_visibility="collapsed"
                    )

                    # Atualizar dados se houver mudança
                    if valor != dados_canal['dados'][rep, intens]:
                        dados_canal['dados'][rep, intens] = valor
                        sistema.calcular_regressoes()

    with col2:
        # Estatísticas rápidas
        st.subheader("📊 Estatísticas")

        medianas = sistema.regressoes[canal_key]['medianas']
        reg = sistema.regressoes[canal_key]['regressao']

        st.metric("Mediana Máxima", f"{max(medianas):.2f}")
        st.metric("Mediana Mínima", f"{min(medianas):.2f}")
        st.metric("Coef. Angular (a)", f"{reg['a']:.4f}")
        st.metric("Coef. Linear (b)", f"{reg['b']:.4f}")
        st.metric("R²", f"{reg['r2']:.4f}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Visualização gráfica em tempo real
    st.subheader("📈 Visualização em Tempo Real")

    fig = go.Figure()

    # Plotar todas as repetições
    for rep in range(5):
        fig.add_trace(go.Scatter(
            x=ref_vals,
            y=dados_canal['dados'][rep, :],
            mode='markers',
            name=f'Repetição {rep+1}',
            marker=dict(size=8, opacity=0.7),
            showlegend=True
        ))

    # Plotar mediana
    fig.add_trace(go.Scatter(
        x=ref_vals,
        y=medianas,
        mode='lines+markers',
        name='Mediana',
        line=dict(color='black', width=3),
        marker=dict(size=12, color='black')
    ))

    # Plotar regressão
    y_previsto = sistema.regressoes[canal_key]['valores_previstos']
    fig.add_trace(go.Scatter(
        x=ref_vals,
        y=y_previsto,
        mode='lines',
        name='Regressão',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f'Dados de Calibração - Canal {canal_selecionado}',
        xaxis_title='Valor de Referência',
        yaxis_title='PPFD Medido (μmol/m²/s)',
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Botão para resetar dados
    if st.button("🔄 Resetar para Valores Padrão"):
        st.session_state.dados_bancada[canal_key]['dados'] = np.array([
            [24.86, 29.3, 27.6, 22.53, 29.51],
            [76.45, 74.32, 73.75, 58.78, 66.12],
            [114.8, 106.9, 114.6, 102.9, 100.9],
            [135.5, 127.1, 138.0, 120.2, 119.8],
            [175.7, 177.0, 164.1, 145.0, 170.0]
        ]).T if canal_key == 'azul' else np.array([
            [58.12, 57.3, 54.3, 55.9, 52.0],
            [143.9, 168.3, 160.4, 147.6, 158.1],
            [235.3, 227.2, 198.0, 233.5, 224.5],
            [279.5, 293.3, 272.2, 302.7, 281.7],
            [360.5, 354.2, 407.3, 398.5, 367.8]
        ]).T if canal_key == 'vermelho' else np.array([
            [20.61, 24.51, 24.24, 22.42, 23.14],
            [62.13, 67.69, 58.93, 59.12, 55.09],
            [69.18, 92.19, 91.02, 86.68, 84.73],
            [109.8, 104.6, 117.0, 113.7, 110.3],
            [120.8, 150.9, 143.3, 130.7, 143.9]
        ]).T
        sistema.calcular_regressoes()
        st.rerun()


def exibir_canal_detalhes(canal_nome, emoji, nome_display):
    """Exibe detalhes de um canal específico"""
    st.header(f"{emoji} Canal {nome_display}")

    # Obter dados do canal
    dados = sistema.get_dados_canal(canal_nome)
    params_gauss = st.session_state.parametros_gaussianos[f'canal_{canal_nome}']
    params_temp = st.session_state.parametros_temporais

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Intensidade Máx",
                  f"{dados['intensidade_max']:.1f} μmol/m²/s")
        st.metric("Hora Início", f"{params_temp['hora_inicio']:02d}:00")

    with col2:
        st.metric("Intensidade Mín",
                  f"{dados['intensidade_min']:.1f} μmol/m²/s")
        st.metric("Hora Fim", f"{params_temp['hora_fim']:02d}:00")

    with col3:
        st.metric("DLI Final", f"{dados['DLI_final']:.3f} mol/m²")
        st.metric("Fotoperíodo",
                  f"{params_temp['hora_fim'] - params_temp['hora_inicio']}h")

    with col4:
        st.metric("ICE", f"{dados['ICE']:.2f} μmol/m²/s")
        st.metric("Nº Pontos", params_temp['n_pontos'])

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de intensidade
        fig1 = go.Figure()

        fig1.add_trace(go.Scatter(
            x=dados['hora_decimal'],
            y=dados['Intensidade'],
            mode='lines',
            name='Intensidade',
            line=dict(color='red' if canal_nome == 'vermelho' else
                      'blue' if canal_nome == 'azul' else 'gray', width=3),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.1)' if canal_nome == 'vermelho' else
            'rgba(0,0,255,0.1)' if canal_nome == 'azul' else 'rgba(128,128,128,0.1)',
            hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
        ))

        fig1.update_layout(
            title=f'Intensidade - Canal {nome_display}',
            xaxis_title='Hora do Dia',
            yaxis_title='Intensidade (μmol/m²/s)',
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Gráfico da integral
        fig2 = go.Figure()

        fig2.add_trace(go.Scatter(
            x=dados['hora_decimal'],
            y=dados['Integral'],
            mode='lines',
            name='Integral',
            line=dict(color='red' if canal_nome == 'vermelho' else
                      'blue' if canal_nome == 'azul' else 'gray', width=3),
            hovertemplate='Hora: %{x:.2f}<br>Integral: %{y:.4f} mol/m²'
        ))

        fig2.update_layout(
            title=f'Integral Acumulada (DLI) - Canal {nome_display}',
            xaxis_title='Hora do Dia',
            yaxis_title='Integral (mol/m²)',
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig2, use_container_width=True)

    # Gráfico da distribuição gaussiana
    st.subheader(f"📊 Distribuição Gaussiana")

    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=dados['x'],
        y=dados['Intensidade'],
        mode='lines',
        name='Distribuição',
        line=dict(color='red' if canal_nome == 'vermelho' else
                  'blue' if canal_nome == 'azul' else 'gray', width=3),
        fill='tozeroy',
        fillcolor='rgba(255,0,0,0.1)' if canal_nome == 'vermelho' else
        'rgba(0,0,255,0.1)' if canal_nome == 'azul' else 'rgba(128,128,128,0.1)',
        hovertemplate='x: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    # Adicionar linhas para μ e ±σ
    fig3.add_vline(x=params_gauss['mi'], line_dash="dash", line_color="black",
                   annotation_text=f"μ = {params_gauss['mi']}")

    sigma_pos = params_gauss['mi'] + params_gauss['sigma']
    sigma_neg = params_gauss['mi'] - params_gauss['sigma']

    fig3.add_vline(x=sigma_pos, line_dash="dot",
                   line_color="gray", opacity=0.7)
    fig3.add_vline(x=sigma_neg, line_dash="dot",
                   line_color="gray", opacity=0.7)

    fig3.update_layout(
        title=f'Distribuição Gaussiana - {nome_display} (σ={params_gauss["sigma"]}, μ={params_gauss["mi"]})',
        xaxis_title='x (domínio normalizado)',
        yaxis_title='Intensidade (μmol/m²/s)',
        height=400,
        template='plotly_white'
    )

    st.plotly_chart(fig3, use_container_width=True)


def exibir_configurar_canais():
    """Exibe a interface para configurar os canais"""
    st.header("🔄 Configurar Canais")

    st.info("""
    **Atenção:** A proporção escolhida aqui é entre canais físicos de LEDs, 
    **NÃO** é de banda espectral.
    """)

    # Formulário de configuração
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Intensidades Totais")

        intensidade_max_total = st.number_input(
            "Intensidade Total Máxima (μmol/m²/s)",
            min_value=0.0,
            max_value=2000.0,
            value=st.session_state.parametros_canais['intensidade_max_total'],
            step=10.0,
            key="int_max_total"
        )

        intensidade_min_total = st.number_input(
            "Intensidade Total Mínima (μmol/m²/s)",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state.parametros_canais['intensidade_min_total'],
            step=10.0,
            key="int_min_total"
        )

    with col2:
        st.subheader("📊 Proporções entre Canais")

        proporcao_azul = st.slider(
            "Proporção Azul",
            min_value=0.0,
            max_value=5.0,
            value=st.session_state.parametros_canais['proporcao_azul'],
            step=0.1,
            key="prop_azul"
        )

        proporcao_vermelho = st.slider(
            "Proporção Vermelho",
            min_value=0.0,
            max_value=5.0,
            value=st.session_state.parametros_canais['proporcao_vermelho'],
            step=0.1,
            key="prop_vermelho"
        )

        proporcao_branco = st.slider(
            "Proporção Branco",
            min_value=0.0,
            max_value=5.0,
            value=st.session_state.parametros_canais['proporcao_branco'],
            step=0.1,
            key="prop_branco"
        )

    # Atualizar parâmetros em tempo real
    if (intensidade_max_total != st.session_state.parametros_canais['intensidade_max_total'] or
        intensidade_min_total != st.session_state.parametros_canais['intensidade_min_total'] or
        proporcao_azul != st.session_state.parametros_canais['proporcao_azul'] or
        proporcao_vermelho != st.session_state.parametros_canais['proporcao_vermelho'] or
            proporcao_branco != st.session_state.parametros_canais['proporcao_branco']):

        st.session_state.parametros_canais.update({
            'intensidade_max_total': intensidade_max_total,
            'intensidade_min_total': intensidade_min_total,
            'proporcao_azul': proporcao_azul,
            'proporcao_vermelho': proporcao_vermelho,
            'proporcao_branco': proporcao_branco
        })

    st.markdown("---")

    # Resultados da configuração
    st.header("📊 Resultados da Configuração")

    # Calcular intensidades por canal
    max_proporcao = max(proporcao_azul, proporcao_vermelho, proporcao_branco)
    proporcao_azul_norm = proporcao_azul / max_proporcao
    proporcao_vermelho_norm = proporcao_vermelho / max_proporcao
    proporcao_branco_norm = proporcao_branco / max_proporcao

    soma_proporcoes = proporcao_azul_norm + \
        proporcao_vermelho_norm + proporcao_branco_norm

    intensidade_max_azul = intensidade_max_total / \
        soma_proporcoes * proporcao_azul_norm
    intensidade_max_vermelho = intensidade_max_total / \
        soma_proporcoes * proporcao_vermelho_norm
    intensidade_max_branco = intensidade_max_total / \
        soma_proporcoes * proporcao_branco_norm

    intensidade_min_azul = intensidade_min_total / \
        soma_proporcoes * proporcao_azul_norm
    intensidade_min_vermelho = intensidade_min_total / \
        soma_proporcoes * proporcao_vermelho_norm
    intensidade_min_branco = intensidade_min_total / \
        soma_proporcoes * proporcao_branco_norm

    # Exibir resultados
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Azul - Máx", f"{intensidade_max_azul:.1f} μmol/m²/s")
        st.metric("Azul - Mín", f"{intensidade_min_azul:.1f} μmol/m²/s")

    with col2:
        st.metric("Vermelho - Máx",
                  f"{intensidade_max_vermelho:.1f} μmol/m²/s")
        st.metric("Vermelho - Mín",
                  f"{intensidade_min_vermelho:.1f} μmol/m²/s")

    with col3:
        st.metric("Branco - Máx", f"{intensidade_max_branco:.1f} μmol/m²/s")
        st.metric("Branco - Mín", f"{intensidade_min_branco:.1f} μmol/m²/s")

    # Gráfico de barras comparativo
    st.subheader("📈 Comparação de Intensidades Máximas")

    fig = go.Figure(data=[
        go.Bar(
            name='Máxima',
            x=['Azul', 'Vermelho', 'Branco'],
            y=[intensidade_max_azul, intensidade_max_vermelho,
                intensidade_max_branco],
            marker_color=['blue', 'red', 'gray']
        ),
        go.Bar(
            name='Mínima',
            x=['Azul', 'Vermelho', 'Branco'],
            y=[intensidade_min_azul, intensidade_min_vermelho,
                intensidade_min_branco],
            marker_color=['lightblue', 'lightcoral', 'lightgray']
        )
    ])

    fig.update_layout(
        barmode='group',
        title='Intensidades por Canal',
        yaxis_title='Intensidade (μmol/m²/s)',
        height=400,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)


def exibir_graficos_comparativos():
    """Exibe gráficos comparativos entre os canais"""
    st.header("📈 Gráficos Comparativos")

    # Obter dados dos canais
    dados_vermelho = sistema.get_dados_canal('vermelho')
    dados_azul = sistema.get_dados_canal('azul')
    dados_branco = sistema.get_dados_canal('branco')

    # Gráfico 1: Intensidades comparadas
    st.subheader("⚡ Intensidade dos Canais")

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=dados_vermelho['hora_decimal'],
        y=dados_vermelho['Intensidade'],
        mode='lines',
        name='Vermelho',
        line=dict(color='red', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    fig1.add_trace(go.Scatter(
        x=dados_azul['hora_decimal'],
        y=dados_azul['Intensidade'],
        mode='lines',
        name='Azul',
        line=dict(color='blue', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    fig1.add_trace(go.Scatter(
        x=dados_branco['hora_decimal'],
        y=dados_branco['Intensidade'],
        mode='lines',
        name='Branco',
        line=dict(color='gray', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    fig1.update_layout(
        title='Intensidade dos Canais ao Longo do Dia',
        xaxis_title='Hora do Dia',
        yaxis_title='Intensidade (μmol/m²/s)',
        hovermode='x unified',
        height=500,
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
        template='plotly_white'
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Integrais comparadas
    st.subheader("📊 Integral Acumulada (DLI)")

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=dados_vermelho['hora_decimal'],
        y=dados_vermelho['Integral'],
        mode='lines',
        name='Vermelho',
        line=dict(color='red', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Integral: %{y:.4f} mol/m²'
    ))

    fig2.add_trace(go.Scatter(
        x=dados_azul['hora_decimal'],
        y=dados_azul['Integral'],
        mode='lines',
        name='Azul',
        line=dict(color='blue', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Integral: %{y:.4f} mol/m²'
    ))

    fig2.add_trace(go.Scatter(
        x=dados_branco['hora_decimal'],
        y=dados_branco['Integral'],
        mode='lines',
        name='Branco',
        line=dict(color='gray', width=2),
        hovertemplate='Hora: %{x:.2f}<br>Integral: %{y:.4f} mol/m²'
    ))

    fig2.update_layout(
        title='Integral de Luz Acumulada (DLI)',
        xaxis_title='Hora do Dia',
        yaxis_title='Integral (mol/m²)',
        hovermode='x unified',
        height=500,
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
        template='plotly_white'
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3: DLIs finais comparados
    st.subheader("📋 DLIs Finais por Canal")

    dli_data = {
        'Canal': ['Vermelho', 'Azul', 'Branco'],
        'DLI Final (mol/m²)': [
            dados_vermelho['DLI_final'],
            dados_azul['DLI_final'],
            dados_branco['DLI_final']
        ],
        'ICE (μmol/m²/s)': [
            dados_vermelho['ICE'],
            dados_azul['ICE'],
            dados_branco['ICE']
        ]
    }

    df_dli = pd.DataFrame(dli_data)

    col1, col2 = st.columns(2)

    with col1:
        fig3 = go.Figure(data=[
            go.Bar(
                x=df_dli['Canal'],
                y=df_dli['DLI Final (mol/m²)'],
                marker_color=['red', 'blue', 'gray'],
                text=df_dli['DLI Final (mol/m²)'].round(3),
                textposition='outside'
            )
        ])

        fig3.update_layout(
            title='DLI Final por Canal',
            yaxis_title='DLI Final (mol/m²)',
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = go.Figure(data=[
            go.Bar(
                x=df_dli['Canal'],
                y=df_dli['ICE (μmol/m²/s)'],
                marker_color=['red', 'blue', 'gray'],
                text=df_dli['ICE (μmol/m²/s)'].round(1),
                textposition='outside'
            )
        ])

        fig4.update_layout(
            title='ICE por Canal',
            yaxis_title='ICE (μmol/m²/s)',
            height=400,
            template='plotly_white'
        )

        st.plotly_chart(fig4, use_container_width=True)

    # Tabela resumo
    st.subheader("📊 Resumo dos Canais")
    st.dataframe(df_dli, use_container_width=True)


def exibir_exportar_dados():
    """Exibe a interface para exportar dados"""
    st.header("💾 Exportar Dados para Excel")

    st.info("""
    Clique no botão abaixo para gerar um arquivo Excel contendo todas as planilhas,
    fiel à planilha original. O arquivo incluirá:
    
    - **bancada**: Dados de calibração e regressões lineares
    - **canal_vermelho**: Dados do canal vermelho com gaussiana
    - **canal_azul**: Dados do canal azul com gaussiana
    - **canal_branco**: Dados do canal branco com gaussiana
    - **configurar canais**: Configuração de proporções e dados combinados
    """)

    # Botão para exportar
    if st.button("📥 Gerar Arquivo Excel Completo", type="primary", use_container_width=True):
        with st.spinner("Gerando arquivo Excel..."):
            excel_data = sistema.exportar_para_excel()

            st.success("✅ Arquivo Excel gerado com sucesso!")

            st.download_button(
                label="⬇️ Baixar Arquivo Excel",
                data=excel_data,
                file_name="calibracao_bancadas_completa.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

    st.markdown("---")

    # Pré-visualização dos dados
    st.subheader("🔍 Pré-visualização dos Dados")

    planilha_preview = st.selectbox(
        "Selecione a planilha para pré-visualizar:",
        ["bancada", "canal_vermelho", "canal_azul", "canal_branco"]
    )

    if planilha_preview == "bancada":
        # Pré-visualização da bancada
        st.write("**Dados da Bancada - Canal Azul**")

        dados = st.session_state.dados_bancada['azul']['dados']
        df_preview = pd.DataFrame(
            dados,
            columns=[f'Intensidade {i+1}' for i in range(5)],
            index=[f'Repetição {i+1}' for i in range(5)]
        )

        st.dataframe(df_preview.style.format(
            "{:.2f}"), use_container_width=True)

    elif planilha_preview.startswith('canal_'):
        canal_nome = planilha_preview.split('_')[1]
        dados = sistema.get_dados_canal(canal_nome)

        st.write(f"**{planilha_preview} - Primeiras 10 linhas**")

        preview_data = []
        for i in range(min(10, st.session_state.parametros_temporais['n_pontos'])):
            preview_data.append({
                'x': dados['x'][i],
                'Hora': f"{dados['hora_decimal'][i]:.2f}",
                'Intensidade': f"{dados['Intensidade'][i]:.2f}",
                'Integral': f"{dados['Integral'][i]:.6f}"
            })

        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)


# Roteamento das abas
if aba_selecionada == "📊 Visão Geral":
    exibir_visao_geral()

elif aba_selecionada == "🧪 Calibração Bancada":
    exibir_calibracao_bancada()

elif aba_selecionada == "🔴 Canal Vermelho":
    exibir_canal_detalhes('vermelho', '🔴', 'Vermelho')

elif aba_selecionada == "🔵 Canal Azul":
    exibir_canal_detalhes('azul', '🔵', 'Azul')

elif aba_selecionada == "⚪ Canal Branco":
    exibir_canal_detalhes('branco', '⚪', 'Branco')

elif aba_selecionada == "🔄 Configurar Canais":
    exibir_configurar_canais()

elif aba_selecionada == "📈 Gráficos Comparativos":
    exibir_graficos_comparativos()

elif aba_selecionada == "💾 Exportar Dados":
    exibir_exportar_dados()

# Rodapé
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🔬 Sistema de Calibração de Bancadas | Desenvolvido para Laboratório de LAAC"
    "</div>",
    unsafe_allow_html=True
)
