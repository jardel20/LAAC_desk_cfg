import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import io
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from scipy.interpolate import interp1d

# Configurar página
st.set_page_config(
    page_title="Sistema de Calibração de Bancadas LAAC - Spectral Int",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Usar tema padrão do Streamlit


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
                'n_pontos': 60  # Aumentado para linhas mais suaves
            }

        self.calcular_regressoes()

    def calcular_mediana(self, dados):
        """Calcula a mediana dos dados"""
        return np.median(dados, axis=0)

    def calcular_media(self, dados):
        """Calcula a média dos dados"""
        return np.mean(dados, axis=0)

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
            medias = self.calcular_media(dados['dados'])
            x = dados['valores_referencia']

            # Calcular regressão usando medianas
            regressao_mediana = self.calcular_regressao(x, medianas)
            valores_previstos_mediana = regressao_mediana['a'] * \
                x + regressao_mediana['b']

            # Calcular regressão usando médias
            regressao_media = self.calcular_regressao(x, medias)
            valores_previstos_media = regressao_media['a'] * \
                x + regressao_media['b']

            self.regressoes[canal] = {
                'medianas': medianas,
                'medias': medias,
                'regressao_mediana': regressao_mediana,
                'regressao_media': regressao_media,
                'valores_previstos_mediana': valores_previstos_mediana,
                'valores_previstos_media': valores_previstos_media
            }

    def calcular_gaussiana(self, x, sigma, mi, intensidade_max, intensidade_min):
        """Calcula a distribuição gaussiana"""
        return intensidade_min + (intensidade_max - intensidade_min) * np.exp(-((x - mi)**2) / (2 * sigma**2))

    def gerar_dados_canal(self, canal, sigma, mi):
        """Gera dados para um canal específico com linhas suaves"""
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

        # Gerar pontos com alta resolução para linhas suaves
        n_pontos = tempo['n_pontos']
        x_vals = np.linspace(-1, 1, n_pontos)
        horas_decimais = np.linspace(
            tempo['hora_inicio'], tempo['hora_fim'], n_pontos)

        # Calcular intensidades
        intensidades = self.calcular_gaussiana(
            x_vals, sigma, mi, intensidade_max, intensidade_min)

        # Suavizar as curvas usando interpolação
        if n_pontos < 50:  # Se poucos pontos, interpolar para suavizar
            x_interp = np.linspace(-1, 1, 200)
            f = interp1d(x_vals, intensidades, kind='cubic')
            intensidades = f(x_interp)
            horas_decimais = np.linspace(
                tempo['hora_inicio'], tempo['hora_fim'], 200)
            x_vals = x_interp

        # Calcular integral
        delta_t_segundos = (
            tempo['hora_fim'] - tempo['hora_inicio']) * 3600 / (len(x_vals) - 1)
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
                    '', '', f"{reg['regressao_mediana']['a']:.6f}" if i == 0 else '']
                bancada_data.append(row)

            bancada_data.append(
                ['', '', '', '', '', '', '', f"{reg['regressao_mediana']['b']:.6f}"])
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
st.title("🖥️ Sistema de Calibração de Bancadas")

with st.expander("⚠️ INSTRUÇÕES IMPORTANTES", expanded=False):
    st.info("""
    **IMPORTANTE:**

    1. **Ao trabalhar com duas bancadas:**
       - Quando for escolher o range de PPFD que o experimento trabalhará, é preciso escolher:
         - **O maior valor entre os dois mínimos** das bancadas de cada canal
         - **O menor valor entre os dois máximos** das bancadas de cada canal
    
    2. **Configuração de arquivos LAMP_CH_X.txt:**
       - Todos os canais (inclusive o quarto) devem iniciar e terminar no mesmo horário
       - Isso evita que o equipamento ligue e desligue sem ativação configurada de dois dos três canais
    
    3. **Atenção às proporções:**
       - A proporção escolhida é entre canais físicos de LEDs
       - **NÃO** é de banda espectral
    """)

st.markdown("---")

