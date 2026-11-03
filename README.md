# Simples Frota MVP

MVP web para gestão de entregas e comprovantes digitais da **Simples Frota**, pequena transportadora de Vila Progresso, São Paulo/SP (5 veículos, 15 colaboradores).

Projeto desenvolvido na disciplina de **Projeto de Software** (Experiência Prática III), a partir do diagnóstico e do desenho técnico feitos nas Experiências Práticas I e II.

## Problema

A gestão das entregas é feita à mão, com papel e WhatsApp. Os comprovantes (canhotos) se perdem e o gerente gasta tempo respondendo consultas de status. Este MVP centraliza o ciclo da entrega em um fluxo curto, que funciona no navegador do celular, sem instalar aplicativo.

## Alinhamento com os ODS

**ODS 8 — Trabalho Decente e Crescimento Econômico** (metas 8.2 e 8.3): produtividade e formalização de uma pequena empresa por meio de tecnologia simples e de baixo custo.

## Escopo do MVP

Incluído:

- Cadastro de entregas pelo gerente (cliente, endereço, observações)
- Atribuição da entrega a um motorista
- Atualização de status pelo motorista, em poucos toques
- Comprovante digital (foto ou assinatura na tela) com data e hora
- Painel do gerente com todas as entregas e destaque para as atrasadas
- Página pública de consulta de status por link, sem login

Fora do escopo desta versão:

- Roteirização e GPS em tempo real
- Módulo fiscal (nota fiscal)
- Aplicativo nativo
- Avisos automáticos, mapa e chat

## Telas

| Tela | Perfil | Função |
|------|--------|--------|
| Minhas entregas | Motorista | Lista as entregas atribuídas e permite atualizar o status |
| Registrar entrega | Gerente | Cadastra e atribui uma nova entrega |
| Painel do gerente | Gerente | Visão geral das entregas e dos atrasos |

## Tecnologias

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Arquitetura monolítica em três camadas (interface, regras de negócio, persistência)
- Autenticação com hash de senha Argon2 e proteções alinhadas ao OWASP Top 10

## Modelo de dados

Três entidades principais: `Usuario`, `Entrega` e `Comprovante`.

## Como executar localmente

Pré-requisitos: Python 3.12, PostgreSQL 16 e Git.

```bash
git clone https://github.com/AfonsoBuarque/simples-frota-mvp.git
cd simples-frota-mvp

python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

Configure as variáveis de ambiente do banco (modelo em `.env.example`) e rode:

```bash
python manage.py migrate
python manage.py runserver
```

> As instruções serão atualizadas conforme o código for adicionado ao repositório.

## Testes

```bash
python manage.py test
```

Testes unitários e de integração, com análise de cobertura, serão adicionados ao longo da implementação.

## Integração Contínua

Um pipeline no GitHub Actions executará o build e os testes a cada push e Pull Request.

## Fluxo de trabalho

- Branch principal: `main`, protegida pelo fluxo de Pull Request
- Uma branch por funcionalidade: `feat/...`, `fix/...`, `docs/...`, `test/...`, `ci/...`
- Commits semânticos ([Conventional Commits](https://www.conventionalcommits.org/pt-br/)): `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`
- Toda alteração entra na `main` por Pull Request, com auto-revisão técnica

## Validação com a comunidade

O MVP será validado em pelo menos duas rodadas de testes de usabilidade com o gerente da Simples Frota. Os feedbacks e os ajustes resultantes serão documentados neste repositório.

## Autor

Afonso Buarque — [@AfonsoBuarque](https://github.com/AfonsoBuarque)

Projeto acadêmico — Cruzeiro do Sul Virtual.