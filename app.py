from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
import numpy_financial as npf

st.set_page_config(page_title="Simulador Imobiliário", layout="wide")

st.title("🏠 Simulador: Comprar Financiado vs Alugar investindo")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏠 Compra 🤑️")
    valor_imovel = st.number_input("Valor do imóvel (R$)", value=300000)
    entrada = st.number_input("Entrada financiamento (R$)", value=40000)
    valorizacao = st.number_input("Valorização anual do imovel (%)", value=3.0)
    juros_financiamento = st.number_input("Juros anual do financiamento (%)", value=10.0)

juros_anual = juros_financiamento/100


with col2:
    st.subheader("🏢 Aluguel")
    aluguel = st.number_input("Aluguel mensal (R$)", value=2000)
    reajuste = st.number_input("Reajuste anual do aluguel (%)", value=3.0)

aluguel_atual = aluguel * 12

with col3:
    st.subheader("💰 Financeiro")
    rendimento = st.number_input("Rendimento investimento(%)", value=10.0)
    capacidade = st.number_input("Valor máximo que você pode pagar por mês para alugar ou pagar financiamento", value=3000)
    prazo_financiamento = st.number_input("Prazo do financiamento (anos)", value=30)

juros_mensal = juros_financiamento / 100 / 12
n = prazo_financiamento * 12
pv = valor_imovel - entrada

parcela_estimada = abs(npf.pmt(juros_mensal, n, -pv))

################## MOTOR DE CALCULO


anos = list(range(0, prazo_financiamento + 1))

valor = valor_imovel
saldo = valor_imovel - entrada

dados = []

invest_aluguel = entrada
amortizacao_anual = (valor_imovel - entrada) / prazo_financiamento

invest_aluguel = entrada

for ano in anos:
    patrimonio_compra = max(valor - saldo, 0)

    dados.append({
        "ano": ano,
        "patrimonio_compra": patrimonio_compra,
        "patrimonio_aluguel": invest_aluguel
    })

    # atualizações

    # --- COMPRA ---
    juros_ano = saldo * juros_anual
    parcela_ano = juros_ano + amortizacao_anual

    saldo -= amortizacao_anual
    saldo = max(saldo, 0)

    # --- ALUGUEL ---
    aluguel_ano = aluguel_atual

    # --- APORTES DINÂMICOS ---
    aporte_compra = max((capacidade * 12) - parcela_ano, 0)
    aporte_aluguel = max((capacidade * 12) - aluguel_ano, 0)

    # --- INVESTIMENTOS ---
    invest_aluguel = (invest_aluguel + aporte_aluguel) * (1 + rendimento/100)

    # --- ATUALIZAÇÕES ---
    valor *= (1 + valorizacao/100)
    aluguel_atual *= (1 + reajuste/100)

df = pd.DataFrame(dados)

final_compra = df["patrimonio_compra"].iloc[-1]
final_aluguel = df["patrimonio_aluguel"].iloc[-1]

diferenca = abs(final_compra - final_aluguel)

#####################

colA, colB, colC = st.columns(3)

colA.metric("Patrimônio Compra ", f"R$ {final_compra:,.0f}")
colB.metric("Patrimônio Aluguel", f"R$ {final_aluguel:,.0f}")
colC.metric("Diferença", f"R$ {diferenca:,.0f}")

st.info(f"💸 Parcela estimada do financiamento: R$ {parcela_estimada:,.0f}/mês")
st.caption("Parcela diminui ao longo do tempo (modelo aproximado SAC)")

if final_compra > final_aluguel:
    resultado = "🏠 Comprar é melhor"
else:
    resultado = "💰 Alugar é melhor" #rafa

######################### GRAFICO
st.divider()
st.subheader("📊 Evolução do patrimônio")

fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(df["ano"], df["patrimonio_compra"], label="Comprar", linewidth=2)
ax.plot(df["ano"], df["patrimonio_aluguel"], label="Alugar + investir", linewidth=2)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R$ {int(x):,}'.replace(',', '.')))