# Barra lateral
with st.sidebar:
    st.header("NAVEGAÇÃO")

    # Usar tabs para navegação
    aba_selecionada = st.radio(
        "Selecione a seção:",
        ["📊 Visão Geral",
         "🧪 Calibração Bancada",
         "🔄 Configurar Canais",
         "🔴 Canal Vermelho",
         "🔵 Canal Azul",
         "⚪ Canal Branco"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if aba_selecionada != "🧪 Calibração Bancada":
        st.header("⚙️ Configurações Rápidas")

        with st.expander("⏰ Horários", expanded=False):
            hora_inicio = st.number_input("Hora Início", 0, 23,
                                          st.session_state.parametros_temporais['hora_inicio'],
                                          key="hora_inicio_sidebar")
            hora_fim = st.number_input("Hora Fim", 0, 23,
                                       st.session_state.parametros_temporais['hora_fim'],
                                       key="hora_fim_sidebar")
            n_pontos = st.slider("Nº de Pontos", 10, 500,
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

        with st.expander("📐 Gaussianas", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                sigma_vermelho = st.slider("σ Vermelho", 0.1, 1.0,
                                           st.session_state.parametros_gaussianos['canal_vermelho']['sigma'],
                                           0.01, key="sigma_v_sidebar")
                sigma_azul = st.slider("σ Azul", 0.1, 1.0,
                                       st.session_state.parametros_gaussianos['canal_azul']['sigma'],
                                       0.01, key="sigma_a_sidebar")
                sigma_branco = st.slider("σ Branco", 0.1, 1.0,
                                         st.session_state.parametros_gaussianos['canal_branco']['sigma'],
                                         0.01, key="sigma_b_sidebar")

            with col2:
                mi_vermelho = st.slider("μ Vermelho", -1.0, 1.0,
                                        st.session_state.parametros_gaussianos['canal_vermelho']['mi'],
                                        0.05, key="mi_v_sidebar")
                mi_azul = st.slider("μ Azul", -1.0, 1.0,
                                    st.session_state.parametros_gaussianos['canal_azul']['mi'],
                                    0.05, key="mi_a_sidebar")
                mi_branco = st.slider("μ Branco", -1.0, 1.0,
                                      st.session_state.parametros_gaussianos['canal_branco']['mi'],
                                      0.05, key="mi_b_sidebar")

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
    st.header("📊 Visão Geral do Sistema")

    # Obter dados dos canais
    dados_vermelho = sistema.get_dados_canal('vermelho')
    dados_azul = sistema.get_dados_canal('azul')
    dados_branco = sistema.get_dados_canal('branco')

    # Métricas em tempo real
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🔴 DLI Vermelho",
            f"{dados_vermelho['DLI_final']:.2f} mol/m²",
            delta=f"ICE: {dados_vermelho['ICE']:.1f} μmol/m²/s"
        )

    with col2:
        st.metric(
            "🔵 DLI Azul",
            f"{dados_azul['DLI_final']:.2f} mol/m²",
            delta=f"ICE: {dados_azul['ICE']:.1f} μmol/m²/s"
        )

    with col3:
        st.metric(
            "⚪DLI Branco",
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

    # Regressões lineares da bancada - LADO A LADO
    st.header("📐 Regressões Lineares da Bancada")

    col1, col2, col3 = st.columns(3)

    for idx, (canal_nome, col, cor) in enumerate(zip(
        ['azul', 'vermelho', 'branco'],
        [col1, col2, col3],
        ['blue', 'red', 'gray']
    )):
        with col:
            reg = sistema.regressoes[canal_nome]

            # Gráfico de regressão
            x = st.session_state.dados_bancada[canal_nome]['valores_referencia']
            y_medido = reg['medianas']
            y_previsto = reg['valores_previstos_mediana']

            fig = go.Figure()

            # Pontos medidos
            fig.add_trace(go.Scatter(
                x=x, y=y_medido,
                mode='markers',
                name='Dados medidos',
                marker=dict(
                    size=8,
                    color=cor,
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

            fig.update_layout(
                title=f'Canal {canal_nome.capitalize()}',
                xaxis_title='Valor de Referência',
                yaxis_title='PPFD (μmol/m²/s)',
                hovermode='x unified',
                height=350,
                showlegend=True,
                margin=dict(l=50, r=50, t=50, b=50)
            )

            # Adicionar equação
            eq_text = f"y = {reg['regressao_mediana']['a']:.3f}x + {reg['regressao_mediana']['b']:.3f}<br>R² = {reg['regressao_mediana']['r2']:.4f}"
            fig.add_annotation(
                x=0.05, y=0.95,
                xref="paper", yref="paper",
                text=eq_text,
                showarrow=False,
                font=dict(size=10),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )

            st.plotly_chart(fig, use_container_width=True)

            # Estatísticas da regressão
            st.markdown("**Estatísticas da Regressão:**")
            stats_data = {
                'Parâmetro': ['a', 'b', 'R²', 'p-valor', 'Erro'],
                'Valor': [
                    f"{reg['regressao_mediana']['a']:.4f}",
                    f"{reg['regressao_mediana']['b']:.4f}",
                    f"{reg['regressao_mediana']['r2']:.4f}",
                    f"{reg['regressao_mediana']['p_value']:.4e}" if reg['regressao_mediana']['p_value'] > 0 else "0.0000",
                    f"{reg['regressao_mediana']['std_err']:.4f}"
                ]
            }

            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, hide_index=True, use_container_width=True)

            # Estatísticas do canal
            st.markdown("**Estatísticas do Canal:**")
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.metric("Máx", f"{max(reg['medianas']):.1f}")
                st.metric("Mín", f"{min(reg['medianas']):.1f}")
            with col_stat2:
                st.metric(
                    "Amplitude", f"{max(reg['medianas']) - min(reg['medianas']):.1f}")
                st.metric("Média", f"{np.mean(reg['medianas']):.1f}")

    st.markdown("---")

    # Gráficos Comparativos
    st.header("📈 Comparação entre Canais")

    # Gráfico 1: Intensidades comparadas com soma
    st.subheader("⚡ Intensidade dos Canais")

    fig1 = go.Figure()

    # Calcular soma das intensidades
    soma_intensidades = dados_vermelho['Intensidade'] + \
        dados_azul['Intensidade'] + dados_branco['Intensidade']

    # Suavizar linhas usando interpolação
    def suavizar_curva(x, y, n_points=500):
        if len(x) < n_points:
            f = interp1d(x, y, kind='cubic')
            x_new = np.linspace(min(x), max(x), n_points)
            y_new = f(x_new)
            return x_new, y_new
        return x, y

    horas_v, intens_v = suavizar_curva(
        dados_vermelho['hora_decimal'], dados_vermelho['Intensidade'])
    horas_a, intens_a = suavizar_curva(
        dados_azul['hora_decimal'], dados_azul['Intensidade'])
    horas_b, intens_b = suavizar_curva(
        dados_branco['hora_decimal'], dados_branco['Intensidade'])

    fig1.add_trace(go.Scatter(
        x=horas_v,
        y=intens_v,
        mode='lines',
        name='Vermelho',
        line=dict(color='red', width=2, shape='spline'),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    fig1.add_trace(go.Scatter(
        x=horas_a,
        y=intens_a,
        mode='lines',
        name='Azul',
        line=dict(color='blue', width=2, shape='spline'),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    fig1.add_trace(go.Scatter(
        x=horas_b,
        y=intens_b,
        mode='lines',
        name='Branco',
        line=dict(color='gray', width=2, shape='spline'),
        hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
    ))

    # Calcular e adicionar soma (dashed)
    horas_soma, soma_suave = suavizar_curva(
        dados_vermelho['hora_decimal'], soma_intensidades)
    fig1.add_trace(go.Scatter(
        x=horas_soma,
        y=soma_suave,
        mode='lines',
        name='Soma Total',
        line=dict(color='black', width=3, dash='dash', shape='spline'),
        hovertemplate='Hora: %{x:.2f}<br>Soma: %{y:.2f} μmol/m²/s'
    ))

    fig1.update_layout(
        xaxis_title='Hora do Dia',
        yaxis_title='Intensidade (μmol/m²/s)',
        hovermode='x unified',
        height=450,
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: DLIs finais comparados
    st.subheader("📊 DLIs Finais por Canal")

    dli_data = {
        'Canal': ['Vermelho', 'Azul', 'Branco', 'Total'],
        'DLI Final (mol/m²)': [
            dados_vermelho['DLI_final'],
            dados_azul['DLI_final'],
            dados_branco['DLI_final'],
            dados_vermelho['DLI_final'] +
            dados_azul['DLI_final'] + dados_branco['DLI_final']
        ],
        'ICE (μmol/m²/s)': [
            dados_vermelho['ICE'],
            dados_azul['ICE'],
            dados_branco['ICE'],
            dados_vermelho['ICE'] + dados_azul['ICE'] + dados_branco['ICE']
        ]
    }

    df_dli = pd.DataFrame(dli_data)

    col1, col2 = st.columns(2)

    with col1:
        fig2 = go.Figure(data=[
            go.Bar(
                x=df_dli['Canal'],
                y=df_dli['DLI Final (mol/m²)'],
                marker_color=['red', 'blue', 'gray', 'green'],
                text=df_dli['DLI Final (mol/m²)'].round(3),
                textposition='outside'
            )
        ])

        fig2.update_layout(
            title='DLI Final por Canal',
            yaxis_title='DLI Final (mol/m²)',
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = go.Figure(data=[
            go.Bar(
                x=df_dli['Canal'],
                y=df_dli['ICE (μmol/m²/s)'],
                marker_color=['red', 'blue', 'gray', 'green'],
                text=df_dli['ICE (μmol/m²/s)'].round(1),
                textposition='outside'
            )
        ])

        fig3.update_layout(
            title='ICE por Canal',
            yaxis_title='ICE (μmol/m²/s)',
            height=400
        )

        st.plotly_chart(fig3, use_container_width=True)

    # Tabelas dos canais lado a lado
    st.subheader("📋 Dados dos Canais")

    col_t1, col_t2, col_t3 = st.columns(3)

    # Função para criar tabela de dados do canal
    def criar_tabela_canal(dados, canal_nome, cor):
        df = pd.DataFrame({
            'Hora': dados['hora_decimal'],
            'Intensidade': dados['Intensidade'],
            'Integral': dados['Integral']
        })

        # Formatar números
        df['Hora'] = df['Hora'].apply(lambda x: f"{x:.2f}")
        df['Intensidade'] = df['Intensidade'].apply(lambda x: f"{x:.2f}")
        df['Integral'] = df['Integral'].apply(lambda x: f"{x:.6f}")

        return df

    with col_t1:
        st.markdown("**🔴 Canal Vermelho**")
        df_vermelho = criar_tabela_canal(dados_vermelho, 'vermelho', 'red')
        st.dataframe(df_vermelho, height=400, use_container_width=True)

    with col_t2:
        st.markdown("**🔵 Canal Azul**")
        df_azul = criar_tabela_canal(dados_azul, 'azul', 'blue')
        st.dataframe(df_azul, height=400, use_container_width=True)

    with col_t3:
        st.markdown("**⚪ Canal Branco**")
        df_branco = criar_tabela_canal(dados_branco, 'branco', 'gray')
        st.dataframe(df_branco, height=400, use_container_width=True)

    # Exportar dados para Excel
    st.markdown("---")
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

        # Container para o grid
        grid_container = st.container()

        with grid_container:
            # Cabeçalho
            cols = st.columns(6)
            with cols[0]:
                st.markdown("**Repetição**")
            for i in range(5):
                with cols[i+1]:
                    st.markdown(
                        f"**Intensidade {i+1}**<br>(Ref: {ref_vals[i]})", unsafe_allow_html=True)

            # Linhas de dados
            for rep in range(5):
                cols = st.columns(6)
                with cols[0]:
                    st.markdown(f"**Repetição {rep+1}**")

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

        reg = sistema.regressoes[canal_key]['regressao_media']
        medias = sistema.regressoes[canal_key]['medias']

        st.metric("Média Máxima", f"{max(medias):.2f}")
        st.metric("Média Mínima", f"{min(medias):.2f}")
        st.metric("Coef. Angular (a)", f"{reg['a']:.4f}")
        st.metric("Coef. Linear (b)", f"{reg['b']:.4f}")
        st.metric("R²", f"{reg['r2']:.4f}")

        # Botão para resetar dados
        if st.button("🔄 Restaurar Valores Padrão", key="reset_button"):
            # Definir valores padrão baseados no canal
            if canal_key == 'azul':
                default_data = np.array([
                    [24.86, 29.3, 27.6, 22.53, 29.51],
                    [76.45, 74.32, 73.75, 58.78, 66.12],
                    [114.8, 106.9, 114.6, 102.9, 100.9],
                    [135.5, 127.1, 138.0, 120.2, 119.8],
                    [175.7, 177.0, 164.1, 145.0, 170.0]
                ]).T
            elif canal_key == 'vermelho':
                default_data = np.array([
                    [58.12, 57.3, 54.3, 55.9, 52.0],
                    [143.9, 168.3, 160.4, 147.6, 158.1],
                    [235.3, 227.2, 198.0, 233.5, 224.5],
                    [279.5, 293.3, 272.2, 302.7, 281.7],
                    [360.5, 354.2, 407.3, 398.5, 367.8]
                ]).T
            else:  # branco
                default_data = np.array([
                    [20.61, 24.51, 24.24, 22.42, 23.14],
                    [62.13, 67.69, 58.93, 59.12, 55.09],
                    [69.18, 92.19, 91.02, 86.68, 84.73],
                    [109.8, 104.6, 117.0, 113.7, 110.3],
                    [120.8, 150.9, 143.3, 130.7, 143.9]
                ]).T

            # Atualizar dados
            st.session_state.dados_bancada[canal_key]['dados'] = default_data
            sistema.calcular_regressoes()
            st.success(
                f"Valores padrão restaurados para o canal {canal_selecionado}!")
            st.rerun()

    # Visualização gráfica em tempo real - MESMO GRÁFICO DA VISÃO GERAL
    st.subheader("📈 Visualização em Tempo Real")

    # Obter dados da regressão
    reg = sistema.regressoes[canal_key]
    x = st.session_state.dados_bancada[canal_key]['valores_referencia']
    y_medido = reg['medianas']
    y_previsto = reg['valores_previstos_mediana']

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

    # Plotar média
    medias = sistema.regressoes[canal_key]['medias']
    fig.add_trace(go.Scatter(
        x=ref_vals,
        y=medias,
        mode='lines+markers',
        name='Média',
        line=dict(color='black', width=3),
        marker=dict(size=12, color='black')
    ))

    # Plotar regressão (usando média)
    y_previsto = sistema.regressoes[canal_key]['valores_previstos_media']
    fig.add_trace(go.Scatter(
        x=ref_vals,
        y=y_previsto,
        mode='lines',
        name='Regressão (média)',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f'Regressão Linear - Canal {canal_selecionado}',
        xaxis_title='Valor de Referência',
        yaxis_title='PPFD Medido (μmol/m²/s)',
        hovermode='x unified',
        height=500
    )

    # Adicionar equação no gráfico
    eq_text = f"y = {reg['regressao_mediana']['a']:.3f}x + {reg['regressao_mediana']['b']:.3f}<br>R² = {reg['regressao_mediana']['r2']:.4f}"
    fig.add_annotation(
        x=0.05, y=0.95,
        xref="paper", yref="paper",
        text=eq_text,
        showarrow=False,
        font=dict(size=12),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1,
        borderpad=4
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela com equação e valores calculados
    st.subheader("📊 Equação de Regressão e Valores Calculados")

    # Obter dados da regressão
    reg = sistema.regressoes[canal_key]['regressao_media']
    medias = sistema.regressoes[canal_key]['medias']
    valores_previstos = sistema.regressoes[canal_key]['valores_previstos_media']
    ref_vals = dados_canal['valores_referencia']

    # Exibir equação
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("**Equação de Regressão:**")
        st.info(f"""
        **y = {reg['a']:.4f}x + {reg['b']:.4f}**
        
        Onde:
        - **y** = PPFD calculado (μmol/m²/s)
        - **x** = Valor de referência
        - **R²** = {reg['r2']:.4f}
        """)

    with col2:
        # Criar tabela com valores
        tabela_dados = []
        for i in range(5):
            erro_relativo = abs(
                (valores_previstos[i] - medias[i]) / medias[i] * 100) if medias[i] != 0 else 0
            tabela_dados.append({
                'Intensidade': i+1,
                'Ref. (x)': ref_vals[i],
                'Média Medida': f"{medias[i]:.2f}",
                'Valor Calculado': f"{valores_previstos[i]:.2f}",
                'Diferença': f"{valores_previstos[i] - medias[i]:.2f}",
                'Erro Relativo (%)': f"{erro_relativo:.2f}"
            })

        df_tabela = pd.DataFrame(tabela_dados)

        st.dataframe(
            df_tabela,
            use_container_width=True,
            hide_index=True
        )

        # Resumo estatístico
        st.markdown("**Resumo Estatístico:**")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Erro Médio Absoluto",
                      f"{np.mean(np.abs(valores_previstos - medias)):.2f} μmol/m²/s")
        with col_stat2:
            st.metric("Erro Quadrático Médio",
                      f"{np.mean((valores_previstos - medias)**2):.2f} (μmol/m²/s)²")
        with col_stat3:
            st.metric("Coef. Determinação (R²)",
                      f"{reg['r2']:.4f}")


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
        # Gráfico de intensidade (suavizado)
        horas_suave, intens_suave = st.session_state.get(
            'horas_suave', None), st.session_state.get('intens_suave', None)
        if len(dados['hora_decimal']) < 200:
            f = interp1d(dados['hora_decimal'],
                         dados['Intensidade'], kind='cubic')
            horas_suave = np.linspace(
                min(dados['hora_decimal']), max(dados['hora_decimal']), 500)
            intens_suave = f(horas_suave)
        else:
            horas_suave, intens_suave = dados['hora_decimal'], dados['Intensidade']

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=horas_suave,
            y=intens_suave,
            mode='lines',
            name='Intensidade',
            line=dict(color='red' if canal_nome == 'vermelho' else
                      'blue' if canal_nome == 'azul' else 'gray', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.1)' if canal_nome == 'vermelho' else
            'rgba(0,0,255,0.1)' if canal_nome == 'azul' else 'rgba(128,128,128,0.1)',
            hovertemplate='Hora: %{x:.2f}<br>Intensidade: %{y:.2f} μmol/m²/s'
        ))

        fig1.update_layout(
            title=f'Intensidade - Canal {nome_display}',
            xaxis_title='Hora do Dia',
            yaxis_title='Intensidade (μmol/m²/s)',
            height=400
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Gráfico da integral (suavizado)
        if len(dados['hora_decimal']) < 200:
            f = interp1d(dados['hora_decimal'],
                         dados['Integral'], kind='cubic')
            integral_suave = f(horas_suave)
        else:
            horas_suave, integral_suave = dados['hora_decimal'], dados['Integral']

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=horas_suave,
            y=integral_suave,
            mode='lines',
            name='Integral',
            line=dict(color='red' if canal_nome == 'vermelho' else
                      'blue' if canal_nome == 'azul' else 'gray', width=3, shape='spline'),
            hovertemplate='Hora: %{x:.2f}<br>Integral: %{y:.4f} mol/m²'
        ))

        fig2.update_layout(
            title=f'Integral Acumulada (DLI) - Canal {nome_display}',
            xaxis_title='Hora do Dia',
            yaxis_title='Integral (mol/m²)',
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)

    # Gráfico da distribuição gaussiana
    st.subheader(f"📊 Distribuição Gaussiana")

    # Suavizar a gaussiana
    if len(dados['x']) < 200:
        f = interp1d(dados['x'], dados['Intensidade'], kind='cubic')
        x_suave = np.linspace(min(dados['x']), max(dados['x']), 500)
        intens_suave = f(x_suave)
    else:
        x_suave, intens_suave = dados['x'], dados['Intensidade']

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=x_suave,
        y=intens_suave,
        mode='lines',
        name='Distribuição',
        line=dict(color='red' if canal_nome == 'vermelho' else
                  'blue' if canal_nome == 'azul' else 'gray', width=3, shape='spline'),
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

    # Área entre ±σ
    fig3.add_vrect(
        x0=sigma_neg, x1=sigma_pos,
        fillcolor="rgba(0, 100, 200, 0.1)",
        line_width=0,
        annotation_text="±σ (68%)",
        annotation_position="top left"
    )

    fig3.update_layout(
        title=f'Distribuição Gaussiana - {nome_display} (σ={params_gauss["sigma"]}, μ={params_gauss["mi"]})',
        xaxis_title='x (domínio normalizado)',
        yaxis_title='Intensidade (μmol/m²/s)',
        height=400
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
        title='Intensidades por Canal',
        barmode='group',
        yaxis_title='Intensidade (μmol/m²/s)',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


# Roteamento das abas
if aba_selecionada == "📊 Visão Geral":
    exibir_visao_geral()

elif aba_selecionada == "🧪 Calibração Bancada":
    exibir_calibracao_bancada()

elif aba_selecionada == "🔄 Configurar Canais":
    exibir_configurar_canais()

elif aba_selecionada == "🔴 Canal Vermelho":
    exibir_canal_detalhes('vermelho', '🔴', 'Vermelho')

elif aba_selecionada == "🔵 Canal Azul":
    exibir_canal_detalhes('azul', '🔵', 'Azul')

elif aba_selecionada == "⚪ Canal Branco":
    exibir_canal_detalhes('branco', '⚪', 'Branco')

# Rodapé
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9em;'>"
    "🖥️ Sistema de Calibração de Bancadas | Desenvolvido para LAAC | v1.0"
    "</div>",
    unsafe_allow_html=True
)
