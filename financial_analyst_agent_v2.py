"""
Institutional Financial & Counterparty Due Diligence Agent (v2.0)
Built with LangChain v1, Pydantic Data Contracts, and Deterministic Financial Tools.

Author: Steven — AI Systems Architect
Portfolio: ai-consultant-portfolio
"""

import json
import math
import os
from pydantic import BaseModel, Field
import yfinance as yf
from ddgs import DDGS
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool


# =====================================================================
# 1. TICKER AUTO-HEALING & HELPER UTILITIES
# =====================================================================
BMV_TICKER_MAP = {
    "BIMBO": "BIMBOA.MX",
    "GRUPO BIMBO": "BIMBOA.MX",
    "WALMART MEXICO": "WALMEX.MX",
    "WALMEX": "WALMEX.MX",
    "BANORTE": "GFNORTEO.MX",
    "CEMEX": "CEMEXCPO.MX",
    "FEMSA": "FEMSAUBD.MX",
    "AMERICA MOVIL": "AMXB.MX",
    "GRUPO MEXICO": "GMEXICOB.MX",
    "CHEDRAUI": "CHDRAUIB.MX",
    "SORIANA": "SORIANAB.MX",
    "SPACEX": "SPCX",
}


def normalizar_ticker(ticker: str) -> str:
    """Normalizes common Mexican BMV and US company names into valid Yahoo Finance tickers."""
    limpio = ticker.strip().upper()
    return BMV_TICKER_MAP.get(limpio, limpio)


# =====================================================================
# 2. DETERMINISTIC TOOL LAYER (5 SPECIALIZED TOOLS)
# =====================================================================
@tool
def obtener_fundamentales_bolsa(ticker: str) -> dict:
    """Obtiene fundamentales financieros en tiempo real de una empresa pública desde Yahoo Finance.
    Acepta tickers de EE.UU. ('NVDA', 'AAPL', 'WMT', 'SPCX') o de México ('WALMEX.MX', 'GFNORTEO.MX', 'BIMBOA.MX').
    Úsala SIEMPRE que analices una empresa pública."""
    ticker_real = normalizar_ticker(ticker)
    try:
        info = yf.Ticker(ticker_real).info
        precio = info.get("currentPrice") or info.get("regularMarketPrice")
        if not precio:
            return {
                "error": (
                    f"No se encontraron datos bursátiles para '{ticker_real}'. "
                    "Verifica si el ticker lleva '.MX' o si es una empresa privada que no cotiza en bolsa."
                )
            }
        return {
            "ticker_usado": ticker_real,
            "empresa": info.get("longName", ticker_real),
            "sector": info.get("sector", "N/A"),
            "moneda": info.get("currency", "USD"),
            "precio_actual": precio,
            "maximo_52_semanas": info.get("fiftyTwoWeekHigh"),
            "minimo_52_semanas": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_trailing": info.get("trailingPE", "N/A"),
            "pe_forward": info.get("forwardPE", "N/A"),
            "margen_neto_pct": round(info.get("profitMargins", 0) * 100, 2) if info.get("profitMargins") else "N/A",
            "roe_pct": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else "N/A",
            "deuda_a_capital": info.get("debtToEquity", "N/A"),
        }
    except Exception as e:
        return {"error": f"Fallo al consultar '{ticker_real}': {str(e)}"}


@tool
def comparar_competidores_sector(tickers_separados_por_coma: str) -> list:
    """Compara lado a lado los múltiplos de valuación (P/E, Margen Neto, ROE) de entre 2 y 4 empresas competidoras.
    Ejemplo de entrada: 'WALMEX.MX, CHDRAUIB.MX, WMT, COST'.
    Úsala cuando necesites comparar una empresa contra sus competidores directos."""
    lista_tickers = [normalizar_ticker(t) for t in tickers_separados_por_coma.split(",")[:4]]
    comparativa = []
    for t in lista_tickers:
        try:
            info = yf.Ticker(t).info
            comparativa.append({
                "ticker": t,
                "empresa": info.get("shortName", t),
                "moneda": info.get("currency", "N/A"),
                "pe_trailing": round(info["trailingPE"], 2) if info.get("trailingPE") else "N/A",
                "pe_forward": round(info["forwardPE"], 2) if info.get("forwardPE") else "N/A",
                "margen_neto_pct": round(info["profitMargins"] * 100, 2) if info.get("profitMargins") else "N/A",
                "roe_pct": round(info["returnOnEquity"] * 100, 2) if info.get("returnOnEquity") else "N/A",
            })
        except Exception as e:
            comparativa.append({"ticker": t, "error": str(e)})
    return comparativa


