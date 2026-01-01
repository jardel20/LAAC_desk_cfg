import pandas as pd
import numpy as np
import streamlit as st
import io
from scipy import stats
from scipy.interpolate import interp1d
from streamlit_echarts import st_echarts

# Configurar página
st.set_page_config(
    page_title="Sistema de Calibração de Bancadas LAAC - Spectral Int",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


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
                'valores_previstos_media': valores_previstos_media
            }

    def calcular_gaussiana(self, x, sigma, mi, intensidade_max, intensidade_min):
        """Calcula a distribuição gaussiana"""
        return intensidade_min + (intensidade_max - intensidade_min) * np.exp(-((x - mi)**2) / (2 * sigma**2))

    def gerar_dados_canal(self, canal, sigma, mi):
        """Gera dados para um canal específico"""
        params = st.session_state.parametros_canais
        tempo = st.session_state.parametros_temporais

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

        n_pontos = tempo['n_pontos']
        x_vals = np.linspace(-1, 1, n_pontos)
        horas_decimais = np.linspace(
            tempo['hora_inicio'], tempo['hora_fim'], n_pontos)

        intensidades = self.calcular_gaussiana(
            x_vals, sigma, mi, intensidade_max, intensidade_min)

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
            'intensidade_min': intensidade_min
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
    'axis': '#7b7b7b'
}

