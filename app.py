import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ARQUIVOS JSON

caminho_arquivo_categorias = "nome_despesas.json"
caminho_arquivo_gastos = "gastos.json"
caminho_arquivo_ovos = "ovos.json" 
caminho_arquivo_faturamento = "faturamento.json"
caminho_arquivo_resumo = "resumo_mensal.json"


# FUNÇÕES DE ESCRITA E LEITURA

def ler_json(caminho, valor_padrao):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return valor_padrao
    return valor_padrao

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)



# FUNÇÕES DA TELA 1 (DESPESAS)

def ler_categorias():
    return ler_json(caminho_arquivo_categorias, [])

def ler_gastos():
    return ler_json(caminho_arquivo_gastos, [])

def salvar_nome_despesa(nova_categoria):
    nova_categoria = nova_categoria.strip()
    if not nova_categoria:
        return

    categorias = ler_categorias()
    if nova_categoria not in categorias:
        categorias.append(nova_categoria)
        salvar_json(caminho_arquivo_categorias, categorias)

def salvar_gasto(categoria, valor):
    gastos = ler_gastos()
    encontrado = False

    for item in gastos:
        if item.get("categoria") == categoria:
            item["valor"] = valor
            encontrado = True
            break

    if not encontrado:
        gastos.append({"categoria": categoria, "valor": valor})

    salvar_json(caminho_arquivo_gastos, gastos)


# FUNÇÕES DA TELA 2 (Ovos)
def ler_ovos():
    return ler_json(caminho_arquivo_ovos, [])

def salvar_ovos(quantidade):
    registros = ler_ovos()
    agora = datetime.now()

    registros.append({
        "quantidade": quantidade,
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M:%S")
    })

    salvar_json(caminho_arquivo_ovos, registros)


# FUNÇÕES DA TELA 3 (Faturamentos)

def ler_faturamento():
    return ler_json(caminho_arquivo_faturamento, [])

def salvar_faturamento(valor_recebido):
    registros = ler_faturamento()
    agora = datetime.now()

    registros.append({
        "valor_ganho": valor_recebido,
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M:%S")
    })

    salvar_json(caminho_arquivo_faturamento, registros)


# FUNÇÕES DA TELA 4 (Lucro)

def ler_resumos():
    return ler_json(caminho_arquivo_resumo, {})

def salvar_resumo_json(mes, faturamento, despesas, lucro):
    resumos = ler_resumos()
    resumos[mes] = {
        "faturamento": faturamento,
        "despesas": despesas,
        "lucro": lucro
    }
    salvar_json(caminho_arquivo_resumo, resumos)

def obter_dados_tela_lucro(mes_solicitado=None):
    faturamentos = ler_faturamento()
    gastos = ler_gastos()

    meses_disponiveis = sorted(
        list(set(item.get("data", "")[3:] for item in faturamentos if len(item.get("data", "")) >= 10)),
        reverse=True
    )

    if not meses_disponiveis:
        meses_disponiveis = [datetime.now().strftime("%m/%Y")]

    mes_selecionado = mes_solicitado if mes_solicitado in meses_disponiveis else meses_disponiveis[0]

    detalhes_dias = {}
    total_faturamento = 0.0

    for item in faturamentos:
        dia_data = item.get("data", "")
        if dia_data[3:] == mes_selecionado:
            val = float(item.get("valor_ganho", 0))
            total_faturamento += val
            detalhes_dias[dia_data] = detalhes_dias.get(dia_data, 0.0) + val

    total_despesas = sum(float(g.get("valor", 0)) for g in gastos)
    lucro_total = total_faturamento - total_despesas

    salvar_resumo_json(mes_selecionado, total_faturamento, total_despesas, lucro_total)

    linhas_tabela = [{"dia": dia, "valor": valor} for dia, valor in detalhes_dias.items()]

    return {
        "meses": meses_disponiveis,
        "mes_selecionado": mes_selecionado,
        "linhas": linhas_tabela,
        "total_faturamento": total_faturamento,
        "total_despesas": total_despesas,
        "lucro_total": lucro_total
    }


# ROTAS DO FLASK

# --- MENU PRINCIPAL (NOVA ROTA INICIAL) ---
@app.route("/", methods=['GET'])
def menu_principal():
    return render_template("menu.html")

# --- TELA 1: DESPESAS ---
@app.route("/despesas", methods=['GET'])
def index():
    categorias = ler_categorias()
    return render_template("index.html", categorias=categorias)


@app.route("/Despesas", methods=['POST'])
def cadastrar_categoria():
    nova_categoria = request.form.get('nome_categoria', '')
    salvar_nome_despesa(nova_categoria)
    return redirect(url_for('index'))

@app.route("/registrar_despesa_gasto", methods=['POST'])
def registrar_gasto():
    categoria_selecionada = request.form.get('EscolherDespesa')
    valor_informado = request.form.get('valor')

    if categoria_selecionada and valor_informado:
        try:
            salvar_gasto(categoria_selecionada, float(valor_informado))
        except ValueError:
            pass

    return redirect(url_for('index'))


# --- TELA 2: OVOS ---
@app.route("/ovos", methods=['GET'])
def tela_ovos():
    registros_ovos = ler_ovos
    return render_template("ovos.html")

@app.route("/registrar_ovos", methods=['POST'])
def registrar_ovos():
    quantidade_informada = request.form.get('quantidade_ovos')
    if quantidade_informada:
        try:
            salvar_ovos(int(quantidade_informada))
        except ValueError:
            pass

    return redirect(url_for('tela_ovos'))


# --- TELA 3: FATURAMENTO ---
@app.route("/faturamento", methods=['GET'])
def tela_faturamento():
    registros = ler_faturamento()
    return render_template("faturamento.html", historico=registros)

@app.route("/registrar_faturamento", methods=['POST'])
def registrar_faturamento():
    valor_form = request.form.get('valor_ganho')

    if valor_form:
        try:
            salvar_faturamento(float(valor_form))
        except ValueError:
            pass

    return redirect(url_for('tela_faturamento'))


# --- TELA 4: LUCRO MENSAL ---
@app.route("/lucro", methods=['GET'])
def tela_lucro():
    mes_solicitado = request.args.get('EscolherMes')
    dados = obter_dados_tela_lucro(mes_solicitado)
    return render_template("lucro.html", dados=dados)


if __name__ == '__main__':
    app.run(debug=True)