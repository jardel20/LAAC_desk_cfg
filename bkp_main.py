import pandas as pd
import numpy as np
import streamlit as st
import zipfile
import io
from datetime import datetime
from scipy import stats
from scipy.interpolate import interp1d
from streamlit_echarts import st_echarts
from scripts.man import exibir_manual_completo

# Configurar página
# Configuração básica da página
st.set_page_config(
    page_title="LAAC - Sistema de Calibração",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cabeçalho personalizado com CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 0;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Conteúdo do cabeçalho
st.markdown("""
    <div class="main-header">
        <h1>🖥️ Calibração de Bancadas LAAC</h1>
        <p>Sistema integrado para calibração fotobiológica e geração de perfis de iluminação</p>
        <div style="margin-top: 1rem;">
            <span class="badge">Versão 1.0.0</span>
            <span class="badge">Spectral Int</span>
            <span class="badge">LAAC - UFV</span>
        </div>
    </div>
""", unsafe_allow_html=True)


class SistemaCalibracao:
    def __init__(self):
        self.inicializar_dados()

    def inicializar_dados(self):
        """Inicializa ou carrega os dados da sessão"""
        if 'dados_bancada' not in st.session_state:
            st.session_state.dados_bancada = {
                'azul': {
                    'dados': np.array([
                        [24.86, 29.3, 27.6, 22.53, 29.51],
                        [76.45, 74.32, 73.75, 58.78, 66.12],
                        [114.8, 106.9, 114.6, 102.9, 100.9],
                        [135.5, 127.1, 138.0, 120.2, 119.8],
                        [175.7, 177.0, 164.1, 145.0, 170.0]
                    ]).T,
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
                'n_pontos': 60
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
            medias = np.mean(dados['dados'], axis=0)
            x = dados['valores_referencia']

            regressao_mediana = self.calcular_regressao(x, medianas)
            valores_previstos_mediana = regressao_mediana['a'] * \
                x + regressao_mediana['b']

            regressao_media = self.calcular_regressao(x, medias)
            valores_previstos_media = regressao_media['a'] * \
                x + regressao_media['b']

            self.regressoes[canal] = {
                'medianas': medianas,
                'medias': medias,
                'regressao_mediana': regressao_mediana,
                'regressao_media': regressao_media,
                'valores_previstos_mediana': valores_previstos_mediana,
                'valores_previstos_media': valores_previstos_media,
                # Adicionando limites da calibração
                # Máximo medido na calibração
                'limite_max_calibracao': np.max(medias),
                # Mínimo medido na calibração
                'limite_min_calibracao': np.min(medias)
            }

    def calcular_gaussiana(self, x, sigma, mi, intensidade_max, intensidade_min):
        """Calcula a distribuição gaussiana"""
        return intensidade_min + (intensidade_max - intensidade_min) * np.exp(-((x - mi)**2) / (2 * sigma**2))

    def normalizar_para_ppfd(self, canal, valor_normalizado):
        """Converte valor normalizado (0-1) para PPFD usando regressão da calibração"""
        reg = self.regressoes[canal]['regressao_media']
        return reg['a'] * valor_normalizado + reg['b']

    def ppfd_para_normalizado(self, canal, ppfd):
        """Converte PPFD para valor normalizado (0-1) usando regressão inversa"""
        reg = self.regressoes[canal]['regressao_media']
        if reg['a'] != 0:
            return (ppfd - reg['b']) / reg['a']
        return 0

    def calcular_intensidade_canal(self, canal):
        """Calcula intensidade máxima e mínima para um canal considerando calibração"""
        params = st.session_state.parametros_canais

        # Calcular proporções normalizadas
        proporcoes = np.array([
            params['proporcao_azul'],
            params['proporcao_vermelho'],
            params['proporcao_branco']
        ])
        proporcoes_norm = proporcoes / proporcoes.sum()

        # Mapear canal para índice
        canal_idx = {'azul': 0, 'vermelho': 1, 'branco': 2}[canal]
        proporcao_canal = proporcoes_norm[canal_idx]

        # Distribuir intensidades totais pelas proporções
        intensidade_max_total = params['intensidade_max_total']
        intensidade_min_total = params['intensidade_min_total']

        intensidade_max_bruta = intensidade_max_total * proporcao_canal
        intensidade_min_bruta = intensidade_min_total * proporcao_canal

        # Obter limites da calibração para este canal
        limite_max_calibracao = self.regressoes[canal]['limite_max_calibracao']
        limite_min_calibracao = self.regressoes[canal]['limite_min_calibracao']

        # Limitar as intensidades brutas pelos limites da calibração
        # Se a intensidade calculada for maior que o máximo possível da calibração,
        # ajustar para o máximo possível
        if intensidade_max_bruta > limite_max_calibracao:
            intensidade_max_bruta = limite_max_calibracao

        # Se a intensidade calculada for menor que o mínimo possível da calibração,
        # ajustar para o mínimo possível
        if intensidade_min_bruta < limite_min_calibracao:
            intensidade_min_bruta = limite_min_calibracao

        # Ajustar mínimo para não ser maior que o máximo
        if intensidade_min_bruta > intensidade_max_bruta:
            intensidade_min_bruta = max(
                limite_min_calibracao, intensidade_max_bruta * 0.1)

        # Converter para valores normalizados usando a calibração
        valor_max_normalizado = self.ppfd_para_normalizado(
            canal, intensidade_max_bruta)
        valor_min_normalizado = self.ppfd_para_normalizado(
            canal, intensidade_min_bruta)

        # Limitar aos limites da calibração (0-1)
        valor_max_normalizado = max(0, min(1, valor_max_normalizado))
        valor_min_normalizado = max(0, min(1, valor_min_normalizado))

        # Converter de volta para PPFD usando a calibração
        intensidade_max_calibrada = self.normalizar_para_ppfd(
            canal, valor_max_normalizado)
        intensidade_min_calibrada = self.normalizar_para_ppfd(
            canal, valor_min_normalizado)

        # Garantir que os valores finais respeitem os limites da calibração
        intensidade_max_calibrada = min(
            intensidade_max_calibrada, limite_max_calibracao)
        intensidade_min_calibrada = max(
            intensidade_min_calibrada, limite_min_calibracao)

        # Garantir que mínimo não seja maior que máximo
        if intensidade_min_calibrada > intensidade_max_calibrada:
            intensidade_min_calibrada = intensidade_max_calibrada * 0.1

        return intensidade_max_calibrada, intensidade_min_calibrada, valor_max_normalizado, valor_min_normalizado

    def gerar_dados_canal(self, canal, sigma, mi):
        """Gera dados para um canal específico"""
        # Calcular intensidades usando calibração
        intensidade_max, intensidade_min, valor_max_norm, valor_min_norm = self.calcular_intensidade_canal(
            canal)

        tempo = st.session_state.parametros_temporais
        n_pontos = tempo['n_pontos']

        # Gerar gaussiana no domínio normalizado [-1, 1]
        x_vals = np.linspace(-1, 1, n_pontos)
        gaussiana_norm = self.calcular_gaussiana(x_vals, sigma, mi, 1.0, 0.0)

        # Normalizar gaussiana para [0, 1]
        gauss_min = gaussiana_norm.min()
        gauss_max = gaussiana_norm.max()
        if gauss_max > gauss_min:
            gaussiana_norm = (gaussiana_norm - gauss_min) / \
                (gauss_max - gauss_min)

        # Mapear para intervalo de operação [valor_min_norm, valor_max_norm]
        range_norm = valor_max_norm - valor_min_norm
        valores_norm = valor_min_norm + gaussiana_norm * range_norm

        # Converter para PPFD usando calibração
        intensidades = np.array(
            [self.normalizar_para_ppfd(canal, val) for val in valores_norm])

        # Garantir que as intensidades respeitem os limites da calibração
        limite_max_calibracao = self.regressoes[canal]['limite_max_calibracao']
        limite_min_calibracao = self.regressoes[canal]['limite_min_calibracao']
        intensidades = np.clip(
            intensidades, limite_min_calibracao, limite_max_calibracao)

        # Gerar horários
        horas_decimais = np.linspace(
            tempo['hora_inicio'], tempo['hora_fim'], n_pontos)

        if n_pontos < 50:
            x_interp = np.linspace(-1, 1, 200)
            f = interp1d(x_vals, intensidades, kind='cubic')
            intensidades = f(x_interp)
            horas_decimais = np.linspace(
                tempo['hora_inicio'], tempo['hora_fim'], 200)
            x_vals = x_interp

        # GARANTIR QUE OS DADOS SÃO ARRAYS NUMPY
        horas_decimais = np.array(horas_decimais)
        intensidades = np.array(intensidades)

        delta_t_segundos = (
            tempo['hora_fim'] - tempo['hora_inicio']) * 3600 / (len(x_vals) - 1)
        integral = np.cumsum(intensidades) * delta_t_segundos / 1_000_000

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
            'intensidade_min': intensidade_min,
            'limite_max_calibracao': limite_max_calibracao,
            'limite_min_calibracao': limite_min_calibracao
        }

    def get_dados_canal(self, canal):
        """Obtém dados de um canal específico"""
        params_gauss = st.session_state.parametros_gaussianos[f'canal_{canal}']
        return self.gerar_dados_canal(canal, params_gauss['sigma'], params_gauss['mi'])

    # Adicione este método dentro da classe SistemaCalibracao:

    def gerar_conteudo_lamp(self, dados, params_temp):
        """Gera o conteúdo formatado para arquivos LAMP"""
        conteudo_arquivo = ""

        # Se houver menos de 50 pontos, usar interpolação para mais pontos
        if len(dados['hora_decimal']) < 50:
            # Interpolar para ter pelo menos 10 pontos
            n_pontos_arquivo = 10
            horas_interp = np.linspace(
                params_temp['hora_inicio'], params_temp['hora_fim'], n_pontos_arquivo)
            f = interp1d(dados['hora_decimal'],
                         dados['Intensidade'], kind='linear')
            intensidades_interp = f(horas_interp)
        else:
            # Usar todos os pontos (limitado a 50 para não ficar muito grande)
            n_pontos_arquivo = min(50, len(dados['hora_decimal']))
            idx_selecionados = np.linspace(
                0, len(dados['hora_decimal'])-1, n_pontos_arquivo, dtype=int)
            horas_interp = dados['hora_decimal'][idx_selecionados]
            intensidades_interp = dados['Intensidade'][idx_selecionados]

        # Formatar cada linha
        for hora, intensidade in zip(horas_interp, intensidades_interp):
            # Converter hora decimal para horas, minutos, segundos
            hora_int = int(hora)
            minuto_int = int((hora - hora_int) * 60)
            segundo_int = int(((hora - hora_int) * 60 - minuto_int) * 60)

            # Arredondar intensidade para inteiro (como no exemplo)
            intensidade_int = int(round(intensidade))

            # Formatar linha (hora minuto segundo intensidade)
            linha = f"{hora_int:02d} {minuto_int:02d} {segundo_int:02d} {intensidade_int}\n"
            conteudo_arquivo += linha

        return conteudo_arquivo

    def gerar_conteudo_lamp_ice(self, dados, params_temp):
        """Gera o conteúdo simplificado para arquivos LAMP com apenas ICE inicial e final"""
        conteudo_arquivo = ""

        # Obter ICE do canal (já calculado no sistema)
        ice = dados['ICE']

        # Converter ICE para inteiro
        ice_int = int(round(ice))

        # Linha 1: Horário de início con ICE
        hora_inicio = params_temp['hora_inicio']
        linha_inicio = f"{hora_inicio:02d} 00 00 {ice_int}\n"

        # Linha 2: Horário de fim con ICE
        hora_fim = params_temp['hora_fim']
        linha_fim = f"{hora_fim:02d} 00 00 {ice_int}\n"

        conteudo_arquivo = linha_inicio + linha_fim
        return conteudo_arquivo

# ============================================================================
# CONFIGURAÇÕES ECHARTS
# ============================================================================


# Paleta de cores padrão do ECharts
COLORS = {
    'vermelho': '#ee6666',
    'azul': '#5470c6',
    'branco': "#b3b3b3",
    'soma': "#363636",
    'regressao': '#73c0de',
    'media': '#fc8452',
    'grid': '#e0e6f1',
    'text': '#2c3e50',
    'title': '#1a1a1a',
    'axis': '#7b7b7b',
    'referencia': '#91cc75'
}

# Configurações de tema padrão
BASE_OPTIONS = {
    "animation": True,
    "animationDuration": 600,
    "animationEasing": "cubicOut",
    "backgroundColor": "transparent",
    "textStyle": {
        "fontFamily": "'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
        "fontSize": 12,
        "color": COLORS['text']
    }
}


def apply_base_config(options):
    """Aplica configurações base a um gráfico"""
    if "title" in options:
        options["title"]["textStyle"] = {
            "fontSize": 16,
            "fontWeight": "bold",
            "color": COLORS['title'],
            "padding": [0, 0, 10, 0]
        }
        options["title"]["left"] = "center"

    if "legend" in options:
        options["legend"]["textStyle"] = {
            "fontSize": 12,
            "color": COLORS['text']
        }
        options["legend"]["top"] = "top"
        options["legend"]["itemGap"] = 10

    if "xAxis" in options and isinstance(options["xAxis"], dict):
        options["xAxis"]["axisLine"] = {
            "lineStyle": {
                "color": COLORS['axis'],
                "width": 1
            }
        }
        options["xAxis"]["axisLabel"] = {
            "color": COLORS['axis'],
            "fontSize": 11
        }
        options["xAxis"]["nameTextStyle"] = {
            "color": COLORS['axis'],
            "fontSize": 12,
            "padding": [0, 0, 10, 0]
        }

    if "yAxis" in options and isinstance(options["yAxis"], dict):
        options["yAxis"]["axisLine"] = {
            "lineStyle": {
                "color": COLORS['axis'],
                "width": 1
            }
        }
        options["yAxis"]["axisLabel"] = {
            "color": COLORS['axis'],
            "fontSize": 11
        }
        options["yAxis"]["nameTextStyle"] = {
            "color": COLORS['axis'],
            "fontSize": 12,
            "padding": [0, 10, 0, 0]
        }

    if "grid" not in options:
        options["grid"] = {
            "left": "60px",
            "right": "40px",
            "bottom": "60px",
            "top": "60px",
            "containLabel": True
        }

    # CToolbox con saveAsImage funcionando
    options["toolbox"] = {
        "feature": {
            "dataView": {
                "show": True,
                "title": "Ver dados",
                "readOnly": True,
                "lang": ["Visualização", "Fechar", "Atualizar"]
            },
            "restore": {
                "show": True,
                "title": "Restaurar"
            },
        },
        "right": 10,
        "top": 10,
        "orient": "vertical",
        "itemSize": 18,
        "itemGap": 8,
        "showTitle": True
    }

    # ANIMAÇÕES

    # Habilita/desabilita animações globalmente
    if "animation" not in options:
        options["animation"] = True

    # Duração total da animação em milissegundos
    if "animationDuration" not in options:
        options["animationDuration"] = 800

    # Função de easing (aceleração/desaceleração) da animação
    # Define a "curva de movimento" da animação
    if "animationEasing" not in options:
        # cubicInOut: começa devagar, acelera no meio, termina devagar
        options["animationEasing"] = "cubicInOut"

    # Limiar para ativar animações (em milissegundos)
    # Si a mudança de dados for mais rápida que este valor, a animação é pulada
    # Isso previne animações muito rápidas que podem ser irritantes
    if "animationThreshold" not in options:
        # Se a mudança levar menos de 800ms, sem animação
        options["animationThreshold"] = 800

    # Duração da animação para ATUALIZAÇÕES (não criação inicial)
    # Útil quando os dados são atualizados dinamicamente
    if "animationDurationUpdate" not in options:
        # Para atualizações, usamos uma duração um pouco menor
        options["animationDurationUpdate"] = 600

    # Define se deve usar o tempo UTC (Tempo Universal Coordenado)
    # True = UTC, False = fuso horário local
    # Importante para gráficos temporais que precisam ser consistentes em diferentes fusos
    # Garante que todos os horários são tratados em UTC
    options["useUTC"] = True

    # Aplica configurações individuais para cada série (linha/barra/ponto) no gráfico
    # Isso permite customização específica por tipo de dados
    if "series" in options:
        for series in options["series"]:

            # Habilita animação específica para esta série
            # Mesmo que a animação global esteja ativa, uma série pode ter animação desabilitada
            if "animation" not in series:
                # Cada série terá sua própria animação
                series["animation"] = True

            # Duração da animação para esta série específica
            # Pode ser diferente da duração global
            if "animationDuration" not in series:
                series["animationDuration"] = 800  # 800ms por série

            # Função de easing específica para esta série
            # Útil para criar efeitos em cascata ou diferentes comportamentos
            if "animationEasing" not in series:
                series["animationEasing"] = "cubicInOut"  # Padrão consistente

    return {**BASE_OPTIONS, **options}


def criar_grafico_regressao(canal_nome, reg, x_ref, y_medido, y_previsto, cor):
    """Cria gráfico de regressão linear"""

    # Preparar dados CORRETAMENTE para ECharts
    dados_medidos = [
        {"value": [float(x_ref[i]), float(y_medido[i])]} for i in range(len(x_ref))]
    dados_regressao = [
        {"value": [float(x_ref[i]), float(y_previsto[i])]} for i in range(len(x_ref))]

    a = reg['regressao_mediana']['a']
    b = reg['regressao_mediana']['b']
    r2 = reg['regressao_mediana']['r2']

    options = {
        "title": {
            "text": f"Canal {canal_nome.capitalize()}",
            "subtext": f"y = {a:.3f}x + {b:.3f} | R² = {r2:.4f}",
            "subtextStyle": {"color": "#666", "fontSize": 12},
            "left": "center",
            "padding": [0, 0, 0, 0]
        },
        "tooltip": {},
        "legend": {
            "data": ["Dados Medidos", "Regressão"],
            "top": 45
        },
        "xAxis": {
            "name": "Valor de Referência (x)",
            "nameLocation": "middle",
            "nameGap": 25,
            "type": "value",
            "min": -0.1,
            "max": 1.1,
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "yAxis": {
            "name": "PPFD (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 35,
            "type": "value"
        },
        "series": [
            {
                "name": "Dados Medidos",
                "type": "scatter",
                "data": dados_medidos,
                "symbolSize": 10,
                "itemStyle": {
                    "color": cor,
                    "borderColor": "#fff",
                    "borderWidth": 2
                }
            },
            {
                "name": "Regressão",
                "type": "line",
                "data": dados_regressao,
                "lineStyle": {"color": cor, "width": 4, "type": "dashed"},
                "smooth": True,
                "showSymbol": False
            }
        ],
        "dataZoom": [{"type": "inside", "xAxisIndex": 0}],
        "grid": {
            "left": "8%",      # Margem esquerda
            "right": "8%",     # Margem direita
            "bottom": "8%",   # Margem inferior
            "top": "20%",      # Margem superior
            "containLabel": True
        }
    }
    return options

    return apply_base_config(options)


def criar_grafico_comparacao_intensidades(dados_vermelho, dados_azul, dados_branco):
    """Cria gráfico comparativo das intensidades dos canais"""

    # Preparar dados suavizados (código existente permanece igual)
    def preparar_dados_suavizados(dados):
        horas = np.array(dados['hora_decimal'])
        intens = np.array(dados['Intensidade'])
        if len(horas) < 100:
            f = interp1d(horas, intens, kind='cubic',
                         bounds_error=False, fill_value='extrapolate')
            horas_new = np.linspace(min(horas), max(horas), 200)
            intens_new = f(horas_new)
            return horas_new, intens_new
        return horas, intens

    horas_v, intens_v = preparar_dados_suavizados(dados_vermelho)
    horas_a, intens_a = preparar_dados_suavizados(dados_azul)
    horas_b, intens_b = preparar_dados_suavizados(dados_branco)

    # Calcular soma con horas comuns
    horas_min = max(min(horas_v), min(horas_a), min(horas_b))
    horas_max = min(max(horas_v), max(horas_a), max(horas_b))
    horas_comuns = np.linspace(horas_min, horas_max, 200)

    # Interpolar para soma
    intens_v_interp = np.interp(horas_comuns, horas_v, intens_v)
    intens_a_interp = np.interp(horas_comuns, horas_a, intens_a)
    intens_b_interp = np.interp(horas_comuns, horas_b, intens_b)
    soma_intensidades = intens_v_interp + intens_a_interp + intens_b_interp

    # DADOS PREPARADOS FORA do options (CRÍTICO)
    dados_vermelho_list = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['vermelho']}}
                           for h, i in zip(horas_v, intens_v)]
    dados_azul_list = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['azul']}}
                       for h, i in zip(horas_a, intens_a)]
    dados_branco_list = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['branco']}}
                         for h, i in zip(horas_b, intens_b)]
    dados_soma_list = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['soma']}}
                       for h, i in zip(horas_comuns, soma_intensidades)]

    options = {
        "color": [COLORS['vermelho'], COLORS['azul'], COLORS['branco'], COLORS['soma']],
        "title": {
            "text": "Comparação de Intensidades por Canal",
            "subtext": "Curvas suavizadas con interpolação cúbica",
            "left": "center",
            "padding": [0, 0, 0, 0]
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "borderColor": "#ccc",
            "borderWidth": 1,
            "textStyle": {
                "color": "#333"
            }
        },
        "legend": {
            "data": ["Vermelho", "Azul", "Branco", "Soma Total"],
            "top": "bottom",
            "left": "center",
            "type": "scroll",
            "padding": [50, 0, 0, 0],
            "itemGap": 5,
            "itemWidth": 25,
            "itemHeight": 14
        },
        "xAxis": {
            "name": "Hora do Dia",
            "nameLocation": "middle",
            "nameGap": 25,
            "nameTextStyle": {"fontSize": 14, "fontWeight": "bold"},
            "type": "value",
            "min": horas_min,
            "max": horas_max,
            "axisLine": {"show": True, "lineStyle": {"color": "#333", "width": 1.5}},
            "axisLabel": {
                "show": True,
                "formatter": """function(value) {
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    return hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0');
                }""",
                "fontSize": 11
            },
            "splitLine": {
                "show": True,
                "lineStyle": {"type": "dashed", "color": COLORS['grid']}
            }
        },
        "yAxis": {
            "name": "Intensidade (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 45,
            "nameTextStyle": {"fontSize": 14, "fontWeight": "bold"},
            "type": "value",
            "axisLine": {"show": True, "lineStyle": {"color": "#333", "width": 1.5}}
        },
        "series": [
            {
                "name": "Vermelho",
                "type": "line",
                "data": dados_vermelho_list,
                "smooth": 0.5,  # Suavização da linha
                "lineStyle": {
                    "color": COLORS['vermelho'],
                    "width": 2.5,
                    "shadowBlur": 0,
                    "shadowColor": COLORS['vermelho'] + "40"
                },
                "showSymbol": False,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": COLORS['vermelho'] + "40"},
                            {"offset": 1, "color": COLORS['vermelho'] + "05"}
                        ]
                    }
                },
                "emphasis": {
                    "focus": "series",
                    "lineStyle": {
                        "width": 3.5,
                        "shadowBlur": 0,
                        "shadowColor": COLORS['vermelho'] + "60"
                    }
                },
                "animation": True,
                "animationDuration": 1000,
                "animationEasing": "cubicInOut",
                "animationDelay": 200  # Delay para animação em cascata
            },
            {
                "name": "Azul",
                "type": "line",
                "data": dados_azul_list,
                "smooth": 0.5,
                "lineStyle": {
                    "color": COLORS['azul'],
                    "width": 2.5,
                    "shadowBlur": 0,
                    "shadowColor": COLORS['azul'] + "40"
                },
                "showSymbol": False,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": COLORS['azul'] + "40"},
                            {"offset": 1, "color": COLORS['azul'] + "05"}
                        ]
                    }
                },
                "emphasis": {"focus": "series"},
                "animation": True,
                "animationDuration": 1000,
                "animationEasing": "cubicInOut",
                "animationDelay": 200  # Delay para animação em cascata
            },
            {
                "name": "Branco",
                "type": "line",
                "data": dados_branco_list,
                "smooth": 0.5,
                "lineStyle": {
                    "color": COLORS['branco'],
                    "width": 2.5,
                    "shadowBlur": 0,
                    "shadowColor": COLORS['branco'] + "40"
                },
                "showSymbol": False,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": COLORS['branco'] + "40"},
                            {"offset": 1, "color": COLORS['branco'] + "05"}
                        ]
                    }
                },
                "emphasis": {"focus": "series"},
                "animation": True,
                "animationDuration": 1000,
                "animationEasing": "cubicInOut",
                "animationDelay": 200  # Delay para animação em cascata
            },
            {
                "name": "Soma Total",
                "type": "line",
                "data": dados_soma_list,
                "smooth": 0.5,
                "lineStyle": {
                    "color": COLORS['soma'],
                    "width": 3.5,
                    "type": "dashed",
                    "shadowBlur": 0,
                    "shadowColor": COLORS['soma'] + "60"
                },
                "showSymbol": False,
                "emphasis": {"focus": "series"},
                "animation": True,
                "animationDuration": 1000,
                "animationEasing": "cubicInOut",
                "animationDelay": 200  # Delay para animação em cascata
            }
        ],
        "dataZoom": [
            {"type": "inside", "xAxisIndex": 0},
            {
                "show": True,
                "xAxisIndex": 0,
                "type": "slider",
                "bottom": 10,
                "height": 20,
                "borderColor": "transparent",
                "handleStyle": {"color": COLORS['vermelho']},
                "fillerColor": "rgba(84, 112, 198, 0.1)",
                "textStyle": {"color": "#666"}
            }
        ],
        "grid": {
            "left": "3%",
            "right": "0%",
            "bottom": "12%",
            "top": "15%",
            "containLabel": True
        },
        # Configurações de animação globais
        "animation": True,
        "animationDuration": 1200,
        "animationDurationUpdate": 400,
        "animationEasing": "cubicInOut",
        "animationEasingUpdate": "cubicInOut",
        "stateAnimation": {
            "duration": 600,
            "delay": 0,
            "easing": "cubicInOut"
        }
    }

    return apply_base_config(options)