ax.set_title("Patrimônio x tempo")
ax.set_xlabel("Ano")
ax.set_ylabel("Patrimônio")
ax.legend()

st.pyplot(fig)

#fig.savefig("grafico.png")

########################### INSIGHTS

if final_compra > final_aluguel:
    st.success(f"🏠 Comprar é melhor (+R$ {final_compra - final_aluguel:,.0f})")
else:
    st.info(f"💰 Investir é melhor (+R$ {final_aluguel - final_compra:,.0f})")

########################## RELATORIOS

st.subheader("📄 Análise")

st.write(f"""
- Seu patrimonio/imovel (estimativa) no final se comprar: R$ {final_compra:,.0f}
- Seu investimentoi (estimativa) no final se continuar alugando com investimento da
    entrada e aportando a diferença entre aluguel e parcela do financiamento 
    se houver: R$ {final_aluguel:,.0f}

Este cenário considera:
- imovel com valorização anual: {valorizacao}%
- rendimento do investimento: {rendimento}%

# Resultado:
# {'Comprar é mais vantajoso' if final_compra > final_aluguel else 'Continuar alugando é mais vantajoso'}
# """)    

################################## PDF


def gerar_pdf(resultado, diferenca, compra, aluguel, reajuste, rendimento):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        title="Simulação Imobiliária",
        author="Simulador Imobiliário",
        subject="Comparação entre comprar imóvel e alugar investindo a entrada"
        )
    styles = getSampleStyleSheet()
    
    centered_style = ParagraphStyle(
        name="CenteredHeading",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        spaceBefore=20,
        spaceAfter=20
    )

    elementos = []

    elementos.append(Paragraph("Simulação: Comprar vs Alugar", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Resultado da Simulação", styles["Title"]))
    elementos.append(Paragraph(f"<b>{resultado}</b>", centered_style))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Diferença: R$ {diferenca:,.0f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    # salvar gráfico em memória
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png")
    img_buffer.seek(0)

    elementos.append(Paragraph("Evolução do Patrimônio", styles["Heading2"]))
    elementos.append(Spacer(1, 12))
    elementos.append(Image(img_buffer, width=400, height=250))

    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Valores finais", styles["Heading2"]))
    elementos.append(Paragraph(f"Comprar: R$ {compra:,.0f}", styles["Normal"]))
    elementos.append(Paragraph(f"Alugar: R$ {aluguel:,.0f}", styles["Normal"]))

    elementos.append(Paragraph(f"==========================", styles["Normal"]))
    elementos.append(Paragraph(f"==========================", styles["Normal"]))


    elementos.append(Paragraph(f"O custo do financiamento começa alto e reduz ao longo do tempo", styles["Normal"]))
    elementos.append(Paragraph(f"O aluguel cresce por conta de reajuste ({reajuste}% ao ano)", styles["Normal"]))
    elementos.append(Paragraph(f"O valor investido cresce a {rendimento}% ao ano", styles["Normal"]))
    elementos.append(Paragraph(f"A diferença mensal entre os cenários foi reinvestida", styles["Normal"]))


    doc.build(elementos)

    buffer.seek(0)
    return buffer

st.subheader("📊 Resultado")

st.write(resultado)
st.write(f"Diferença: R$ {diferenca:,.0f}")

st.write(f"""
📌 Por que esse resultado?

- O custo do financiamento começa alto e reduz ao longo do tempo
- O aluguel cresce com inflação ({reajuste}% ao ano)
- O valor investido cresce a {rendimento}% ao ano
- A diferença mensal entre os cenários foi reinvestida

👉 Isso fez o cenário de {'compra' if final_compra > final_aluguel else 'aluguel + investimento'} acumular mais patrimônio.
""")

if st.button("📄 Gerar relatório"):
    pdf = gerar_pdf(resultado, diferenca, final_compra, final_aluguel, reajuste, rendimento)

    st.download_button(
        label="Download PDF",
        data=pdf,
        file_name="simulacao-imobiliaria.pdf",
        mime="application/pdf"
    )