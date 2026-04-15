from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Simulador Imobiliário", layout="wide")

st.title("🏠 Simulador: Comprar Financiado vs Alugar investindo a entrada")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏠 Compra")
    valor_imovel = st.number_input("Valor do imóvel", value=300000)
    entrada = st.number_input("Entrada financiamento", value=40000)
    valorizacao = st.number_input("Valorização anual do imovel (%)", value=3.0)
    juros_financiamento = st.number_input("Juros do financiamento (%)", value=10.0)

with col2:
    st.subheader("🏢 Aluguel")
    aluguel = st.number_input("Aluguel mensal", value=2000)
    reajuste = st.number_input("Reajuste anual do aluguel (%)", value=3.0)

with col3:
    st.subheader("💰 Financeiro")
    rendimento = st.number_input("Rendimento investimento(%)", value=10.0)
    capacidade = st.number_input("Capacidade financeira mensal para imovel", value=3000)
    prazo = st.number_input("Prazo do financiamento (anos)", value=30)
    parcela_estimada = (valor_imovel - entrada) / (prazo * 12) + ((valor_imovel - entrada)*(1+juros_financiamento)**1/12) - (valor_imovel - entrada)


################## MOTOR


anos = list(range(0, prazo + 1))

valor = valor_imovel
saldo = valor_imovel - entrada

dados = []

invest_aluguel = entrada
amortizacao_anual = (valor_imovel - entrada) / prazo
aporte_aluguel = max(capacidade - aluguel, 0) * 12
invest_aluguel = entrada

for ano in anos:
    patrimonio_compra = max(valor - saldo, 0)

    dados.append({
        "ano": ano,
        "patrimonio_compra": patrimonio_compra,
        "patrimonio_aluguel": invest_aluguel
    })

    # atualizações
    valor *= (1 + valorizacao/100)
    saldo -= amortizacao_anual
    saldo = max(saldo, 0)
    invest_aluguel = (invest_aluguel + aporte_aluguel) * (1 + rendimento/100)

df = pd.DataFrame(dados)

final_compra = df["patrimonio_compra"].iloc[-1]
final_aluguel = df["patrimonio_aluguel"].iloc[-1]

diferenca = abs(final_compra - final_aluguel)

colA, colB, colC = st.columns(3)

colA.metric("Patrimônio Compra", f"R$ {final_compra:,.0f}")
colB.metric("Patrimônio Aluguel", f"R$ {final_aluguel:,.0f}")
colC.metric("Diferença", f"R$ {diferenca:,.0f}")

st.info(f"💸 Parcela estimada do financiamento: R$ {parcela_estimada:,.0f}/mês")

if final_compra > final_aluguel:
    resultado = "🏠 Comprar é melhor"
else:
    resultado = "💰 Alugar + investir é melhor"

######################### GRAFICO
st.divider()
st.subheader("📊 Evolução do patrimônio")

fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(df["ano"], df["patrimonio_compra"], label="Comprar", linewidth=2)
ax.plot(df["ano"], df["patrimonio_aluguel"], label="Alugar + investir", linewidth=2)

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R$ {int(x):,}'.replace(',', '.')))

ax.set_title("Comparação de Patrimônio ao Longo do Tempo")
ax.set_xlabel("Ano")
ax.set_ylabel("Patrimônio")
ax.legend()

st.pyplot(fig)

#fig.savefig("grafico.png")

########################### INSIGHTS

if final_compra > final_aluguel:
    st.success(f"🏠 Comprar é melhor (+R$ {final_compra - final_aluguel:,.0f})")
else:
    st.warning(f"💰 Investir é melhor (+R$ {final_aluguel - final_compra:,.0f})")

########################## RELATORIOS

st.subheader("📄 Análise")

st.write(f"""
- Patrimônio comprando: R$ {final_compra:,.0f}
- Patrimônio alugando: R$ {final_aluguel:,.0f}

Este cenário considera:
- valorização de {valorizacao}%
- rendimento de {rendimento}%

Resultado:
{'Comprar é mais vantajoso' if final_compra > final_aluguel else 'Investir é mais vantajoso'}
""")    

################################## PDF


def gerar_pdf(resultado, diferenca, compra, aluguel):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(Paragraph("Simulação: Comprar vs Alugar", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Resultado da Simulação", styles["Heading2"]))
    elementos.append(Paragraph(f"<b>{resultado}</b>", styles["Title"]))
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

    doc.build(elementos)

    buffer.seek(0)
    return buffer

st.subheader("📊 Resultado")

st.write(resultado)
st.write(f"Diferença: R$ {diferenca:,.0f}")

if st.button("📄 Gerar relatório"):
    pdf = gerar_pdf(resultado, diferenca, final_compra, final_aluguel)

    st.download_button(
        label="Download PDF",
        data=pdf,
        file_name="simulacao-imobiliaria.pdf",
        mime="application/pdf"
    )