def criar_grafico_barras_dli(dli_data):
    """Cria gráfico de barras para DLI"""
    data = [
        {
            "value": round(float(dli_data['DLI Final (mol/m²)'][0]), 2),
            "itemStyle": {"color": COLORS['vermelho']}
        },
        {
            "value": round(float(dli_data['DLI Final (mol/m²)'][1]), 2),
            "itemStyle": {"color": COLORS['azul']}
        },
        {
            "value": round(float(dli_data['DLI Final (mol/m²)'][2]), 2),
            "itemStyle": {"color": COLORS['branco']}
        },
        {
            "value": round(float(dli_data['DLI Final (mol/m²)'][3]), 2),
            "itemStyle": {"color": COLORS['soma']}
        }
    ]

    options = {
        "title": {
            "text": "Daily Light Integral (DLI) por Canal",
            "subtext": "Valores acumulados ao final do fotoperíodo"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            },
            "formatter": "{b}: {c} mol/m²"
        },
        "grid": {
            "left": "50px",
            "right": "50px",
            "bottom": "50px",
            "top": "50px",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": dli_data['Canal'],
            "axisTick": {
                "alignWithLabel": True
            },
            "axisLabel": {
                "interval": 0,
                "rotate": 0
            }
        },
        "yAxis": {
            "type": "value",
            "name": "DLI (mol/m²)",
            "nameLocation": "middle",     # ✅ NOME NO MEIO
            "nameGap": 40,                # ✅ DISTÂNCIA do eixo
            "nameTextStyle": {            # ✅ ESTILO do nome
                "fontSize": 14,
                "fontWeight": "bold"
            },
            "axisLabel": {
                "formatter": "{value}"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#E0E6ED"  # ✅ COR FIXA
                }
            }
        },
        "series": [
            {
                "name": "DLI Final",
                "type": "bar",
                "data": data,
                "barWidth": "60%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                    "borderColor": "#fff",
                    "borderWidth": 1
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": COLORS['text']
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)"
                    }
                }
            }
        ]
    }

    return apply_base_config(options)