@tool
def tipo_cambio_usd_mxn_en_vivo(monto: float, direccion: str = "MXN_a_USD") -> dict:
    """Obtiene el tipo de cambio spot USD/MXN en tiempo real del mercado y convierte un monto entre pesos y dólares.
    Parámetro 'direccion' debe ser 'MXN_a_USD' o 'USD_a_MXN'."""
    try:
        tc = yf.Ticker("MXN=X").fast_info["last_price"]
        tc = round(float(tc), 4)
        if direccion.upper() == "USD_A_MXN":
            convertido = round(monto * tc, 2)
            moneda_destino = "MXN"
        else:
            convertido = round(monto / tc, 2)
            moneda_destino = "USD"
        return {
            "tipo_cambio_spot_usd_mxn": tc,
            "monto_original": monto,
            "monto_convertido": convertido,
            "moneda_destino": moneda_destino,
        }
    except Exception as e:
        return {"error": f"No se pudo obtener el tipo de cambio en vivo: {str(e)}"}


@tool
def calculadora_financiera(expresion_matematica: str) -> str:
    """Ejecuta cálculos matemáticos y financieros exactos en Python.
    Úsala SIEMPRE que necesites sumar, restar, multiplicar, dividir, calcular porcentajes,
    tasas de crecimiento, márgenes, IVA, ISR o múltiplos financieros. Nunca calcules mentalmente."""
    try:
        allowed_names = {"round": round, "abs": abs, "pow": pow, "sqrt": math.sqrt}
        resultado = eval(expresion_matematica, {"__builtins__": {}}, allowed_names)
        return f"Resultado exacto: {resultado:,.4f}"
    except Exception as e:
        return f"Error en la expresión matemática '{expresion_matematica}': {str(e)}"


@tool
def busqueda_web_tiempo_real(consulta: str) -> str:
    """Busca noticias actuales, datos macroeconómicos o eventos recientes de empresas en internet en tiempo real.
    Úsala MÁXIMO UNA VEZ por empresa cuando necesites información reciente."""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=4))
            if not resultados:
                return "No se encontraron resultados en la web."
            bloques = [
                f"Título: {r.get('title')}\nFuente: {r.get('href')}\nResumen: {r.get('body')}"
                for r in resultados
            ]
            return "\n\n".join(bloques)
    except Exception as e:
        return f"Error al buscar en la web: {str(e)}"


# =====================================================================
# 3. PYDANTIC DATA CONTRACT (STRICT OUTPUT VALIDATION)
# =====================================================================
class DictamenComiteInversion(BaseModel):
    empresa: str = Field(description="Nombre oficial completo de la empresa analizada")
    ticker: str = Field(description="Símbolo bursátil utilizado (ej. WALMEX.MX)")
    precio_actual_moneda: str = Field(description="Precio actual con su código de moneda (ej. '$50.34 MXN')")
    descuento_max_52s_pct: float = Field(
        description="Porcentaje exacto de cambio respecto al máximo de 52 semanas calculado con Python (ej. -21.31)"
    )
    pe_trailing: float = Field(description="Múltiplo P/E Trailing actual de la empresa")
    roe_pct: float = Field(description="Return on Equity (ROE) en porcentaje")
    valor_mercado_usd_billones: float = Field(
        description="Market Cap convertido a miles de millones de USD (Billions USD)"
    )
    comparativa_competidores: list[str] = Field(
        description="Lista de 2 a 3 viñetas comparando sus múltiplos contra competidores directos"
    )
    catalizadores_recientes: list[str] = Field(
        description="Lista de 3 noticias o catalizadores estratégicos recientes obtenidos de la web"
    )
    semaforo_comite: str = Field(
        description="Uno de: '🟢 VERDE - SÓLIDA', '🟡 AMARILLO - CAUTELA', o '🔴 ROJO - RIESGO ALTO'"
    )
    tesis_ejecutiva: str = Field(description="Veredicto cuantitativo del CFO en 3 líneas directas, sin relleno")


