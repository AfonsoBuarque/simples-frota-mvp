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

| Tela | Endereço | Perfil | Função |
|------|----------|--------|--------|
| Entrar | `/entrar/` | Todos | Login; cada perfil vai para a sua tela inicial |
| Minhas entregas | `/entregas/` | Motorista | Lista as entregas atribuídas, inicia a rota e abre o comprovante |
| Registrar comprovante | `/entregas/<id>/comprovante/` | Motorista | Foto ou assinatura na tela; conclui a entrega |
| Painel do gerente | `/painel/` | Gerente | Indicadores, filtros por status e destaque para as atrasadas |
| Nova entrega | `/painel/nova/` | Gerente | Cadastra e atribui uma entrega a um motorista |
| Acompanhar entrega | `/acompanhar/<token>/` | Público | Status da entrega por link, sem login e sem dados internos |

## Acessibilidade

- Barra de acessibilidade em todas as telas: **Alto contraste** (fundo preto, texto branco, ações em amarelo) e **A− / A+** para ajustar o texto de 100% a 160%; a preferência fica salva no navegador
- Página em `pt-BR`, link "Pular para o conteúdo" e foco visível em todos os controles
- Botões e áreas de toque com no mínimo 44 px (48 px nos botões principais)
- Status sempre escrito por extenso, nunca indicado só por cor
- Cores com contraste mínimo de 4,5:1 (WCAG 2.1 AA)
- Rótulos em todos os campos, mensagens anunciadas por leitores de tela (`role="status"` e `role="alert"`)
- Assinatura na tela opcional, com a foto do comprovante como alternativa

## Tecnologias

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Arquitetura monolítica em três camadas (interface, regras de negócio, persistência)
- Autenticação com hash de senha Argon2 e proteções alinhadas ao OWASP Top 10

## Modelo de dados

Três entidades principais: `Usuario`, `Entrega` e `Comprovante`.

## Como executar localmente

Pré-requisitos: Python 3.12 e Git. O PostgreSQL 16 é opcional no desenvolvimento: sem `DB_NAME` no `.env`, o projeto usa SQLite.

```bash
git clone https://github.com/AfonsoBuarque/simples-frota-mvp.git
cd simples-frota-mvp

python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
```

Copie `.env.example` para `.env`. Para usar SQLite, apague ou comente a linha `DB_NAME`. Depois rode:

```bash
python manage.py migrate
python manage.py popular_demo
python manage.py runserver
```

Acesse http://127.0.0.1:8000. O comando `popular_demo` (só funciona com `DJANGO_DEBUG=True`) cria entregas de exemplo e os usuários abaixo, todos com a senha `demo12345`:

| Usuário | Perfil |
|---------|--------|
| `gerente` | Gerente |
| `carlos` | Motorista |
| `marina` | Motorista |

Use `python manage.py popular_demo --reset` para recriar as entregas.

## Publicação (deploy) e monitoramento

O MVP roda em produção no **Railway**, a partir do `Dockerfile` deste repositório:

- **Aplicação:** Django servido pelo Gunicorn, com arquivos estáticos comprimidos pelo WhiteNoise
- **Banco:** PostgreSQL gerenciado pelo Railway, ligado pela variável `DATABASE_URL`
- **Arquivos de comprovante:** volume persistente montado em `/app/media` e servidos só a usuários autorizados
- **HTTPS:** certificado do Railway, com redirecionamento HTTPS, cookies `Secure` e HSTS
- **Migrações:** aplicadas automaticamente a cada deploy

Variáveis de ambiente usadas em produção:

| Variável | Exemplo |
|----------|---------|
| `DJANGO_SECRET_KEY` | chave aleatória longa |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `simples-frota.up.railway.app` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://simples-frota.up.railway.app` |
| `DATABASE_URL` | fornecida pelo Railway |
| `DJANGO_MEDIA_ROOT` | `/app/media` |
| `DEMO_SENHA` | senha dos usuários de demonstração (mínimo de 10 caracteres) |
| `DEMO_SEED` | `True` cria os usuários e as entregas de demonstração ao iniciar (idempotente); remova depois de usar |

Para criar os dados de demonstração em produção: `python manage.py popular_demo --producao`. Esse comando nunca usa a senha conhecida do repositório.

### Monitoramento

- **Health check:** `GET /saude/` responde `{"status": "ok", "banco": "ok"}` e testa a conexão com o banco (HTTP 503 se o banco cair). O Railway usa essa rota para validar cada deploy (`railway.json`).
- **Disponibilidade:** o UptimeRobot consulta `/saude/` a cada 5 minutos e envia alerta por e-mail se o site sair do ar.
- **Logs:** acessos do Gunicorn e eventos do sistema (`comprovante_registrado`, `ocorrencia_registrada`, erros) em linha única na saída padrão, visíveis no painel do Railway.

## Testes

```bash
python manage.py test
```

Testes unitários e de integração, com análise de cobertura, serão adicionados ao longo da implementação.

## Integração Contínua

[![CI](https://github.com/AfonsoBuarque/simples-frota-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/AfonsoBuarque/simples-frota-mvp/actions/workflows/ci.yml)

O pipeline do GitHub Actions (`.github/workflows/ci.yml`) roda a cada push na `main` e a cada Pull Request, com Python 3.12 e PostgreSQL 16:

1. Instala as dependências
2. Verifica o projeto (`manage.py check`) e se há migrações pendentes
3. Executa os testes com cobertura
4. Falha se a cobertura ficar abaixo de 90%

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