def criar_grafico_barras_ice(ice_data):
    """Cria gráfico de barras para ICE"""
    data = [
        {
            "value": round(float(ice_data['ICE (μmol/m²/s)'][0]), 2),
            "itemStyle": {"color": COLORS['vermelho']}
        },
        {
            "value": round(float(ice_data['ICE (μmol/m²/s)'][1]), 2),
            "itemStyle": {"color": COLORS['azul']}
        },
        {
            "value": round(float(ice_data['ICE (μmol/m²/s)'][2]), 2),
            "itemStyle": {"color": COLORS['branco']}
        },
        {
            "value": round(float(ice_data['ICE (μmol/m²/s)'][3]), 2),
            "itemStyle": {"color": COLORS['soma']}
        }
    ]

    options = {
        "title": {
            "text": "Irradiação Contínua Equivalente (ICE)",
            "subtext": "Média fotoperiódica de intensidade"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            },
            "formatter": "{b}: {c} μmol/m²/s"
        },
        "grid": {
            "left": "50px",
            "right": "50px",
            "bottom": "50px",
            "top": "50px",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": ice_data['Canal'],
            "axisTick": {
                "alignWithLabel": True
            }
        },
        "yAxis": {
            "type": "value",
            "name": "DLI (mol/m²)",
            "nameLocation": "middle",     # ✅ NOME NO MEIO
            "nameGap": 40,                # ✅ DISTÂNCIA do eixo
            "nameTextStyle": {            # ✅ ESTILO do nome
                "fontSize": 14,
                "fontWeight": "bold"
            },
            "axisLabel": {
                "formatter": "{value}"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#E0E6ED"  # ✅ COR FIXA
                }
            }
        },
        "series": [
            {
                "name": "ICE",
                "type": "bar",
                "data": data,
                "barWidth": "60%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                    "borderColor": "#fff",
                    "borderWidth": 1
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": COLORS['text']
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)"
                    }
                }
            }
        ]
    }

    return apply_base_config(options)


def criar_grafico_canal_detalhes(dados, canal_nome, cor, params_gauss):
    """Crea gráfico detalhado de um canal"""
    # Suavizar dados
    if len(dados['hora_decimal']) < 200:
        f = interp1d(dados['hora_decimal'], dados['Intensidade'], kind='cubic')
        horas_suave = np.linspace(
            min(dados['hora_decimal']), max(dados['hora_decimal']), 200)
        intens_suave = f(horas_suave)
    else:
        horas_suave = dados['hora_decimal']
        intens_suave = dados['Intensidade']

    hora_min = min(horas_suave)
    hora_max = max(horas_suave)

    # Adicionar informações de limites da calibração ao subtítulo
    subtexto = f"σ={params_gauss['sigma']:.2f}, μ={params_gauss['mi']:.2f} | "
    subtexto += f"Máx: {dados['intensidade_max']:.1f} (Limite: {dados.get('limite_max_calibracao', 'N/A'):.1f}), "
    subtexto += f"Mín: {dados['intensidade_min']:.1f} (Limite: {dados.get('limite_min_calibracao', 'N/A'):.1f}) μmol/m²/s"

    options = {
        "title": {
            "text": f"Intensidade - Canal {canal_nome.capitalize()}",
            "subtext": subtexto
        },
        "grid": {
            "left": "60px",
            "right": "95px",
            "bottom": "60px",
            "top": "60px",
            "containLabel": True
        },
        "tooltip": {},
        "xAxis": {
            "name": "Hora do Dia",
            "nameLocation": "middle",
            "nameGap": 25,
            "type": "value",
            "min": hora_min,
            "max": hora_max,
            "axisLabel": {
                "formatter": """function(value) {
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    return hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0');
                }"""
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": COLORS['grid']
                }
            },
            "splitNumber": 12
        },
        "yAxis": {
            "name": "Intensidade (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "axisLabel": {
                "formatter": "{value}"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": COLORS['grid']
                }
            }
        },
        "series": [
            {
                "name": "Intensidade",
                "type": "line",
                "data": [[float(horas_suave[i]), float(intens_suave[i])] for i in range(len(horas_suave))],
                "smooth": 0.5,
                "lineStyle": {
                    "color": cor,
                    "width": 3
                },
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [{
                            "offset": 0,
                            "color": cor + "80"
                        }, {
                            "offset": 1,
                            "color": cor + "10"
                        }]
                    }
                },
                "showSymbol": False,
                "emphasis": {
                    "focus": "self",
                    "shadowBlur": 10
                },
                "markLine": {
                    "silent": True,
                    "data": [
                        {
                            "yAxis": round(dados['intensidade_max'], 2),
                            "name": "Máximo Atual",
                            "lineStyle": {
                                "color": cor,
                                "type": "dashed",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Máx. Atual: {c}",
                                "position": "middle"
                            }
                        },
                        {
                            "yAxis": round(dados['intensidade_min'], 2),
                            "name": "Mínimo Atual",
                            "lineStyle": {
                                "color": cor,
                                "type": "dashed",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Mín. Atual: {c}",
                                "position": "middle"
                            }
                        },
                        {
                            "yAxis": round(dados.get('limite_max_calibracao', dados['intensidade_max']), 2),
                            "name": "Limite Máx Calibração",
                            "lineStyle": {
                                "color": "#ff0000",
                                "type": "dotted",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Lim. Máx: {c}",
                                "position": "end"
                            }
                        },
                        {
                            "yAxis": round(dados.get('limite_min_calibracao', dados['intensidade_min']), 2),
                            "name": "Limite Mín Calibração",
                            "lineStyle": {
                                "color": "#00aa00",
                                "type": "dotted",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Lim. Mín: {c}",
                                "position": "end"
                            }
                        }
                    ]
                }
            }
        ],
        "dataZoom": [
            {
                "type": "inside",
                "xAxisIndex": 0,
                "start": 0,
                "end": 100
            }
        ]
    }

    return apply_base_config(options)


def criar_grafico_integral(dados, canal_nome, cor):
    """Cria gráfico da integral acumulada"""
    if len(dados['hora_decimal']) < 200:
        f = interp1d(dados['hora_decimal'], dados['Integral'], kind='cubic')
        horas_suave = np.linspace(
            min(dados['hora_decimal']), max(dados['hora_decimal']), 200)
        integral_suave = f(horas_suave)
    else:
        horas_suave = dados['hora_decimal']
        integral_suave = dados['Integral']

    hora_min = min(horas_suave)
    hora_max = max(horas_suave)

    options = {
        "title": {
            "text": f"Integral Acumulada (DLI) - Canal {canal_nome.capitalize()}",
            "subtext": f"DLI final: {dados['DLI_final']:.2f} mol/m² | ICE: {dados['ICE']:.2f} μmol/m²/s"
        },
        "tooltip": {},
        "xAxis": {
            "name": "Hora do Dia",
            "nameLocation": "middle",
            "nameGap": 25,
            "min": hora_min,
            "max": hora_max,
            "type": "value",
            "axisLabel": {
                "formatter": """function(value) {
                    const hours = Math.floor(value);
                    const minutes = Math.round((value - hours) * 60);
                    return hours.toString().padStart(2, '0') + ':' + minutes.toString().padStart(2, '0');
                }"""
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": COLORS['grid']
                }
            }
        },
        "yAxis": {
            "name": "Integral (mol/m²)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "axisLabel": {
                "formatter": """function(value) {
                    return value.toFixed(4);
                }"""
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": COLORS['grid']
                }
            }
        },
        "series": [
            {
                "name": "Integral Acumulada",
                "type": "line",
                "data": [[float(horas_suave[i]), float(integral_suave[i])] for i in range(len(horas_suave))],
                "smooth": True,
                "lineStyle": {
                    "color": cor,
                    "width": 3
                },
                "showSymbol": False,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [{
                            "offset": 0,
                            "color": cor + "40"
                        }, {
                            "offset": 1,
                            "color": cor + "05"
                        }]
                    }
                },
                "emphasis": {
                    "focus": "series"
                }
            }
        ]
    }

    return apply_base_config(options)


def criar_grafico_gaussiana(dados, canal_nome, cor, sigma, mi):
    """Cria gráfico da distribuição gaussiana"""
    # Suavizar a gaussiana
    if len(dados['x']) < 200:
        f = interp1d(dados['x'], dados['Intensidade'], kind='cubic')
        x_suave = np.linspace(min(dados['x']), max(dados['x']), 200)
        intens_suave = f(x_suave)
    else:
        x_suave = dados['x']
        intens_suave = dados['Intensidade']

    # Calcular altura EXATA da curva na média μ
    y_mu = np.interp(mi, x_suave, intens_suave)
    y_max = max(intens_suave)

    # Preparar área entre ±σ (mantida)
    sigma_pos = mi + sigma
    sigma_neg = mi - sigma
    idx_area = np.where((x_suave >= sigma_neg) & (x_suave <= sigma_pos))[0]
    area_x = x_suave[idx_area]
    area_y = intens_suave[idx_area]

    options = {
        "title": {
            "text": f"Distribuição Gaussiana - Canal {canal_nome.capitalize()}",
            "subtext": f"σ = {sigma:.2f}, μ = {mi:.2f}"
        },
        "tooltip": {},
        "legend": {"show": False},
        "xAxis": {
            "name": "x (domínio normalizado)",
            "nameLocation": "middle",
            "nameGap": 25,
            "type": "value",
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": COLORS['grid']}}
        },
        "yAxis": {
            "name": "Intensidade (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "axisLabel": {"formatter": "{value}"}
        },
        "series": [
            {
                "name": "Distribuição Gaussiana",
                "type": "line",
                "data": [[float(round(x, 2)), float(round(y, 2))] for x, y in zip(x_suave, intens_suave)],
                "smooth": True,
                "lineStyle": {"color": cor, "width": 3},
                "showSymbol": False,
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": cor + "30"}, {"offset": 1, "color": cor + "05"}]
                    }
                },
                "markLine": {
                    "data": [
                        {
                            "name": "μ",
                            "xAxis": mi,
                            "lineStyle": {
                                "color": "#2c3e50",
                                "type": "dashed",
                                "width": 2
                            }
                        }
                    ]
                }
            },
            {
                "name": f"Área ±σ ({sigma*100}%)",
                "type": "line",
                "data": [[float(round(x, 2)), float(round(y, 2))] for x, y in zip(area_x, area_y)],
                "smooth": True,
                "lineStyle": {"color": "#73c0de", "width": 0},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "#73c0de40"}, {"offset": 1, "color": "#73c0de10"}]
                    }
                },
                "showSymbol": True,
                "symbol": "circle",
                "symbolSize": 4
            }
        ]
    }

    return apply_base_config(options)


def criar_grafico_comparacao_intensidades_barras(intensidades_max, intensidades_min):
    """Cria gráfico de barras comparativo"""
    options = {
        "title": {
            "text": "Comparação de Intensidades por Canal",
            "subtext": "Valores máximos e mínimos calculados",
            "left": "left",
            "padding": [0, 0, 0, 0]
        },
        "tooltip": {},
        "legend": {"show": False},
        "grid": {
            "left": "50px",
            "right": "50px",
            "bottom": "50px",
            "top": 50,
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": ["Azul", "Vermelho", "Branco"],
            "axisTick": {
                "show": False
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Intensidade (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 45,
            "nameTextStyle": {
                "fontSize": 14,
                "fontWeight": "bold",
                "color": "#333"
            },
            "axisLabel": {
                "formatter": "{value}"
            },
            "axisLine": {
                "show": True,
                "lineStyle": {"color": "#333", "width": 1.5}
            },
            "splitLine": {
                "show": True,
                "lineStyle": {"type": "dashed", "color": "#E0E6ED"}
            }
        },
        "series": [
            {
                "name": "Intensidade Máxima",
                "type": "bar",
                "data": [
                    {"value": float(round(intensidades_max[0], 2)), "itemStyle": {
                        "color": COLORS['azul']}},
                    {"value": float(round(intensidades_max[1], 2)), "itemStyle": {
                        "color": COLORS['vermelho']}},
                    {"value": float(round(intensidades_max[2], 2)), "itemStyle": {
                        "color": COLORS['branco']}}
                ],
                "barWidth": "40%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                    "borderColor": "#fff",
                    "borderWidth": 1
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": COLORS['text']
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)"
                    }
                }
            },
            {
                "name": "Intensidade Mínima",
                "type": "bar",
                "data": [
                    {"value": float(round(intensidades_min[0], 2)), "itemStyle": {
                        "color": COLORS['azul'] + "80"}},
                    {"value": float(round(intensidades_min[1], 2)), "itemStyle": {
                        "color": COLORS['vermelho'] + "80"}},
                    {"value": float(round(intensidades_min[2], 2)), "itemStyle": {
                        "color": COLORS['branco'] + "80"}}
                ],
                "barWidth": "40%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                    "borderColor": "#fff",
                    "borderWidth": 1
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "fontSize": 11,
                    "color": COLORS['text']
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)"
                    }
                }
            }
        ]
    }

    return apply_base_config(options)

# ============================================================================
# INICIALIZAÇÃO DO SISTEMA E INTERFACE
# ============================================================================


# Inicializar sistema
sistema = SistemaCalibracao()

