import httpx

BASE_URL = "http://localhost:8000"

EXEMPLOS = [
    {
        "numero_trm": "278163",
        "tipo_demanda": "Melhoria",
        "modulo_sistema": "Financeiro — Atributos de Cobrança / Itens de Cobrança",
        "objeto_afetado": "GnAtributoCobComissionados (coleção Classificação)",
        "descricao_problema": (
            "Ausência de coleção de classificações por percentual abaixo do cadastro de "
            "comissionados. Cliente necessitava definir percentuais distintos por tipo/"
            "classificação (ex: Diretor, Gerente de Conta, Executor) para o mesmo "
            "comissionado, com o campo Percentual na capa refletindo a soma das "
            "classificações cadastradas."
        ),
        "descricao_solucao": (
            "Criada nova coleção Classificações para Comissionados nas páginas Atributos "
            "de Cobrança e Itens de Cobrança. Quando não há classificações cadastradas, o "
            "campo Percentual permanece editável. Após cadastrar classificações, o campo "
            "Percentual torna-se somente leitura e exibe a soma dos percentuais da coleção. "
            "Changeset TFS 92874, replicado para release 6.0.143 via TFS 92941. "
            "XML de customização obrigatório."
        ),
        "release": "6.00.147",
        "patch": "PacoteComplementar_6.0.143.7",
        "tag_customizacao": None,
        "changesets": ["TFS 92874", "TFS 92941"],
        "data_liberacao": "2021-07-15",
        "especifico_cliente": True,
    },
    {
        "numero_trm": "278200",
        "tipo_demanda": "Correção",
        "modulo_sistema": "RH — Folha de Pagamento",
        "objeto_afetado": "GnFolhaPagamento",
        "descricao_problema": "Cálculo incorreto de INSS para salários acima do teto.",
        "descricao_solucao": "Corrigida a tabela de alíquotas progressivas conforme IN 2110/2022.",
        "release": "6.00.148",
        "patch": None,
        "tag_customizacao": None,
        "changesets": ["TFS 93001"],
        "data_liberacao": "2021-08-03",
        "especifico_cliente": False,
    },
]


def enviar(payload):
    r = httpx.post(f"{BASE_URL}/tickets", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print("Escolha o modo de envio:")
    print("  1 - Enviar um único chamado (primeiro exemplo)")
    print("  2 - Enviar múltiplos chamados (array com dois exemplos)")
    modo = input("Opção: ").strip()

    if modo == "1":
        resultado = enviar(EXEMPLOS[0])
    elif modo == "2":
        resultado = enviar(EXEMPLOS)
    else:
        print("Opção inválida.")
        raise SystemExit(1)

    import json
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