# Configurações de tema padrão
BASE_OPTIONS = {
    "animation": True,
    "animationDuration": 1000,
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

    options["toolbox"] = {
        "feature": {
            "dataZoom": {
                "yAxisIndex": "none"
            },
            "restore": {},
            "saveAsImage": {
                "title": "Salvar imagem",
                "pixelRatio": 2
            }
        },
        "right": 20,
        "top": 20
    }

    return {**BASE_OPTIONS, **options}


def criar_grafico_regressao(canal_nome, reg, x_ref, y_medido, y_previsto, cor):
    """Cria gráfico de regressão linear PROFISSIONAL"""

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

    # Preparar dados suavizados
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

    # Calcular soma com horas comuns
    horas_min = max(min(horas_v), min(horas_a), min(horas_b))
    horas_max = min(max(horas_v), max(horas_a), max(horas_b))
    horas_comuns = np.linspace(horas_min, horas_max, 200)

    # Interpolar para soma
    intens_v_interp = np.interp(horas_comuns, horas_v, intens_v)
    intens_a_interp = np.interp(horas_comuns, horas_a, intens_a)
    intens_b_interp = np.interp(horas_comuns, horas_b, intens_b)
    soma_intensidades = intens_v_interp + intens_a_interp + intens_b_interp

    # DADOS PREPARADOS FORA do options (CRÍTICO)
    dados_vermelho = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['vermelho']}}
                      for h, i in zip(horas_v, intens_v)]
    dados_azul = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['azul']}}
                  for h, i in zip(horas_a, intens_a)]
    dados_branco = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['branco']}}
                    for h, i in zip(horas_b, intens_b)]
    dados_soma = [{"value": [float(h), float(round(i, 2))], "itemStyle": {"color": COLORS['soma']}}
                  for h, i in zip(horas_comuns, soma_intensidades)]

    options = {
        "color": [COLORS['vermelho'], COLORS['azul'], COLORS['branco'], COLORS['soma']],
        "title": {
            "text": "Comparação de Intensidades por Canal",
            "subtext": "Curvas suavizadas com interpolação cúbica",
            "left": "center",
            "padding": [40, 0, 0, 0]
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "top": "10%",
            "type": "scroll"
        },
        "xAxis": {
            "name": "Hora do Dia",
            "nameLocation": "middle",
            "nameGap": 25,
            "nameTextStyle": {"fontSize": 14, "fontWeight": "bold"},
            "type": "value",
            "min": horas_min - 0.2,
            "max": horas_max + 0.2,
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
                "data": dados_vermelho,
                "smooth": True,
                "lineStyle": {"color": COLORS['vermelho'], "width": 2.5},
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
                "emphasis": {"focus": "series"}
            },
            {
                "name": "Azul",
                "type": "line",
                "data": dados_azul,
                "smooth": True,
                "lineStyle": {"color": COLORS['azul'], "width": 2.5},
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
                "emphasis": {"focus": "series"}
            },
            {
                "name": "Branco",
                "type": "line",
                "data": dados_branco,
                "smooth": True,
                "lineStyle": {"color": COLORS['branco'], "width": 2.5},
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
                "emphasis": {"focus": "series"}
            },
            {
                "name": "Soma Total",
                "type": "line",
                "data": dados_soma,
                "smooth": True,
                "lineStyle": {"color": COLORS['soma'], "width": 3.5, "type": "dashed"},
                "showSymbol": False,
                "emphasis": {"focus": "series"}
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
                "fillerColor": "rgba(84, 112, 198, 0.1)"
            }
        ],
        "grid": {
            "left": "5%",
            "right": "5%",
            "bottom": "12%",
            "top": 100,
            "containLabel": True
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
    """Cria gráfico detalhado de um canal"""
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

    options = {
        "title": {
            "text": f"Intensidade - Canal {canal_nome.capitalize()}",
            "subtext": f"σ={params_gauss['sigma']:.2f}, μ={params_gauss['mi']:.2f} | Máx: {dados['intensidade_max']:.1f}, Mín: {dados['intensidade_min']:.1f} μmol/m²/s"
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
                            "name": "Máximo",
                            "lineStyle": {
                                "color": cor,
                                "type": "dashed",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Máx: {c}",
                                "position": "middle"
                            }
                        },
                        {
                            "yAxis": round(dados['intensidade_min'], 2),
                            "name": "Mínimo",
                            "lineStyle": {
                                "color": cor,
                                "type": "dashed",
                                "width": 1
                            },
                            "label": {
                                "formatter": "Mín: {c}",
                                "position": "middle"
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

    options = {
        "title": {
            "text": f"Integral Acumulada (DLI) - Canal {canal_nome.capitalize()}",
            "subtext": f"DLI final: {dados['DLI_final']:.3f} mol/m² | ICE: {dados['ICE']:.1f} μmol/m²/s"
        },
        "tooltip": {},
        "xAxis": {
            "name": "Hora do Dia",
            "nameLocation": "middle",
            "nameGap": 25,
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
            "min": min(-1.1, min(x_suave)*0.95),
            "max": max(1.1, max(x_suave)*1.05),
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": COLORS['grid']}}
        },
        "yAxis": {
            "name": "Intensidade (μmol/m²/s)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "min": 0,
            "max": y_max * 1.15,
            "axisLabel": {"formatter": "{value}"}
        },
        "series": [
            {
                "name": "Distribuição Gaussiana",
                "type": "line",
                "data": [[float(x), float(y)] for x, y in zip(x_suave, intens_suave)],
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
                "data": [[float(x), float(y)] for x, y in zip(area_x, area_y)],
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
                    {"value": intensidades_min[0], "itemStyle": {
                        "color": COLORS['azul'] + "80"}},
                    {"value": intensidades_min[1], "itemStyle": {
                        "color": COLORS['vermelho'] + "80"}},
                    {"value": intensidades_min[2], "itemStyle": {
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
        - Legenda:
            - LAMP_CH1.txt - Canal Vermelho
            - LAMP_CH2.txt - Canal Azul  
            - LAMP_CH3.txt - Canal Branco
            - LAMP_CH4.txt - Cópia do Branco (mesmo conteúdo de LAMP_CH3.txt)
        - Gerar arquivos LAMP gera arquivos de configuração LAMP, cada arquivo contém horários e intensidades calculadas para cada canal de LED
    
    3. **Atenção às proporções:**
       - A proporção escolhida é entre canais físicos de LEDs
       - **NÃO** é de banda espectral
    """)

st.markdown("---")

# Barra lateral
with st.sidebar:
    st.header("📜 Navegação")

    aba_selecionada = st.radio(
        "Selecione a seção:",
        ["📊 Visão Geral",
         "🧪 Calibração Bancada",
         "🔄 Configurar Canais"],
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

        # Seção para gerar arquivos LAMP
        st.markdown("---")
        st.header("💡 Gerar Arquivos LAMP")

        with st.expander("📄 Arquivos", expanded=False):

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

            # ... (código anterior na barra lateral)

            col1, col2 = st.columns(2)

            with col1:
                # Botão para gerar arquivo individual
                if st.button("⚡ Único", use_container_width=True):
                    # Obter dados do canal
                    dados = sistema.get_dados_canal(canal_nome)
                    params_temp = st.session_state.parametros_temporais

                    # Criar conteúdo do arquivo usando o método do sistema
                    conteudo_arquivo = sistema.gerar_conteudo_lamp(
                        dados, params_temp)

                    # Nome do arquivo baseado na seleção
                    nome_arquivo = arquivo_selecionado.split(" ")[0]

                    # Criar download
                    st.download_button(
                        label=f"⬇️ Baixar (TXT)",
                        data=conteudo_arquivo,
                        file_name=nome_arquivo,
                        mime="text/plain",
                        use_container_width=True,
                        key=f"download_{nome_arquivo}"
                    )

            with col2:
                # Botão para gerar todos os arquivos
                if st.button("📦 Todos", use_container_width=True):
                    # Criar arquivo ZIP com todos os 4 arquivos
                    import zipfile
                    import io

                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Gerar cada um dos 4 arquivos
                        arquivos_para_gerar = [
                            ("LAMP_CH1.txt", "vermelho"),
                            ("LAMP_CH2.txt", "azul"),
                            ("LAMP_CH3.txt", "branco"),
                            ("LAMP_CH4.txt", "branco")  # Usa dados do branco
                        ]

                        for nome_arquivo, canal in arquivos_para_gerar:
                            dados = sistema.get_dados_canal(canal)
                            params_temp = st.session_state.parametros_temporais
                            # Usar o método do sistema
                            conteudo = sistema.gerar_conteudo_lamp(
                                dados, params_temp)
                            zip_file.writestr(nome_arquivo, conteudo)

                        # Adicionar um arquivo README
                        readme_content = f"""
                        ARQUIVOS DE CONFIGURAÇÃO LAMP
                        Gerado em: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                        
                        Conteúdo:
                        1. LAMP_CH1.txt - Canal Vermelho
                        2. LAMP_CH2.txt - Canal Azul  
                        3. LAMP_CH3.txt - Canal Branco
                        4. LAMP_CH4.txt - Cópia do Branco (mesmo conteúdo de LAMP_CH3.txt)
                        
                        Configurações utilizadas:
                        - Intensidade Total Máxima: {st.session_state.parametros_canais['intensidade_max_total']} μmol/m²/s
                        - Intensidade Total Mínima: {st.session_state.parametros_canais['intensidade_min_total']} μmol/m²/s
                        - Fotoperíodo: {st.session_state.parametros_temporais['hora_inicio']}:00 às {st.session_state.parametros_temporais['hora_fim']}:00
                        - Número de pontos: {st.session_state.parametros_temporais['n_pontos']}
                        
                        Formato dos arquivos:
                        HH MM SS INTENSIDADE
                        """
                        zip_file.writestr("README.txt", readme_content)

                    buffer.seek(0)

                    # Criar download do ZIP
                    st.download_button(
                        label="📥 Baixar (ZIP)",
                        data=buffer,
                        file_name="lamp_config_files.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_all_zip"
                    )

            # Mostrar preview do arquivo selecionado
            if st.button("👁️ Preview", use_container_width=True):
                dados = sistema.get_dados_canal(canal_nome)
                params_temp = st.session_state.parametros_temporais
                # Usar o método do sistema
                conteudo_arquivo = sistema.gerar_conteudo_lamp(
                    dados, params_temp)
                st.code(conteudo_arquivo, language="text")

# ============================================================================
# FUNÇÕES PARA CADA ABA
# ============================================================================


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

    st.markdown("---")

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
            st_echarts(options=options, height=400, key=f"reg_{canal_nome}")

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

    st.markdown("---")

    # Gráficos Comparativos
    st.header("📈 Comparação entre Canais")

    # Gráfico 1: Intensidades comparadas com soma
    st.subheader("⚡ Intensidade dos Canais")

    options_intensidades = criar_grafico_comparacao_intensidades(
        dados_vermelho, dados_azul, dados_branco)
    st_echarts(options=options_intensidades, height=500,
               key="comparacao_intensidades")

    # Gráfico 2: DLIs finais comparados
    st.subheader("📊 Métricas de Luz por Canal")

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

    col1, col2 = st.columns(2)

    with col1:
        options_dli = criar_grafico_barras_dli(dli_data)
        st_echarts(options=options_dli, height=400, key="barras_dli")

    with col2:
        options_ice = criar_grafico_barras_ice(dli_data)
        st_echarts(options=options_ice, height=400, key="barras_ice")


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

    # Interface de entrada de dados
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Valores de Referência:**")
        ref_vals = dados_canal['valores_referencia']

        grid_container = st.container()
        with grid_container:
            cols = st.columns(6)
            with cols[0]:
                st.markdown("**Repetição**")
            for i in range(5):
                with cols[i+1]:
                    st.markdown(
                        f"**Intensidade {i+1}**<br>(Ref: {ref_vals[i]})", unsafe_allow_html=True)

            for rep in range(5):
                cols = st.columns(6)
                with cols[0]:
                    st.markdown(f"**Repetição {rep+1}**")
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
                            label_visibility="collapsed"
                        )
                        if valor != dados_canal['dados'][rep, intens]:
                            dados_canal['dados'][rep, intens] = valor
                            sistema.calcular_regressoes()

    with col2:
        st.subheader("📊 Estatísticas")
        reg = sistema.regressoes[canal_key]['regressao_media']
        medias = sistema.regressoes[canal_key]['medias']

        st.metric("Média Máxima", f"{max(medias):.2f}")
        st.metric("Média Mínima", f"{min(medias):.2f}")
        st.metric("Coef. Angular (a)", f"{reg['a']:.4f}")
        st.metric("Coef. Linear (b)", f"{reg['b']:.4f}")
        st.metric("R²", f"{reg['r2']:.4f}")

        if st.button("🔄 Restaurar Valores Padrão", key="reset_button"):
            # Restaurar valores padrão
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
            else:
                default_data = np.array([
                    [20.61, 24.51, 24.24, 22.42, 23.14],
                    [62.13, 67.69, 58.93, 59.12, 55.09],
                    [69.18, 92.19, 91.02, 86.68, 84.73],
                    [109.8, 104.6, 117.0, 113.7, 110.3],
                    [120.8, 150.9, 143.3, 130.7, 143.9]
                ]).T

            st.session_state.dados_bancada[canal_key]['dados'] = default_data
            sistema.calcular_regressoes()
            st.success(
                f"Valores padrão restaurados para o canal {canal_selecionado}!")
            st.rerun()

    # Visualização gráfica
    st.subheader("📈 Visualização em Tempo Real")

    # Criar gráfico ECharts para regressão
    reg = sistema.regressoes[canal_key]
    x_ref = st.session_state.dados_bancada[canal_key]['valores_referencia']

    # Preparar dados para o gráfico
    series_data = []

    # Adicionar repetições
    for rep in range(5):
        series_data.append({
            "name": f'Repetição {rep+1}',
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
        "data": [[float(x_ref[i]), float(medias[i])] for i in range(5)],
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
            "data": [f'Repetição {i+1}' for i in range(5)] + ['Média', 'Regressão (média)'],
            "top": "10%",
            "type": "scroll"
        },
        "xAxis": {
            "name": "Valor de Referência",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": -0.1,
            "max": 1.1
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

    st_echarts(options=options, height=500, key="calibracao_grafico")


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
        cor = COLORS['vermelho'] if canal_nome == 'vermelho' else COLORS['azul'] if canal_nome == 'azul' else COLORS['branco']
        options_intensidade = criar_grafico_canal_detalhes(
            dados, canal_nome, cor, params_gauss)
        st_echarts(options=options_intensidade, height=400,
                   key=f"intensidade_{canal_nome}")

    with col2:
        # Gráfico da integral
        options_integral = criar_grafico_integral(dados, canal_nome, cor)
        st_echarts(options=options_integral, height=400,
                   key=f"integral_{canal_nome}")

    # Gráfico da distribuição gaussiana
    st.subheader(f"📊 Distribuição Gaussiana")
    options_gaussiana = criar_grafico_gaussiana(
        dados, canal_nome, cor, params_gauss['sigma'], params_gauss['mi'])
    st_echarts(options=options_gaussiana, height=400,
               key=f"gaussiana_{canal_nome}")


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
    st.subheader("📈 Comparação de Intensidades")

    intensidades_max = [intensidade_max_azul,
                        intensidade_max_vermelho, intensidade_max_branco]
    intensidades_min = [intensidade_min_azul,
                        intensidade_min_vermelho, intensidade_min_branco]

    options_barras = criar_grafico_comparacao_intensidades_barras(
        intensidades_max, intensidades_min)
    st_echarts(options=options_barras, height=400,
               key="comparacao_intensidades_barras")

    st.markdown("---")

    # Seletor para visualização detalhada do canal
    st.header("🔍 Visualização Detalhada por Canal")

    canal_selecionado = st.selectbox(
        "Selecione o canal para visualização detalhada:",
        ["Vermelho", "Azul", "Branco"],
        key="canal_detalhado"
    )

    # Mapear seleção para nomes internos
    canal_map = {
        "Vermelho": ("vermelho", "🔴", "Vermelho"),
        "Azul": ("azul", "🔵", "Azul"),
        "Branco": ("branco", "⚪", "Branco")
    }

    canal_nome, emoji, nome_display = canal_map[canal_selecionado]

    # Exibir detalhes do canal selecionado
    st.subheader(f"{emoji} Canal {nome_display} - Detalhes")

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
        cor = COLORS['vermelho'] if canal_nome == 'vermelho' else COLORS['azul'] if canal_nome == 'azul' else COLORS['branco']
        options_intensidade = criar_grafico_canal_detalhes(
            dados, canal_nome, cor, params_gauss)
        st_echarts(options=options_intensidade, height=400,
                   key=f"intensidade_{canal_nome}_config")

    with col2:
        # Gráfico da integral
        options_integral = criar_grafico_integral(dados, canal_nome, cor)
        st_echarts(options=options_integral, height=400,
                   key=f"integral_{canal_nome}_config")

    # Gráfico da distribuição gaussiana
    st.subheader(f"📊 Distribuição Gaussiana")
    options_gaussiana = criar_grafico_gaussiana(
        dados, canal_nome, cor, params_gauss['sigma'], params_gauss['mi'])
    st_echarts(options=options_gaussiana, height=400,
               key=f"gaussiana_{canal_nome}_config")

# ============================================================================
# ROTEAMENTO DAS ABAS (ATUALIZADO)
# ============================================================================


if aba_selecionada == "📊 Visão Geral":
    exibir_visao_geral()
elif aba_selecionada == "🧪 Calibração Bancada":
    exibir_calibracao_bancada()
elif aba_selecionada == "🔄 Configurar Canais":
    exibir_configurar_canais()
# Removi completamente as chamadas das abas individuais de canal

# Rodapé
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 0.9em;'>"
    "🖥️ Sistema de Calibração de Bancadas | Desenvolvido para LAAC | v1.0"
    "</div>",
    unsafe_allow_html=True
)