with st.sidebar:
    st.header("📜 Navegação")

    # Navegação principal
    aba_selecionada = st.radio(
        "Selecione a seção:",
        ["📊 Visão Geral",
         "🧪 Calibração Bancada",
         "🎛️ Configurar Canais",
         "༗ Espectros"],
        label_visibility="collapsed"
    )

    if aba_selecionada != "🧪 Calibração Bancada":
        st.header("⚙️ Configurações")

        with st.expander("⏰ Horário", expanded=False):
            # Colunas para hora início e fim lado a lado
            col_hora1, col_hora2 = st.columns(2)

            with col_hora1:
                hora_inicio = st.number_input("Início", 0, 23,
                                              st.session_state.parametros_temporais['hora_inicio'],
                                              key="hora_inicio_sidebar")

            with col_hora2:
                hora_fim = st.number_input("Fim", 0, 23,
                                           st.session_state.parametros_temporais['hora_fim'],
                                           key="hora_fim_sidebar")

            # Nº de pontos embaixo, ocupando largura total
            n_pontos = st.slider("Nº de Pontos", 10, 60,
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

                # Incrementar contador para forçar animação
                if 'animacao_counter' in st.session_state:
                    st.session_state.animacao_counter += 1

                st.rerun()

        # Seção para gerar arquivos LAMP

        with st.expander("📄 Gerar Arquivos", expanded=False):
            # Selecionar qual arquivo gerar
            arquivo_selecionado = st.selectbox(
                "Selecione o arquivo:",
                ["LAMP_CH1.txt",
                 "LAMP_CH2.txt",
                 "LAMP_CH3.txt",
                 "LAMP_CH4.txt"],
                key="arquivo_lamp"
            )

            # Mapear seleção para canal
            canal_map = {
                "LAMP_CH1.txt": "vermelho",
                "LAMP_CH2.txt": "azul",
                "LAMP_CH3.txt": "branco",
                # Usa dados do branco
                "LAMP_CH4.txt": "branco"
            }

            canal_nome = canal_map[arquivo_selecionado]

            # Colunas para os botões
            col1, col2, col3 = st.columns(3)

            with col1:
                # Botão para gerar arquivo individual con curva completa
                if st.button("⚡ Curva", use_container_width=True,
                             help="Gera arquivo con curva gaussiana completa (múltiplos pontos)"):
                    # Obter dados do canal
                    dados = sistema.get_dados_canal(canal_nome)
                    params_temp = st.session_state.parametros_temporais

                    # Criar conteúdo do arquivo usando o método do sistema
                    conteudo_arquivo = sistema.gerar_conteudo_lamp(
                        dados, params_temp)

                    # Nome do arquivo baseado na seleção
                    nome_arquivo = arquivo_selecionado

                    # Criar download
                    st.download_button(
                        label=f"⬇️ Baixar TXT",
                        data=conteudo_arquivo,
                        file_name=nome_arquivo,
                        mime="text/plain",
                        use_container_width=True,
                        key=f"download_{nome_arquivo}"
                    )

            with col2:
                # Botão para gerar arquivo simplificado con ICE
                if st.button("📊 Linear", use_container_width=True,
                             help="Gera arquivo con apenas início e fim con ICE (2 linhas)"):
                    # Obter dados do canal
                    dados = sistema.get_dados_canal(canal_nome)
                    params_temp = st.session_state.parametros_temporais

                    # Criar conteúdo simplificado con ICE
                    conteudo_arquivo = sistema.gerar_conteudo_lamp_ice(
                        dados, params_temp)

                    # Nome do arquivo baseado na seleção (adiciona _ICE)
                    nome_arquivo = arquivo_selecionado.replace(
                        '.txt', '_ICE.txt')

                    # Criar download
                    st.download_button(
                        label=f"⬇️ Baixar TXT",
                        data=conteudo_arquivo,
                        file_name=nome_arquivo,
                        mime="text/plain",
                        use_container_width=True,
                        key=f"download_ice_{arquivo_selecionado.replace('.txt', '')}"
                    )

            with col3:
                # Botão para gerar todos os arquivos (ambos os formatos)
                if st.button("📦 Todos", use_container_width=True,
                             help="Gera todos os arquivos em ambos formatos"):
                    # Criar arquivo ZIP con todos os arquivos

                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Gerar cada um dos 4 arquivos em ambos formatos
                        arquivos_para_gerar = [
                            ("LAMP_CH1.txt", "vermelho"),
                            ("LAMP_CH2.txt", "azul"),
                            ("LAMP_CH3.txt", "branco"),
                            ("LAMP_CH4.txt", "branco")
                        ]

                        # Primeiro: arquivos con curva completa
                        for nome_arquivo, canal in arquivos_para_gerar:
                            dados = sistema.get_dados_canal(canal)
                            params_temp = st.session_state.parametros_temporais
                            conteudo = sistema.gerar_conteudo_lamp(
                                dados, params_temp)
                            zip_file.writestr(
                                f"curva_completa/{nome_arquivo}", conteudo)

                        # Segundo: arquivos con ICE simplificado
                        for nome_arquivo, canal in arquivos_para_gerar:
                            dados = sistema.get_dados_canal(canal)
                            params_temp = st.session_state.parametros_temporais
                            conteudo = sistema.gerar_conteudo_lamp_ice(
                                dados, params_temp)
                            nome_ice = nome_arquivo.replace('.txt', '_ICE.txt')
                            zip_file.writestr(
                                f"ice_simplificado/{nome_ice}", conteudo)

                        # Adicionar um arquivo README
                        readme_content = f"""
                        ARQUIVOS DE CONFIGURAÇÃO LAMP - AMBOS FORMATOS
                        Gerado em: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

                        ESTRUTURA DO ZIP:
                        ├── curva_completa/        - Arquivos con curva gaussiana completa
                        │   ├── LAMP_CH1.txt      - Canal Vermelho (curva completa)
                        │   ├── LAMP_CH2.txt      - Canal Azul (curva completa)
                        │   ├── LAMP_CH3.txt      - Canal Branco (curva completa)
                        │   └── LAMP_CH4.txt      - Cópia do Branco (curva completa)
                        │
                        └── ice_simplificado/     - Arquivos simplificados con ICE
                            ├── LAMP_CH1_ICE.txt - Canal Vermelho (apenas ICE)
                            ├── LAMP_CH2_ICE.txt - Canal Azul (apenas ICE)
                            ├── LAMP_CH3_ICE.txt - Canal Branco (apenas ICE)
                            └── LAMP_CH4_ICE.txt - Cópia do Branco (apenas ICE)

                        VALORES DE ICE POR CANAL:
                        - Vermelho: {sistema.get_dados_canal('vermelho')['ICE']:.1f} μmol/m²/s

                        - Azul: {sistema.get_dados_canal('azul')['ICE']:.1f} μmol/m²/s
                        - Branco: {sistema.get_dados_canal('branco')['ICE']:.1f} μmol/m²/s

                        Configurações utilizadas:
                        - Intensidade Total Máxima: {st.session_state.parametros_canais['intensidade_max_total']} μmol/m²/s
                        - Intensidade Total Mínima: {st.session_state.parametros_canais['intensidade_min_total']} μmol/m²/s
                        - Fotoperíodo: {st.session_state.parametros_temporais['hora_inicio']}:00 às {st.session_state.parametros_temporais['hora_fim']}:00
                        - Número de pontos: {st.session_state.parametros_temporais['n_pontos']}

                        FORMATO DOS ARQUIVOS:

                        1. Curva completa:
                        HH MM SS INTENSIDADE
                        (Múltiplas linhas ao longo do fotoperíodo)

                        2. ICE simplificado:
                        HH_INICIO 00 00 ICE
                        HH_FIM 00 00 ICE
                        (Apenas 2 linhas: início e fim con valor de ICE)
                        """
                        zip_file.writestr("README.txt", readme_content)

                        # Adicionar também um arquivo CSV con os ICEs
                        ice_data = []
                        for canal_nome, canal_display in [('vermelho', 'Vermelho'), ('azul', 'Azul'), ('branco', 'Branco')]:
                            dados_canal = sistema.get_dados_canal(canal_nome)
                            ice_data.append({
                                'Canal': canal_display,
                                'ICE_μmol_m2_s': round(dados_canal['ICE'], 1),
                                'DLI_mol_m2': round(dados_canal['DLI_final'], 3),
                                'Intensidade_Max': round(dados_canal['intensidade_max'], 1),
                                'Intensidade_Min': round(dados_canal['intensidade_min'], 1)
                            })

                        df_ice = pd.DataFrame(ice_data)
                        csv_ice = df_ice.to_csv(index=False)
                        zip_file.writestr("valores_ice.csv", csv_ice)

                    buffer.seek(0)

                    # Criar download do ZIP
                    st.download_button(
                        label="📥 Baixar ZIP",
                        data=buffer,
                        file_name="lamp_config_completo.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_all_formats_zip"
                    )

            # Resumo dos ICEs (se gerado Todos)
            with st.expander("👁️ Preview ICE e DLI", expanded=False):
                for canal_nome, canal_display in [('vermelho', 'Vermelho'), ('azul', 'Azul'), ('branco', 'Branco')]:
                    dados_canal = sistema.get_dados_canal(canal_nome)
                    st.metric(
                        f"ICE {canal_display}",
                        f"{dados_canal['ICE']:.1f} μmol/m²/s",
                        f"DLI: {dados_canal['DLI_final']:.1f} mol/m²")

            # Mostrar preview do arquivo selecionado
            with st.expander("👁️ Preview Graussin", expanded=False):
                dados = sistema.get_dados_canal(canal_nome)
                params_temp = st.session_state.parametros_temporais
                # Usar o método do sistema
                conteudo_arquivo = sistema.gerar_conteudo_lamp(
                    dados, params_temp)
                st.code(conteudo_arquivo, language="text")

        # Botão de instruções completas
        if st.button("Manual do Sistema",
                     use_container_width=True,
                     icon="📖",
                     help="Instruções detalhadas do sistema",
                     type="primary"):
            st.session_state.show_full_manual = True

    # 6. Rodapé
    st.markdown("---")
    with st.container():
        footer_cols = st.columns(3)

        with footer_cols[0]:
            st.caption("Última versão:")
            st.caption("1.0")

        with footer_cols[1]:
            st.caption("Meios de Contato:")
            st.caption("laac@ufv.br")

        with footer_cols[2]:
            st.caption("Última atualização:")
            st.caption(datetime.now().strftime("%d/%m/%Y"))

# ============================================================================
# MODAl DE AJUDA
# ============================================================================

# Inicializar estados dos modais
if 'show_quick_help' not in st.session_state:
    st.session_state.show_quick_help = False

if 'show_full_manual' not in st.session_state:
    st.session_state.show_full_manual = False

# MANUAL COMPLETO
if st.session_state.show_full_manual:
    # Chamar o manual modularizado
    exibir_manual_completo()


# ============================================================================
# FUNÇÕES PARA CADA ABA
# ============================================================================


def exibir_visao_geral():
    """Exibe a visão geral do sistema"""

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
            "⚪ DLI Branco",
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

    # Regressões lineares da bancada - LADO A LADO
    st.header("📐 Regressões Lineares da Bancada")

    col1, col2, col3 = st.columns(3)

    for idx, (canal_nome, col, cor) in enumerate(zip(
        ['azul', 'vermelho', 'branco'],
        [col1, col2, col3],
        [COLORS['azul'], COLORS['vermelho'], COLORS['branco']]
    )):
        with col:
            reg = sistema.regressoes[canal_nome]
            x_ref = st.session_state.dados_bancada[canal_nome]['valores_referencia']
            y_medido = reg['medianas']
            y_previsto = reg['valores_previstos_mediana']

            # Criar gráfico ECharts
            options = criar_grafico_regressao(
                canal_nome, reg, x_ref, y_medido, y_previsto, cor)
            st_echarts(options=options, height=400, key=f"reg_{canal_nome}",
                       renderer="canvas",
                       theme="light")

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

    # Gráficos Comparativos
    st.header("📈 Comparação entre Canais")

    # Gráfico 1: Intensidades comparadas con soma - CORREÇÃO 1
    options_intensidades = criar_grafico_comparacao_intensidades(
        dados_vermelho, dados_azul, dados_branco)
    # Corrigido: Adicionar apply_base_config
    options_intensidades = apply_base_config(options_intensidades)
    st_echarts(options=options_intensidades, height=500,
               key="comparacao_intensidades")

    # Criar abas para cada canal
    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        params_v = st.session_state.parametros_gaussianos['canal_vermelho']
        dados_v = sistema.get_dados_canal('vermelho')

        # Criar DataFrame com todos os pontos da gaussiana
        df_gauss_v = pd.DataFrame({
            'id': range(1, len(dados_v['x']) + 1),
            'x_normalizado': dados_v['x'],
            'hora_decimal': dados_v['hora_decimal'],
            'hora_formato': [f"{int(h)}:{int((h-int(h))*60):02d}:{int(((h-int(h))*60 - int((h-int(h))*60))*60):02d}" for h in dados_v['hora_decimal']],
            'intensidade_ppfd': dados_v['Intensidade'],
            'integral_acumulada': dados_v['Integral']
        })

        # Adicionar informações de resumo
        st.markdown(f"""
        **Parâmetros da Distribuição:**
        - σ (Sigma): `{params_v['sigma']:.3f}`
        - μ (Mi): `{params_v['mi']:.3f}`
        - Intensidade Máxima: `{dados_v['intensidade_max']:.1f}` μmol/m²/s
        - Intensidade Mínima: `{dados_v['intensidade_min']:.1f}` μmol/m²/s
        - Limite Máx Calibração: `{dados_v.get('limite_max_calibracao', 'N/A'):.1f}` μmol/m²/s
        - Limite Mín Calibração: `{dados_v.get('limite_min_calibracao', 'N/A'):.1f}` μmol/m²/s
        - ICE: `{dados_v['ICE']:.1f}` μmol/m²/s
        - DLI Final: `{dados_v['DLI_final']:.3f}` mol/m²
        """)

        # Mostrar tabela con todos os pontos (limitado a 50 pontos para não ficar muito grande)
        if len(df_gauss_v) > 50:
            df_display_v = df_gauss_v.iloc[::len(df_gauss_v)//50]
        else:
            df_display_v = df_gauss_v

        st.dataframe(
            df_display_v,
            column_config={
                "x_normalizado": st.column_config.NumberColumn("x (normalizado)", format="%.3f"),
                "hora_decimal": st.column_config.NumberColumn("Hora (decimal)", format="%.4f"),
                "hora_formato": st.column_config.TextColumn("Hora (HH:MM:SS)"),
                "intensidade_ppfd": st.column_config.NumberColumn("PPFD (μmol/m²/s)", format="%.1f"),
                "integral_acumulada": st.column_config.NumberColumn("Integral (mol/m²)", format="%.6f")
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

        # Botão para baixar dados completos
        csv_v = df_gauss_v.to_csv(index=False)
        st.download_button(
            label="📥 Baixar dados completos (CSV)",
            data=csv_v,
            file_name="gaussiana_vermelho_completa.csv",
            mime="text/csv",
            key="download_v"
        )

    with tab2:
        params_a = st.session_state.parametros_gaussianos['canal_azul']
        dados_a = sistema.get_dados_canal('azul')

        # Criar DataFrame com todos os pontos da gaussiana
        df_gauss_a = pd.DataFrame({
            'id': range(1, len(dados_a['x']) + 1),
            'x_normalizado': dados_a['x'],
            'hora_decimal': dados_a['hora_decimal'],
            'hora_formato': [f"{int(h)}:{int((h-int(h))*60):02d}:{int(((h-int(h))*60 - int((h-int(h))*60))*60):02d}" for h in dados_a['hora_decimal']],
            'intensidade_ppfd': dados_a['Intensidade'],
            'integral_acumulada': dados_a['Integral']
        })

        # Adicionar informações de resumo
        st.markdown(f"""
        **Parâmetros da Distribuição:**
        - σ (Sigma): `{params_a['sigma']:.3f}`
        - μ (Mi): `{params_a['mi']:.3f}`
        - Intensidade Máxima: `{dados_a['intensidade_max']:.1f}` μmol/m²/s
        - Intensidade Mínima: `{dados_a['intensidade_min']:.1f}` μmol/m²/s
        - Limite Máx Calibração: `{dados_a.get('limite_max_calibracao', 'N/A'):.1f}` μmol/m²/s
        - Limite Mín Calibração: `{dados_a.get('limite_min_calibracao', 'N/A'):.1f}` μmol/m²/s
        - ICE: `{dados_a['ICE']:.1f}` μmol/m²/s
        - DLI Final: `{dados_a['DLI_final']:.3f}` mol/m²
        """)

        # Mostrar tabela con todos os pontos
        if len(df_gauss_a) > 50:
            df_display_a = df_gauss_a.iloc[::len(df_gauss_a)//50]
        else:
            df_display_a = df_gauss_a

        st.dataframe(
            df_display_a,
            column_config={
                "x_normalizado": st.column_config.NumberColumn("x (normalizado)", format="%.3f"),
                "hora_decimal": st.column_config.NumberColumn("Hora (decimal)", format="%.4f"),
                "hora_formato": st.column_config.TextColumn("Hora (HH:MM:SS)"),
                "intensidade_ppfd": st.column_config.NumberColumn("PPFD (μmol/m²/s)", format="%.1f"),
                "integral_acumulada": st.column_config.NumberColumn("Integral (mol/m²)", format="%.6f")
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

        # Botão para baixar dados completos
        csv_a = df_gauss_a.to_csv(index=False)
        st.download_button(
            label="📥 Baixar dados completos (CSV)",
            data=csv_a,
            file_name="gaussiana_azul_completa.csv",
            mime="text/csv",
            key="download_a"
        )

    with tab3:
        params_b = st.session_state.parametros_gaussianos['canal_branco']
        dados_b = sistema.get_dados_canal('branco')

        # Criar DataFrame com todos os pontos da gaussiana
        df_gauss_b = pd.DataFrame({
            'id': range(1, len(dados_b['x']) + 1),
            'x_normalizado': dados_b['x'],
            'hora_decimal': dados_b['hora_decimal'],
            'hora_formato': [f"{int(h)}:{int((h-int(h))*60):02d}:{int(((h-int(h))*60 - int((h-int(h))*60))*60):02d}" for h in dados_b['hora_decimal']],
            'intensidade_ppfd': dados_b['Intensidade'],
            'integral_acumulada': dados_b['Integral']
        })

        # Adicionar informações de resumo
        st.markdown(f"""
        **Parâmetros da Distribuição:**
        - σ (Sigma): `{params_b['sigma']:.3f}`
        - μ (Mi): `{params_b['mi']:.3f}`
        - Intensidade Máxima: `{dados_b['intensidade_max']:.1f}` μmol/m²/s
        - Intensidade Mínima: `{dados_b['intensidade_min']:.1f}` μmol/m²/s
        - Limite Máx Calibração: `{dados_b.get('limite_max_calibracao', 'N/A'):.1f}` μmol/m²/s
        - Limite Mín Calibração: `{dados_b.get('limite_min_calibracao', 'N/A'):.1f}` μmol/m²/s
        - ICE: `{dados_b['ICE']:.1f}` μmol/m²/s
        - DLI Final: `{dados_b['DLI_final']:.3f}` mol/m²
        """)

        # Mostrar tabela con todos os pontos
        if len(df_gauss_b) > 50:
            df_display_b = df_gauss_b.iloc[::len(df_gauss_b)//50]
        else:
            df_display_b = df_gauss_b

        st.dataframe(
            df_display_b,
            column_config={
                "x_normalizado": st.column_config.NumberColumn("x (normalizado)", format="%.3f"),
                "hora_decimal": st.column_config.NumberColumn("Hora (decimal)", format="%.4f"),
                "hora_formato": st.column_config.TextColumn("Hora (HH:MM:SS)"),
                "intensidade_ppfd": st.column_config.NumberColumn("PPFD (μmol/m²/s)", format="%.1f"),
                "integral_acumulada": st.column_config.NumberColumn("Integral (mol/m²)", format="%.6f")
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )

        # Botão para baixar dados completos
        csv_b = df_gauss_b.to_csv(index=False)
        st.download_button(
            label="📥 Baixar dados completos (CSV)",
            data=csv_b,
            file_name="gaussiana_branco_completa.csv",
            mime="text/csv",
            key="download_b"
        )

    # Gráfico 2: DLIs finais comparados
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

    col1, col2, col3 = st.columns(3)

    with col1:
        options_dli = criar_grafico_barras_dli(dli_data)
        st_echarts(options=options_dli, height=300, key="barras_dli")

    with col2:
        options_ice = criar_grafico_barras_ice(dli_data)
        st_echarts(options=options_ice, height=300, key="barras_ice")

    # Gráfico de Comparação de Intensidades por Canal
    # Calcular intensidades por canal
    with col3:
        # Usar intensidades calculadas que respeitam a calibração
        intensidades_max = [dados_azul['intensidade_max'],
                            dados_vermelho['intensidade_max'],
                            dados_branco['intensidade_max']]
        intensidades_min = [dados_azul['intensidade_min'],
                            dados_vermelho['intensidade_min'],
                            dados_branco['intensidade_min']]

        options_barras = criar_grafico_comparacao_intensidades_barras(
            intensidades_max, intensidades_min)
        st_echarts(options=options_barras, height=300,
                   key="comparacao_intensidades_barras_visao_geral")


def exibir_calibracao_bancada():
    """Exibe a interface de calibração da bancada"""

    # Selecionar canal
    canal_selecionado = st.selectbox(
        "Selecione o canal para calibração:",
        ["Vermelho", "Azul", "Branco"],
        key="canal_calibracao"
    )

    canal_key = canal_selecionado.lower()
    dados_canal = st.session_state.dados_bancada[canal_key]

    col1, col2 = st.columns([3, 1])

    with col1:
        with st.container():
            reg = sistema.regressoes[canal_key]['regressao_media']
            medias = sistema.regressoes[canal_key]['medias']

            cols = st.columns(5)
            metrics = [
                ("Média Máx", f"{max(medias):.1f}", "μmol/m²/s"),
                ("Média Mín", f"{min(medias):.1f}", "μmol/m²/s"),
                ("Intercepto", f"{reg['a']:.4f}", ""),
                ("Inclinação", f"{reg['b']:.1f}", ""),
                ("R²", f"{reg['r2']:.4f}", "")
            ]

            for i, (label, value, unit) in enumerate(metrics):
                with cols[i]:
                    st.metric(label, value, delta=unit if unit else None)

    with col2:
        if st.button(icon="🔄", label="Restaurar Valores Padrão",
                     key=f"reset_button_{canal_key}",
                     help="Restaura os valores padrão de calibração para este canal"):
            # Restaurar valores padrão para cada canal
            if canal_key == 'azul':
                default_data = np.array([
                    [24.86, 29.3, 27.6, 22.53, 29.51],
                    [76.45, 74.32, 73.75, 58.78, 66.12],
                    [114.8, 106.9, 114.6, 102.9, 100.9],
                    [135.5, 127.1, 138.0, 120.2, 119.8],
                    [175.7, 177.0, 164.1, 145.0, 170.0]
                ]).T
                default_ref = np.array([0, 0.3, 0.5, 0.7, 1.0])
            elif canal_key == 'vermelho':
                default_data = np.array([
                    [58.12, 57.3, 54.3, 55.9, 52.0],
                    [143.9, 168.3, 160.4, 147.6, 158.1],
                    [235.3, 227.2, 198.0, 233.5, 224.5],
                    [279.5, 293.3, 272.2, 302.7, 281.7],
                    [360.5, 354.2, 407.3, 398.5, 367.8]
                ]).T
                default_ref = np.array([0, 0.3, 0.5, 0.7, 1.0])
            else:  # branco
                default_data = np.array([
                    [20.61, 24.51, 24.24, 22.42, 23.14],
                    [62.13, 67.69, 58.93, 59.12, 55.09],
                    [69.18, 92.19, 91.02, 86.68, 84.73],
                    [109.8, 104.6, 117.0, 113.7, 110.3],
                    [120.8, 150.9, 143.3, 130.7, 143.9]
                ]).T
                default_ref = np.array([0, 0.3, 0.5, 0.7, 1.0])

            st.session_state.dados_bancada[canal_key]['dados'] = default_data
            st.session_state.dados_bancada[canal_key]['valores_referencia'] = default_ref

            sistema.calcular_regressoes()

            st.success(
                f"✅ Valores padrão restaurados para {canal_key.capitalize()}!")
            st.rerun()

        # Exibir mensagem de confirmação se acabou de restaurar
        if st.session_state.get(f'restaurado_{canal_key}', False):
            st.info(
                f"Valores padrão do canal {canal_key.capitalize()} foram restaurados.")
            st.session_state[f'restaurado_{canal_key}'] = False

    # Interface de entrada de dados
    col1, col2 = st.columns([2, 2])

    with col1:
        st.markdown("**Valores de Referência:**")
        ref_vals = dados_canal['valores_referencia']

        grid_container = st.container()
        with grid_container:
            cols = st.columns(6, width=800)
            with cols[0]:
                st.markdown("**Repetição**", unsafe_allow_html=True,
                            text_alignment="center")
            for i in range(5):
                with cols[i+1]:
                    st.markdown(
                        f"**Intensidade**</br>{ref_vals[i]*100}%</br>",
                        unsafe_allow_html=True,
                        text_alignment="center")

            for rep in range(5):
                cols = st.columns(6, width=800)
                with cols[0]:
                    st.markdown(f"**{rep+1}**", text_alignment="center")
                for intens in range(5):
                    with cols[intens+1]:
                        key = f"input_{canal_key}_{rep}_{intens}"
                        valor = st.number_input(
                            "",
                            min_value=0.0,
                            max_value=1000.0,
                            value=float(dados_canal['dados'][rep, intens]),
                            step=0.1,
                            format="%.2f",
                            key=key,
                            label_visibility="collapsed",
                        )
                        if valor != dados_canal['dados'][rep, intens]:
                            dados_canal['dados'][rep, intens] = valor
                            sistema.calcular_regressoes()

    # Criar gráfico para regressão
    with col2:
        reg = sistema.regressoes[canal_key]
        x_ref = st.session_state.dados_bancada[canal_key]['valores_referencia']

        # Preparar dados para o gráfico
        series_data = []

        # Adicionar repetições
        for rep in range(5):
            series_data.append({
                "name": f'Rep {rep+1}',
                "type": "scatter",
                "data": [[float(x_ref[i]), float(dados_canal['dados'][rep, i])] for i in range(5)],
                "symbolSize": 8,
                "itemStyle": {
                    "color": f'rgba({100 + rep * 30}, {100 + rep * 30}, {100 + rep * 30}, 0.7)'
                }
            })

        # Adicionar média
        medias = sistema.regressoes[canal_key]['medias']
        series_data.append({
            "name": 'Média',
            "type": "line",
            "data": [[float(round(x_ref[i], 1)), float(round(medias[i], 1))] for i in range(5)],
            "lineStyle": {
                "color": COLORS["soma"],
                "width": 3
            },
            "symbol": "circle",
            "symbolSize": 12,
            "itemStyle": {
                "color": COLORS["soma"]
            }
        })

        # Adicionar regressão
        y_previsto = sistema.regressoes[canal_key]['valores_previstos_media']
        series_data.append({
            "name": 'Regressão (média)',
            "type": "line",
            "data": [[float(x_ref[i]), float(y_previsto[i])] for i in range(5)],
            "lineStyle": {
                "color": COLORS['vermelho'] if canal_key == 'vermelho' else COLORS['azul'] if canal_key == 'azul' else COLORS['branco'],
                "width": 2,
                "type": "dashed"
            },
            "smooth": True,
            "showSymbol": False
        })

        options = {
            "title": {
                "text": f'Regressão Linear - Canal {canal_selecionado}',
                "left": "center"
            },
            "tooltip": {},
            "legend": {
                "data": [f'Rep {i+1}' for i in range(5)] + ['Média', 'Regressão (média)'],
                "top": "10%",
                "type": "scroll"
            },
            "xAxis": {
                "name": "Valor de Referência",
                "nameLocation": "middle",
                "nameGap": 30,
                "type": "value"
            },
            "yAxis": {
                "name": "PPFD Medido (μmol/m²/s)",
                "nameLocation": "middle",
                "nameGap": 50,
                "type": "value"
            },
            "series": series_data,
            "grid": {
                "left": "15%",
                "right": "10%",
                "bottom": "20%",
                "top": "20%"
            }
        }

        st_echarts(options=options, height=500, key="calibracao_grafico",
                   renderer="canvas")


def exibir_configurar_canais():
    """Exibe a interface para configurar os canais"""

    # Inicializar estado da visualização se não existir
    if 'canal_configuracao_atual' not in st.session_state:
        st.session_state.canal_configuracao_atual = "Vermelho"

    if 'ultima_atualizacao_config' not in st.session_state:
        st.session_state.ultima_atualizacao_config = {
            'proporcoes': (1.0, 1.0, 1.0),
            'gaussianas': (0.3, 0.3, 0.3, 0.5, -0.5, 0.0),
            'intensidades': (650.0, 120.0)
        }

    # Formulário de configuração
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.subheader("🔍 Visualizar", anchor=False)
        # Seletor para visualização detalhada do canal
        canal_selecionado = st.selectbox(
            "Selecione o canal",
            ["Vermelho", "Azul", "Branco"],
            key="canal_detalhado_config",
            index=["Vermelho", "Azul", "Branco"].index(
                st.session_state.canal_configuracao_atual)
        )

        # Armazenar a seleção atual
        if canal_selecionado != st.session_state.canal_configuracao_atual:
            st.session_state.canal_configuracao_atual = canal_selecionado

        # Mapear seleção para nomes internos
        canal_map = {
            "Vermelho": ("vermelho", "🔴", "Vermelho"),
            "Azul": ("azul", "🔵", "Azul"),
            "Branco": ("branco", "⚪", "Branco")
        }

    canal_nome, emoji, nome_display = canal_map[canal_selecionado]

    with col2:
        st.subheader("📊 Proporções",
                     help="Proporção física entre os LEDs", anchor=False)

        # Number inputs con valores inteiros de 1 a 5
        col_slider1, col_slider2, col_slider3 = st.columns(3)

        with col_slider1:
            proporcao_azul = st.number_input(
                "Azul",
                min_value=1,
                max_value=5,
                value=int(
                    st.session_state.parametros_canais['proporcao_azul']),
                step=1,
                key="prop_azul_config",
                help="Proporção do canal Azul (1 a 5)"
            )

        with col_slider2:
            proporcao_vermelho = st.number_input(
                "Vermelho",
                min_value=1,
                max_value=5,
                value=int(
                    st.session_state.parametros_canais['proporcao_vermelho']),
                step=1,
                key="prop_vermelho_config",
                help="Proporção do canal Vermelho (1 a 5)"
            )

        with col_slider3:
            proporcao_branco = st.number_input(
                "Branco",
                min_value=1,
                max_value=5,
                value=int(
                    st.session_state.parametros_canais['proporcao_branco']),
                step=1,
                key="prop_branco_config",
                help="Proporção do canal Branco (1 a 5)"
            )

    with col3:
        st.subheader("⚡ Intensidades Totais",
                     help="Intensidades máximas e mínimas totais combinadas dos canais acima do mínimo e abaixo do máximo mensurados",
                     anchor=False)

        # Criar 2 colunas para os inputs lado a lado
        col_max, col_min = st.columns(2)

        with col_max:
            intensidade_max_total = st.number_input(
                "Máx. Total (μmol/m²/s)",
                min_value=0.0,
                max_value=2000.0,
                value=st.session_state.parametros_canais['intensidade_max_total'],
                step=10.0,
                key="int_max_total_config",
                help="Intensidade máxima total combinada dos canais"
            )

        with col_min:
            intensidade_min_total = st.number_input(
                "Mín. Total (μmol/m²/s)",
                min_value=0.0,
                max_value=1000.0,
                value=st.session_state.parametros_canais['intensidade_min_total'],
                step=10.0,
                key="int_min_total_config",
                help="Intensidade mínima total combinada dos canais"
            )

    # Exibir detalhes do canal selecionado
    st.markdown("---")

    # Obter dados do canal
    dados = sistema.get_dados_canal(canal_nome)
    params_gauss = st.session_state.parametros_gaussianos[f'canal_{canal_nome}']
    params_temp = st.session_state.parametros_temporais

    # Gráfico comparativo de intensidades
    st.subheader(f"📈 Comparação de Intensidades - Todos os Canais")

    # Obter dados de todos os canais para o gráfico comparativo
    dados_vermelho = sistema.get_dados_canal('vermelho')
    dados_azul = sistema.get_dados_canal('azul')
    dados_branco = sistema.get_dados_canal('branco')

    options_intensidades = criar_grafico_comparacao_intensidades(
        dados_vermelho, dados_azul, dados_branco)
    options_intensidades = apply_base_config(options_intensidades)

    # Usar uma chave estável para o gráfico comparativo
    st_echarts(options=options_intensidades, height=500,
               key="comparacao_intensidades_config_principal")

    st.subheader(f"{emoji} Detalhes do Canal {nome_display}")

    # Verificar se houve mudanças nos parâmetros
    mudancas_detectadas = False
    proporcoes_atual = (
        float(proporcao_azul),
        float(proporcao_vermelho),
        float(proporcao_branco)
    )
    proporcoes_anterior = st.session_state.ultima_atualizacao_config['proporcoes']

    intensidades_atual = (intensidade_max_total, intensidade_min_total)
    intensidades_anterior = st.session_state.ultima_atualizacao_config['intensidades']

    # Verificar se houve mudanças
    if (proporcoes_atual != proporcoes_anterior or
            intensidades_atual != intensidades_anterior):
        mudancas_detectadas = True
        st.session_state.ultima_atualizacao_config.update({
            'proporcoes': proporcoes_atual,
            'intensidades': intensidades_atual
        })

    # Atualizar parâmetros somente se houver mudanças
    if mudancas_detectadas:
        st.session_state.parametros_canais.update({
            'intensidade_max_total': intensidade_max_total,
            'intensidade_min_total': intensidade_min_total,
            'proporcao_azul': float(proporcao_azul),
            'proporcao_vermelho': float(proporcao_vermelho),
            'proporcao_branco': float(proporcao_branco)
        })

    container_detalhes = st.container()

    with container_detalhes:
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Gráfico de intensidade - usar chave única baseada no canal
            cor = COLORS['vermelho'] if canal_nome == 'vermelho' else COLORS['azul'] if canal_nome == 'azul' else COLORS['branco']
            options_intensidade = criar_grafico_canal_detalhes(
                dados, canal_nome, cor, params_gauss)
            st_echarts(options=options_intensidade, height=400,
                       key=f"intensidade_{canal_nome}_config_detalhe")

        with col2:
            # Gráfico da integral - usar chave única baseada no canal
            options_integral = criar_grafico_integral(dados, canal_nome, cor)
            st_echarts(options=options_integral, height=400,
                       key=f"integral_{canal_nome}_config_detalhe",
                       renderer="canvas",
                       theme="light")

        with col3:
            # Gráfico da distribuição gaussiana - usar chave única baseada no canal
            options_gaussiana = criar_grafico_gaussiana(
                dados, canal_nome, cor, params_gauss['sigma'], params_gauss['mi'])
            st_echarts(options=options_gaussiana, height=400,
                       key=f"gaussiana_{canal_nome}_config_detalhe")


def exibir_simular_espectro():
    """Exibe a interface para simulação de espectros usando ECharts"""

    import json
    import os
    # Carregar espectros do arquivo spectra_data.json
    spectra_path = os.path.join(os.path.dirname(__file__), "spectra_data.json")
    # usar cache para leitura do JSON (evita re-leitura em cada rerun)

    @st.cache_data
    def load_spectra(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    spectra_data = load_spectra(spectra_path)

    # Verificar consistência dos comprimentos entre 'wavelengths' e arrays de dados
    def _check_spectra_lengths(spectra):
        candidate_keys = ("irradiance", "transmittance",
                          "absorbance", "values", "data")
        problems = []
        for name, obj in spectra.items():
            wl = obj.get("wavelengths")
            if not isinstance(wl, list):
                problems.append(
                    (name, "wavelengths missing or not list", None, None))
                continue
            wl_len = len(wl)
            found = False
            for k in candidate_keys:
                if k in obj:
                    found = True
                    arr = obj.get(k)
                    if not isinstance(arr, list):
                        problems.append((name, k + " not list", wl_len, None))
                    elif len(arr) != wl_len:
                        problems.append((name, k, wl_len, len(arr)))
                    break
            if not found:
                problems.append(
                    (name, "no data array (irradiance/transmittance/absorbance/...)", wl_len, None))
        return problems

    inconsistencies = _check_spectra_lengths(spectra_data)
    if inconsistencies:
        # Agrupar todas as mensagens em um único balão para manter a interface limpa
        lines = [
            f"Foram encontradas {len(inconsistencies)} entradas com comprimentos inconsistentes em spectra_data.json:"]
        for entry in inconsistencies:
            name, key, wl_len, arr_len = entry
            if arr_len is None:
                lines.append(f" - {name}: {key} (wavelengths={wl_len})")
            else:
                lines.append(
                    f" - {name}: {key} (wavelengths={wl_len} vs {key}={arr_len})")
        st.warning("\n".join(lines))

        # Oferecer ação de correção automática
        if st.button("Corrigir automaticamente (interpolar) usando scripts/fix_spectra_interpolate.py"):
            import subprocess
            try:
                res = subprocess.run(
                    ["python3", "scripts/fix_spectra_interpolate.py"], capture_output=True, text=True, check=False)
                st.code(res.stdout or "(sem saída)")
                if res.stderr:
                    st.error(res.stderr)
                # limpar cache e recarregar os dados
                try:
                    load_spectra.clear()
                except Exception:
                    pass
                spectra_data = load_spectra(spectra_path)
                st.success(
                    "Correção executada. spectra_data.json recarregado.")
                # recomputar inconsistências para informar ao usuário
                inconsistencies = _check_spectra_lengths(spectra_data)
                if inconsistencies:
                    lines2 = ["Após correção, ainda há inconsistências:"]
                    for entry in inconsistencies:
                        name, key, wl_len, arr_len = entry
                        lines2.append(
                            f" - {name}: {key} (wavelengths={wl_len} vs {key}={arr_len})")
                    st.warning("\n".join(lines2))
                    st.stop()
                else:
                    st.info(
                        "Todos os espectros têm comprimentos compatíveis agora.")
                    st.info(
                        "Por favor, recarregue manualmente a página (F5) para aplicar as mudanças e continuar.")
                    st.stop()
            except Exception as e:
                st.error(f"Falha ao executar o script de correção: {e}")

        # Interromper a execução enquanto houver inconsistências para evitar renderizar gráficos
        st.info("Corrija as inconsistências no arquivo spectra_data.json ou use o botão acima. A página ficará parada até a correção.")
        st.stop()

    # Gerar nomes amigáveis para o selectbox
    def nome_amigavel(chave):
        nomes = {
            "Chlorophyll a": "Clorofila A (absorbância)",
            "Chlorophyll b": "Clorofila B (absorbância)",
            "Beta Carotene": "Beta-caroteno (absorbância)",
            "Zeaxanthin": "Zeaxantina (absorbância)",
            "Anthocyanin": "Antocianina (absorbância)",
            "Phytochrome Pr": "Phytochrome Pr (absorbância)",
            "Phytochrome Pfr": "Phytochrome Pfr (absorbância)",
            "Cryptochrome": "Criptocromo (absorbância)",
            "LOV": "LOV (absorbância)",
            "Phycoerythrin": "Ficoeritrina (absorbância)",
            "Phycocyanin": "Ficocianina (absorbância)",
            "Allophycocyanin": "Aloficocianina (absorbância)",
            "LED_Branco": "LED Branco (irradiância)",
            "LED_Azul": "LED Azul (irradiância)",
            "LED_Vermelho": "LED Vermelho (irradiância)"
        }
        return nomes.get(chave, chave)

    opcoes_espectros = list(spectra_data.keys())
    opcoes_amigaveis = [nome_amigavel(k) for k in opcoes_espectros]

    # Divisão em duas colunas para configurações
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

    with col1:
        espectro_idx = st.selectbox(
            "Selecione o espectro de referência:",
            options=range(len(opcoes_amigaveis)),
            format_func=lambda i: opcoes_amigaveis[i],
            index=0,
            placeholder="Selecione um espectro..."
        )
        espectro_ref = opcoes_espectros[espectro_idx]

    # Configurações do usuário
    with col2:
        faixa_min = st.number_input(
            " λ mínimo (nm):", 380, 780, 380)

    with col3:
        faixa_max = st.number_input(
            " λ máximo (nm):", 380, 780, 780)

    with col4:
        resolucao = st.slider(
            "Resolução espectral (nm):",
            min_value=1, max_value=10, value=5, step=1,
            help="Passo em nm para reamostragem quando não usar resolução nativa."
        )
    with col5:
        limiar_picos_pct = st.slider(
            "Limiar de picos (% do máximo):",
            min_value=0, max_value=100, value=25, step=5,
            help="Define o limiar relativo para detectar picos locais como porcentagem do valor máximo da série"

        )
        limiar_picos = float(limiar_picos_pct) / 100.0

    c_native, c_log, col3, col4 = st.columns([1, 1, 1, 1])
    with c_native:
        use_native = st.checkbox(
            "Resolução nativa do espectro",
            value=False,
            disabled=False,
            help="Se ativado, usa os comprimentos de onda originais do espectro selecionado (melhor fidelidade)."
        )
    with c_log:
        use_norm_leds = st.checkbox(
            "Visualizar LEDs normalizados (0-1)",
            value=True,
            help="Normaliza visualmente os espectros dos LEDs para o intervalo [0,1] apenas na visualização (não altera cálculos)."
        )

    # grid preliminar (pode ser sobrescrito pela resolução nativa mais abaixo)
    wavelengths = np.arange(faixa_min, faixa_max + resolucao, resolucao)

    espectro_json = spectra_data.get(espectro_ref)
    if espectro_json is None:
        st.error(
            f"Espectro '{espectro_ref}' não encontrado no arquivo spectra_data.json.")
        return

    # Cálculos pesados e reamostragem cacheados para minimizar custo em reruns
    @st.cache_data
    def compute_spectral_data(espectro_json, spectra_data, faixa_min, faixa_max, resolucao, use_native, max_points=2000):
        # preparar grade
        wavelengths = np.arange(faixa_min, faixa_max + resolucao, resolucao)

        # resolver grade nativa
        if use_native:
            native_wl = np.array(espectro_json.get(
                "wavelengths", []), dtype=float)
            if native_wl.size > 0:
                mask = (native_wl >= faixa_min) & (native_wl <= faixa_max)
                native_grid = native_wl[mask]
                if native_grid.size > 0:
                    wavelengths = native_grid

        # safety cap
        if len(wavelengths) > max_points:
            factor = int(np.ceil(len(wavelengths) / max_points))
            wavelengths = wavelengths[::factor]

        espectro_wl = np.array(espectro_json.get(
            "wavelengths", []), dtype=float)
        if "absorbance" in espectro_json:
            espectro_vals = np.array(espectro_json["absorbance"], dtype=float)
            tipo_espectro = "absorbância"
            cor_espectro = "#2E86AB"
        elif "irradiance" in espectro_json:
            espectro_vals = np.array(espectro_json["irradiance"], dtype=float)
            tipo_espectro = "irradiance"
            cor_espectro = "#FFD166"
        elif "irradiance" in espectro_json:
            espectro_vals = np.array(
                espectro_json["irradiance"], dtype=float)
            tipo_espectro = "transmittância"
            cor_espectro = "#E0E6ED"
        else:
            espectro_vals = np.array([])
            tipo_espectro = "unknown"
            cor_espectro = "#999"

        if espectro_wl.size == 0 or espectro_vals.size == 0:
            espectro_ref_valores = np.zeros_like(wavelengths, dtype=float)
        else:
            espectro_ref_valores = np.interp(
                wavelengths, espectro_wl, espectro_vals)

        # carregar LEDs e reamostrar
        def interp_led(key):
            led_json = spectra_data.get(key, {})
            if not led_json:
                return np.zeros_like(wavelengths, dtype=float)
            xp = np.array(led_json.get("wavelengths", []), dtype=float)
            # try common keys for led data
            fp = None
            for k in ("irradiance", "transmittance", "absorbance", "values", "data"):
                if k in led_json:
                    fp = np.array(led_json.get(k, []), dtype=float)
                    break
            if fp is None:
                fp = np.array([])

            if xp.size == 0 or fp.size == 0:
                return np.zeros_like(wavelengths, dtype=float)

            if xp.size == fp.size:
                order = np.argsort(xp)
                xp_s = xp[order]
                fp_s = fp[order]
                return np.interp(wavelengths, xp_s, fp_s)

            if fp.size == 1:
                return np.full_like(wavelengths, float(fp[0]), dtype=float)

            # fallback: assume fp sampled uniformly across xp_range
            try:
                xp_fp = np.linspace(xp.min(), xp.max(), fp.size)
                f = interp1d(xp_fp, fp, kind='linear',
                             bounds_error=False, fill_value=0.0)
                fp_on_xp = f(xp) if xp.size > 1 else np.full_like(
                    xp, float(fp.mean()))
                order = np.argsort(xp)
                xp_s = xp[order]
                fp_s = fp_on_xp[order]
                return np.interp(wavelengths, xp_s, fp_s)
            except Exception:
                return np.zeros_like(wavelengths, dtype=float)

        led_vermelho = interp_led("LED_Vermelho")
        led_azul = interp_led("LED_Azul")
        led_branco = interp_led("LED_Branco")

        # escala se for irradiance
        if tipo_espectro == "irradiance" and espectro_ref_valores.sum() > 0:
            intensidade_ref = 650
            fator_escala = intensidade_ref / \
                (np.trapezoid(espectro_ref_valores, wavelengths) / 1000)
            espectro_ref_valores = espectro_ref_valores * fator_escala

        # funções utilitarias
        def identificar_picos(espectro, wavelengths, threshold=0.3):
            picos = []
            for i in range(1, len(espectro)-1):
                if espectro[i] > espectro[i-1] and espectro[i] > espectro[i+1] and espectro[i] > threshold:
                    picos.append({'wavelength': float(
                        wavelengths[i]), 'intensity': float(espectro[i]), 'fwhm': 20})
            return picos

        def calcular_pfd_bandas(espectro, wavelengths):
            bandas = {'UV': (380, 400), 'BLUE': (400, 500), 'GREEN': (
                500, 600), 'RED': (600, 700), 'FAR_RED': (700, 780)}
            resultados = {}
            for nome, (min_wl, max_wl) in bandas.items():
                mask = (wavelengths >= min_wl) & (wavelengths <= max_wl)
                if np.any(mask):
                    area = np.trapezoid(espectro[mask], wavelengths[mask])
                    resultados[nome] = float(area / 1000)
                else:
                    resultados[nome] = 0.0
            mask_par = (wavelengths >= 400) & (wavelengths <= 700)
            resultados['PPFD'] = float(np.trapezoid(
                espectro[mask_par], wavelengths[mask_par]) / 1000) if np.any(mask_par) else 0.0
            return resultados

        def calcular_lamp_otimo(espectro_ref, led_v, led_a, led_b):
            X = np.column_stack([led_v, led_a, led_b])
            coef, residuals, rank, s = np.linalg.lstsq(
                X, espectro_ref, rcond=None)
            coef = np.maximum(coef, 0)
            if coef.max() > 0:
                coef = coef / coef.max()
            return [float(c) for c in coef]

        picos_ref = identificar_picos(espectro_ref_valores, wavelengths)
        pfd_ref = calcular_pfd_bandas(espectro_ref_valores, wavelengths)
        pfd_vermelho = calcular_pfd_bandas(led_vermelho, wavelengths)
        pfd_azul = calcular_pfd_bandas(led_azul, wavelengths)
        pfd_branco = calcular_pfd_bandas(led_branco, wavelengths)

        coef = calcular_lamp_otimo(
            espectro_ref_valores, led_vermelho, led_azul, led_branco)
        proporcoes_lamp = {
            'LAMP_CH1_Vermelho': coef[0], 'LAMP_CH2_Azul': coef[1], 'LAMP_CH3_Branco': coef[2]}
        lamp_ch1 = led_vermelho * proporcoes_lamp['LAMP_CH1_Vermelho']
        lamp_ch2 = led_azul * proporcoes_lamp['LAMP_CH2_Azul']
        lamp_ch3 = led_branco * proporcoes_lamp['LAMP_CH3_Branco']
        lamp_soma = lamp_ch1 + lamp_ch2 + lamp_ch3
        pfd_lamp_ch1 = calcular_pfd_bandas(lamp_ch1, wavelengths)
        pfd_lamp_ch2 = calcular_pfd_bandas(lamp_ch2, wavelengths)
        pfd_lamp_ch3 = calcular_pfd_bandas(lamp_ch3, wavelengths)
        pfd_lamp_soma = calcular_pfd_bandas(lamp_soma, wavelengths)

        return {
            'wavelengths': wavelengths,
            'espectro_ref_valores': espectro_ref_valores,
            'led_vermelho': led_vermelho,
            'led_azul': led_azul,
            'led_branco': led_branco,
            'picos_ref': picos_ref,
            'pfd_ref': pfd_ref,
            'pfd_vermelho': pfd_vermelho,
            'pfd_azul': pfd_azul,
            'pfd_branco': pfd_branco,
            'proporcoes_lamp': proporcoes_lamp,
            'lamp_ch1': lamp_ch1,
            'lamp_ch2': lamp_ch2,
            'lamp_ch3': lamp_ch3,
            'lamp_soma': lamp_soma,
            'pfd_lamp_ch1': pfd_lamp_ch1,
            'pfd_lamp_ch2': pfd_lamp_ch2,
            'pfd_lamp_ch3': pfd_lamp_ch3,
            'pfd_lamp_soma': pfd_lamp_soma,
            'tipo_espectro': tipo_espectro,
            'cor_espectro': cor_espectro
        }

    # calcular (cacheado) - menor custo nas reruns
    computed = compute_spectral_data(
        espectro_json, spectra_data, faixa_min, faixa_max, resolucao, use_native)

    # expandir resultados locais
    wavelengths = computed['wavelengths']
    espectro_ref_valores = computed['espectro_ref_valores']
    led_vermelho = computed['led_vermelho']
    led_azul = computed['led_azul']
    led_branco = computed['led_branco']
    picos_ref = computed['picos_ref']
    pfd_ref = computed['pfd_ref']
    pfd_vermelho = computed['pfd_vermelho']
    pfd_azul = computed['pfd_azul']
    pfd_branco = computed['pfd_branco']
    proporcoes_lamp = computed['proporcoes_lamp']
    lamp_ch1 = computed['lamp_ch1']
    lamp_ch2 = computed['lamp_ch2']
    lamp_ch3 = computed['lamp_ch3']
    lamp_soma = computed['lamp_soma']
    pfd_lamp_ch1 = computed['pfd_lamp_ch1']
    pfd_lamp_ch2 = computed['pfd_lamp_ch2']
    pfd_lamp_ch3 = computed['pfd_lamp_ch3']
    pfd_lamp_soma = computed['pfd_lamp_soma']
    tipo_espectro = computed['tipo_espectro']
    cor_espectro = computed['cor_espectro']

    # --- Preparar arrays de visualização (não alteram os dados computados) ---
    def _is_in_0_1(arr):
        try:
            a = np.array(arr, dtype=float)
            if a.size == 0:
                return False
            amin = np.nanmin(a)
            amax = np.nanmax(a)
            return (np.isfinite(amin) and np.isfinite(amax) and amin >= 0.0 and amax <= 1.0)
        except Exception:
            return False

    def _to_0_1_for_viz(arr):
        a = np.array(arr, dtype=float)
        if a.size == 0:
            return a
        if _is_in_0_1(a):
            return a
        # forçar não-negativos
        a = np.where(np.isfinite(a), a, 0.0)
        a[a < 0] = 0.0
        amin = a.min()
        amax = a.max()
        if amax <= amin:
            return np.zeros_like(a)
        return (a - amin) / (amax - amin)

    viz_led_vermelho = led_vermelho.copy()
    viz_led_azul = led_azul.copy()
    viz_led_branco = led_branco.copy()
    if 'use_norm_leds' in locals() and use_norm_leds:
        viz_led_vermelho = _to_0_1_for_viz(viz_led_vermelho)
        viz_led_azul = _to_0_1_for_viz(viz_led_azul)
        viz_led_branco = _to_0_1_for_viz(viz_led_branco)

    # preparar markPoints com coordenadas de picos (pode identificar múltiplos picos)
    def _peak_markpoints(wl, arr, rel_threshold=0.3, max_peaks=5):
        try:
            a = np.array(arr, dtype=float)
            w = np.array(wl, dtype=float)
            if a.size < 3 or w.size < 3:
                return {}
            # limiar relativo baseado no máximo
            maxv = np.nanmax(a)
            if not np.isfinite(maxv) or maxv <= 0:
                return {}
            thresh = maxv * float(rel_threshold)
            points = []
            for i in range(1, len(a)-1):
                if a[i] > a[i-1] and a[i] > a[i+1] and a[i] >= thresh:
                    points.append((float(w[i]), float(a[i])))
            if not points:
                # fallback: use global max if no local peaks above threshold
                idx = int(np.nanargmax(a))
                points = [(float(w[idx]), float(a[idx]))]
            # limitar número de picos
            points = points[:int(max_peaks)]
            data = []
            for (wx, vx) in points:
                data.append({
                    "coord": [wx, vx],
                    "name": "Pico",
                    "label": {"show": True, "formatter": f"{int(round(wx))} nm", "position": "top"}
                })
            return {
                "data": data,
                "symbol": "pin",
                "itemStyle": {
                    "borderColor": "#333",
                    "borderWidth": 1,
                    "shadowBlur": 8,
                    "shadowColor": "rgba(0,0,0,0.25)",
                    "opacity": 0.95
                },
                "symbolSize": [18, 18]
            }
        except Exception:
            return {}

    # usar limiar definido pelo usuário (limiar_picos) — fallback para valores padrão se não existir
    try:
        user_thresh = float(limiar_picos)
    except Exception:
        user_thresh = 0.25
    mark_v = _peak_markpoints(
        wavelengths, viz_led_vermelho, rel_threshold=user_thresh)
    mark_a = _peak_markpoints(
        wavelengths, viz_led_azul, rel_threshold=user_thresh)
    mark_b = _peak_markpoints(
        wavelengths, viz_led_branco, rel_threshold=user_thresh)
    mark_ref = _peak_markpoints(
        wavelengths, espectro_ref_valores, rel_threshold=max(0.05, user_thresh * 0.8))

    # ============================================================================
    # CÁLCULO DE ICE PARA CADA LAMP BASEADO NO ESPECTRO DE REFERÊNCIA
    # ============================================================================

    # Obter intensidade máxima total da configuração atual
    intensidade_max_total = st.session_state.parametros_canais['intensidade_max_total']
    intensidade_min_total = st.session_state.parametros_canais['intensidade_min_total']

    # Obter proporções atuais dos canais
    proporcoes_atuais = np.array([
        st.session_state.parametros_canais['proporcao_vermelho'],
        st.session_state.parametros_canais['proporcao_azul'],
        st.session_state.parametros_canais['proporcao_branco']
    ])

    # Normalizar proporções
    if proporcoes_atuais.sum() > 0:
        proporcoes_norm = proporcoes_atuais / proporcoes_atuais.sum()
    else:
        proporcoes_norm = np.array([0.33, 0.33, 0.34])

    # Calcular ICE baseado na eficiência espectral
    # ICE será proporcional ao PPFD do espectro de referência nas faixas dos LEDs
    ppfd_ref_total = pfd_ref['PPFD']

    # Calcular eficiência de cada LED para o espectro de referência
    # Usar a correlação entre os espectros
    eficiencia_v = np.correlate(led_vermelho, espectro_ref_valores)[
        0] if len(led_vermelho) > 0 else 0
    eficiencia_a = np.correlate(led_azul, espectro_ref_valores)[
        0] if len(led_azul) > 0 else 0
    eficiencia_b = np.correlate(led_branco, espectro_ref_valores)[
        0] if len(led_branco) > 0 else 0

    # Normalizar eficiências
    eficiencias = np.array([eficiencia_v, eficiencia_a, eficiencia_b])
    if eficiencias.sum() > 0:
        eficiencias_norm = eficiencias / eficiencias.sum()
    else:
        eficiencias_norm = np.array([0.33, 0.33, 0.34])

    # Calcular ICE para cada canal (fixo durante o dia)
    # Baseado na intensidade máxima e eficiência espectral
    ice_base = intensidade_min_total + \
        (intensidade_max_total - intensidade_min_total) * 0.7

    ice_lamp_ch1 = ice_base * \
        proporcoes_norm[0] * eficiencias_norm[0] * \
        proporcoes_lamp['LAMP_CH1_Vermelho']
    ice_lamp_ch2 = ice_base * \
        proporcoes_norm[1] * eficiencias_norm[1] * \
        proporcoes_lamp['LAMP_CH2_Azul']
    ice_lamp_ch3 = ice_base * \
        proporcoes_norm[2] * eficiencias_norm[2] * \
        proporcoes_lamp['LAMP_CH3_Branco']

    # Arredondar para inteiros (como no padrão LAMP)
    ice_lamp_ch1_int = int(round(ice_lamp_ch1))
    ice_lamp_ch2_int = int(round(ice_lamp_ch2))
    ice_lamp_ch3_int = int(round(ice_lamp_ch3))

    # Obter horários do sistema
    hora_inicio = st.session_state.parametros_temporais['hora_inicio']
    hora_fim = st.session_state.parametros_temporais['hora_fim']

    # Gerar conteúdo LAMP_ para cada canal (formato HH MM SS ICE)
    conteudo_lamp_ch1 = f"{hora_inicio:02d} 00 00 {ice_lamp_ch1_int}\n{hora_fim:02d} 00 00 {ice_lamp_ch1_int}\n"
    conteudo_lamp_ch2 = f"{hora_inicio:02d} 00 00 {ice_lamp_ch2_int}\n{hora_fim:02d} 00 00 {ice_lamp_ch2_int}\n"
    conteudo_lamp_ch3 = f"{hora_inicio:02d} 00 00 {ice_lamp_ch3_int}\n{hora_fim:02d} 00 00 {ice_lamp_ch3_int}\n"

    # ============================================================================
    # GRAFICOS ESPECTRAIS
    # ============================================================================

    # Gráfico 1: Espectros comparados
    col1, col2 = st.columns([1, 1])

    # placeholders para evitar remounts visíveis durante reruns
    ph_leds = col1.empty()
    ph_lamp = col2.empty()

    with ph_leds:
        # Gráfico comparativo de LEDs
        options_leds = {
            "color": [COLORS['vermelho'], COLORS['azul'], COLORS['branco'], COLORS['referencia']],
            "title": {
                "text": "Espectros dos LEDs da Bancada",
                "subtext": "Espectros normalizados para comparação",
                "left": "center",
                "padding": [0, 0, 0, 0]
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"}
            },
            "legend": {
                "data": ["LED Vermelho", "LED Azul", "LED Branco", espectro_ref],
                "top": "10%",
                "type": "scroll",
                "padding": [50, 0, 0, 0],
                "itemGap": 5,
                "itemWidth": 25,
                "itemHeight": 14
            },
            "xAxis": {
                "name": "Comprimento de onda (nm)",
                "nameLocation": "middle",
                "nameGap": 25,
                "type": "value",
                "min": faixa_min,
                "max": faixa_max
            },
            "yAxis": {
                "name": "Intensidade Normalizada",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value"
            },
            "series": [
                {
                    "name": "LED Vermelho",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, viz_led_vermelho)],
                    "markPoint": mark_v,
                    "smooth": True,
                    "lineStyle": {"color": COLORS['vermelho'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0,
                                    "color": COLORS['vermelho'] + "40"},
                                {"offset": 1,
                                    "color": COLORS['vermelho'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": "LED Azul",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, viz_led_azul)],
                    "markPoint": mark_a,
                    "smooth": True,
                    "lineStyle": {"color": COLORS['azul'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": COLORS['azul'] + "40"},
                                {"offset": 1, "color": COLORS['azul'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": "LED Branco",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, viz_led_branco)],
                    "markPoint": mark_b,
                    "smooth": True,
                    "lineStyle": {"color": COLORS['branco'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0,
                                    "color": COLORS['branco'] + "40"},
                                {"offset": 1, "color": COLORS['branco'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": espectro_ref,
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, espectro_ref_valores)],
                    "markPoint": mark_ref,
                    "smooth": True,
                    "lineStyle": {
                        "color": COLORS['referencia'],
                        "width": 1,
                        "type": "dashed"
                    },
                    "showSymbol": False
                },
            ],
            "dataZoom": [
                {"type": "inside", "xAxisIndex": 0},
                {
                    "show": True,
                    "xAxisIndex": 0,
                    "type": "slider",
                    "bottom": 10,
                    "height": 20,
                    "borderColor": "transparent",
                    "handleStyle": {"color": COLORS['vermelho']},
                    "fillerColor": "rgba(84, 112, 198, 0.1)",
                    "textStyle": {"color": "#666"}
                }
            ],
            "grid": {
                "left": "30px",
                "right": "40px",
                "bottom": "60px",
                "top": "110px",
                "containLabel": True
            }
        }
        st_echarts(options=apply_base_config(options_leds),
                   height=350, key="espectros_leds")

    with ph_lamp:
        # Gráfico dos espectros LAMP_CH
        options_lamp_espectros = {
            "color": [COLORS['vermelho'], COLORS['azul'], COLORS['branco'], COLORS['soma'], COLORS['referencia']],
            "title": {
                "text": "Espectros LAMP_CH Otimizados",
                "subtext": f"Proporções: CH1={proporcoes_lamp['LAMP_CH1_Vermelho']:.2f}, CH2={proporcoes_lamp['LAMP_CH2_Azul']:.2f}, CH3={proporcoes_lamp['LAMP_CH3_Branco']:.2f}",
                "left": "center",
                "padding": [0, 0, 0, 0]
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"}
            },
            "legend": {
                "data": ["LAMP_CH1 (Vermelho)", "LAMP_CH2 (Azul)",
                         "LAMP_CH3 (Branco)", "Soma Total", espectro_ref],
                "type": "scroll",
                "top": "10%",
                "padding": [50, 0, 0, 0],
                "itemGap": 5,
                "itemWidth": 25,
                "itemHeight": 14
            },
            "xAxis": {
                "name": "Comprimento de onda (nm)",
                "nameLocation": "middle",
                "nameGap": 25,
                "type": "value",
                "min": faixa_min,
                "max": faixa_max
            },
            "yAxis": {
                "name": "Intensidade",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value"
            },
            "series": [
                {
                    "name": "LAMP_CH1 (Vermelho)",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, lamp_ch1)],
                    "smooth": True,
                    "lineStyle": {"color": COLORS['vermelho'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0,
                                    "color": COLORS['vermelho'] + "40"},
                                {"offset": 1,
                                    "color": COLORS['vermelho'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": "LAMP_CH2 (Azul)",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, lamp_ch2)],
                    "smooth": True,
                    "lineStyle": {"color": COLORS['azul'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": COLORS['azul'] + "40"},
                                {"offset": 1, "color": COLORS['azul'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": "LAMP_CH3 (Branco)",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, lamp_ch3)],
                    "smooth": True,
                    "lineStyle": {"color": COLORS['branco'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0,
                                    "color": COLORS['branco'] + "40"},
                                {"offset": 1,
                                    "color": COLORS['branco'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": "Soma Total",
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, lamp_soma)],
                    "smooth": True,
                    "lineStyle": {"color": COLORS['soma'], "width": 2},
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0,
                                    "color": COLORS['soma'] + "40"},
                                {"offset": 1,
                                    "color": COLORS['soma'] + "05"}
                            ]
                        }
                    },
                    "showSymbol": False
                },
                {
                    "name": espectro_ref,
                    "type": "line",
                    "data": [[float(round(wl, 4)), float(round(val, 4))] for wl, val in zip(wavelengths, espectro_ref_valores)],
                    "smooth": True,
                    "lineStyle": {"color": COLORS['referencia'], "width": 1, "type": "dashed"},
                    "showSymbol": False
                }
            ],
            "dataZoom": [
                {"type": "inside", "xAxisIndex": 0},
                {
                    "show": True,
                    "xAxisIndex": 0,
                    "type": "slider",
                    "bottom": 10,
                    "height": 20,
                    "borderColor": "transparent",
                    "handleStyle": {"color": COLORS['vermelho']},
                    "fillerColor": "rgba(84, 112, 198, 0.1)",
                    "textStyle": {"color": "#666"}
                }
            ],
            "grid": {
                "left": "30px",
                "right": "40px",
                "bottom": "60px",
                "top": "80px",
                "containLabel": True
            }
        }
        st_echarts(options=apply_base_config(
            options_lamp_espectros), height=350, key="espectros_lamp")

    # ============================================================================
    # GRÁFICO E TABELA DE ICE FIXO
    # ============================================================================

    col_ice1, col_ice2 = st.columns([1, 1])

    ph_ice = col_ice2.empty()

    with col_ice1:
        # Tabela com valores de ICE
        st.markdown("**📊 Valores de ICE Fixos**")

        df_ice_fixo = pd.DataFrame({
            'Canal': ['LAMP_CH1 (Vermelho)', 'LAMP_CH1 (Vermelho)',
                      'LAMP_CH2 (Azul)', 'LAMP_CH2 (Azul)',
                      'LAMP_CH3 (Branco)', 'LAMP_CH3 (Branco)'],
            'ICE (μmol/m²/s)': [ice_lamp_ch1_int, ice_lamp_ch1_int,
                                ice_lamp_ch2_int,  ice_lamp_ch2_int,
                                ice_lamp_ch3_int, ice_lamp_ch3_int],
            'Proporção': [
                f"{proporcoes_lamp['LAMP_CH1_Vermelho']:.3f}",
                f"{proporcoes_lamp['LAMP_CH1_Vermelho']:.3f}",
                f"{proporcoes_lamp['LAMP_CH2_Azul']:.3f}",
                f"{proporcoes_lamp['LAMP_CH2_Azul']:.3f}",
                f"{proporcoes_lamp['LAMP_CH3_Branco']:.3f}",
                f"{proporcoes_lamp['LAMP_CH3_Branco']:.3f}"
            ],
            'Hora': [
                f"{hora_inicio:02d} 00 00 {ice_lamp_ch1_int}",
                f"{hora_fim:02d} 00 00 {ice_lamp_ch1_int}",
                f"{hora_inicio:02d} 00 00 {ice_lamp_ch2_int}",
                f"{hora_fim:02d} 00 00 {ice_lamp_ch2_int}",
                f"{hora_inicio:02d} 00 00 {ice_lamp_ch3_int}",
                f"{hora_fim:02d} 00 00 {ice_lamp_ch3_int}"
            ]
        })

        st.dataframe(df_ice_fixo, use_container_width=True, hide_index=True)

    with ph_ice:
        # Gráfico de barras mostrando ICE fixo por canal
        # Preparar dados para o gráfico
        data_barras_ice = [
            {"value": ice_lamp_ch1_int, "itemStyle": {
                "color": COLORS['vermelho']}},
            {"value": ice_lamp_ch2_int, "itemStyle": {
                "color": COLORS['azul']}},
            {"value": ice_lamp_ch3_int, "itemStyle": {
                "color": COLORS['branco']}}
        ]

        options_ice_fixo = {
            "title": {
                "text": "ICE Fixo por Canal LAMP",
                "subtext": f"Valores constantes durante {hora_inicio:02d}:00-{hora_fim:02d}:00",
                "left": "center"
            },
            "tooltip": {
                "trigger": "axis",
                "formatter": "{b}: {c} μmol/m²/s"
            },
            "xAxis": {
                "type": "category",
                "data": ["LAMP_CH1", "LAMP_CH2", "LAMP_CH3"],
                "axisLabel": {
                    "rotate": 0,
                    "interval": 0
                }
            },
            "yAxis": {
                "name": "ICE (μmol/m²/s)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": 0
            },
            "series": [{
                "name": "ICE Fixo",
                "type": "bar",
                "data": data_barras_ice,
                "barWidth": "60%",
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0],
                    "borderColor": "#fff",
                    "borderWidth": 1
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "fontSize": 12,
                    "fontWeight": "bold"
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)"
                    }
                }
            }],
            "grid": {
                "left": "60px",
                "right": "40px",
                "bottom": "10px",
                "top": "60",
                "containLabel": True
            }
        }

        with ph_ice:
            st_echarts(options=apply_base_config(
                options_ice_fixo), height=300, key="ice_fixo")

    # Resultados numéricos e tabelas
    col_res1, col_res2, col_res3 = st.columns(3)

    with col_res1:
        st.markdown("**📈 PROPORÇÕES LAMP ÓTIMAS**")
        df_proporcoes = pd.DataFrame([
            {"Canal": "LAMP_CH1 (Vermelho)",
                "Proporção": f"{proporcoes_lamp['LAMP_CH1_Vermelho']:.3f}"},
            {"Canal": "LAMP_CH2 (Azul)",
                "Proporção": f"{proporcoes_lamp['LAMP_CH2_Azul']:.3f}"},
            {"Canal": "LAMP_CH3 (Branco)",
                "Proporção": f"{proporcoes_lamp['LAMP_CH3_Branco']:.3f}"}
        ])
        st.dataframe(df_proporcoes, use_container_width=True,
                     hide_index=True)

        # Botões de download para arquivos LAMP_ individuais
        st.markdown("**📥 Download Arquivos LAMP**")

        col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])

        with col_dl1:
            st.download_button(
                label="CH1.txt",
                data=conteudo_lamp_ch1,
                file_name="LAMP_CH1.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_dl2:
            st.download_button(
                label="CH2.txt",
                data=conteudo_lamp_ch2,
                file_name="LAMP_CH2.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_dl3:
            st.download_button(
                label="CH3.txt",
                data=conteudo_lamp_ch3,
                file_name="LAMP_CH3.txt",
                mime="text/plain",
                use_container_width=True
            )

    with col_res2:
        st.markdown("**🔬 PFDs DO ESPECTRO DE REFERÊNCIA**")
        df_pfd_ref = pd.DataFrame([
            {"Banda": "PPFD (400-700nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['PPFD']:.1f}"},
            {"Banda": "BLUE (400-500nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['BLUE']:.1f}"},
            {"Banda": "GREEN (500-600nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['GREEN']:.1f}"},
            {"Banda": "RED (600-700nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['RED']:.1f}"},
            {"Banda": "FAR RED (700-780nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['FAR_RED']:.1f}"},
            {"Banda": "UV (380-400nm)",
                "Valor (μmol/m²/s)": f"{pfd_ref['UV']:.1f}"}
        ])
        st.dataframe(df_pfd_ref, use_container_width=True, hide_index=True)

    with col_res3:
        st.markdown("**⚡ PFDs DA SOMA LAMP**")
        df_pfd_lamp = pd.DataFrame([
            {"Banda": "PPFD (400-700nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['PPFD']:.1f}"},
            {"Banda": "BLUE (400-500nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['BLUE']:.1f}"},
            {"Banda": "GREEN (500-600nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['GREEN']:.1f}"},
            {"Banda": "RED (600-700nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['RED']:.1f}"},
            {"Banda": "FAR RED (700-780nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['FAR_RED']:.1f}"},
            {"Banda": "UV (380-400nm)",
                "Valor (μmol/m²/s)": f"{pfd_lamp_soma['UV']:.1f}"}
        ])
        st.dataframe(df_pfd_lamp, use_container_width=True,
                     hide_index=True)


# ============================================================================
# ROTEAMENTO DAS ABAS (ATUALIZADO)
# ============================================================================


if aba_selecionada == "📊 Visão Geral":
    exibir_visao_geral()
elif aba_selecionada == "🧪 Calibração Bancada":
    exibir_calibracao_bancada()
elif aba_selecionada == "🎛️ Configurar Canais":
    exibir_configurar_canais()
elif aba_selecionada == "༗ Espectros":
    exibir_simular_espectro()