# =====================================================================
# 4. AGENT ORCHESTRATOR & REPORT RENDERER
# =====================================================================
SYSTEM_PROMPT_V2 = """Eres el Managing Director del Comité de Inversiones de un fondo institucional en México.
Para analizar la empresa solicitada, ejecuta tus herramientas con eficiencia:
1. Usa `obtener_fundamentales_bolsa` para la empresa principal.
2. Si la empresa cotiza en MXN, usa `tipo_cambio_usd_mxn_en_vivo` para convertir su Market Cap a USD.
3. Usa `calculadora_financiera` para calcular el descuento exacto frente al máximo de 52 semanas y el Market Cap en Billions USD.
4. Usa `comparar_competidores_sector` UNA sola vez con 2 competidores relevantes del mismo sector.
5. Usa `busqueda_web_tiempo_real` UNA sola vez para catalizadores recientes.
Finalmente, entrega tu dictamen llenando estrictamente el esquema estructurado `DictamenComiteInversion`."""


def build_financial_agent(model_name: str = "google_genai:gemini-2.5-flash-lite"):
    """Builds and returns the configured LangChain v1 Financial Analyst Agent."""
    return create_agent(
        model=model_name,
        tools=[
            obtener_fundamentales_bolsa,
            comparar_competidores_sector,
            tipo_cambio_usd_mxn_en_vivo,
            calculadora_financiera,
            busqueda_web_tiempo_real,
        ],
        system_prompt=SYSTEM_PROMPT_V2,
        response_format=ToolStrategy(DictamenComiteInversion),
    )


def imprimir_dictamen_ejecutivo(dictamen: DictamenComiteInversion) -> None:
    """Renders the validated Pydantic object into an executive tear-sheet."""
    print("\n" + "═" * 75)
    print(f"🏛️ DICTAMEN DE COMITÉ DE INVERSIÓN: {dictamen.empresa.upper()} ({dictamen.ticker})")
    print("═" * 75)
    print(f"📌 Semáforo Ejecutivo : {dictamen.semaforo_comite}")
    print(f"💵 Precio Actual      : {dictamen.precio_actual_moneda} ({dictamen.descuento_max_52s_pct}% vs Máx 52s)")
    print(f"🌎 Market Cap (USD)   : ${dictamen.valor_mercado_usd_billones:,.2f} Billions USD")
    print(f"📊 Múltiplos Clave    : P/E Trailing {dictamen.pe_trailing}x | ROE {dictamen.roe_pct}%")
    print("-" * 75)
    print("⚖️ COMPARATIVA CONTRA COMPETIDORES DIRECTOS:")
    for comp in dictamen.comparativa_competidores:
        print(f"   • {comp}")
    print("-" * 75)
    print("📰 CATALIZADORES Y RIESGOS RECIENTES (LIVE WEB):")
    for cat in dictamen.catalizadores_recientes:
        print(f"   • {cat}")
    print("-" * 75)
    print(f"🧠 TESIS DEL COMITÉ:\n{dictamen.tesis_ejecutiva}")
    print("═" * 75)


if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        raise EnvironmentError("Por favor configura la variable de entorno GOOGLE_API_KEY antes de ejecutar.")

    agent = build_financial_agent()
    resultado = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Analiza Walmart de México (WALMEX) y compárala contra Chedraui (CHEDRAUI) y Walmart US (WMT).",
        }]
    })
    dictamen_validado: DictamenComiteInversion = resultado["structured_response"]
    print(json.dumps(dictamen_validado.model_dump(), indent=2, ensure_ascii=False))
    imprimir_dictamen_ejecutivo(dictamen_validado)
