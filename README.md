# MJ_PONTO_GESTAO

Aplicacao Flask para gestao de ponto com autenticacao, funcionarios, historico, relatorios e exportacao.

## Objetivo desta preparacao

Esta versao foi ajustada para:

- rodar localmente com a estrutura atual
- permitir deploy publico em ambiente gratuito
- manter a base pronta para upgrade futuro para plano pago
- evitar exposicao de segredos no repositorio
- suportar um cenario simples de teste com ate 10 usuarios sem refatoracao estrutural

As regras de negocio do sistema nao foram alteradas.

## Stack de deploy

- Python 3.12
- Flask
- Gunicorn para execucao em producao
- Render como exemplo de hospedagem gratuita

## Variaveis de ambiente

Defina estas variaveis no ambiente local ou no provedor de hospedagem:

- `SECRET_KEY`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `FIREBASE_CREDENTIALS_JSON` com o JSON completo da service account
- `FLASK_ENV=production` em producao
- `FLASK_DEBUG=false` em producao
- `AUTO_OPEN_BROWSER=false` em producao

## Credenciais do Firebase

Para ambiente local e hospedado, use:

- `FIREBASE_CREDENTIALS_JSON` com o JSON completo da service account

O projeto converte esse JSON diretamente para dicionario em tempo de execucao, sem exigir arquivo de credencial no repositorio ou no servidor.

## Execucao local

1. Crie um ambiente virtual.
2. Instale as dependencias com `pip install -r requirements.txt`.
3. Defina as variaveis de ambiente necessarias.
4. Rode com `python app.py`.

Exemplo de configuracao local:

```powershell
$env:SECRET_KEY="uma-chave-local"
$env:FIREBASE_PROJECT_ID="seu-projeto"
$env:FIREBASE_STORAGE_BUCKET="seu-bucket.appspot.com"
$env:FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"seu-projeto"}'
python app.py
```

## Deploy no Render

1. Suba o projeto para um repositorio Git.
2. Crie um novo Web Service no Render.
3. Use o arquivo `render.yaml` ou configure manualmente:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Configure as variaveis de ambiente:
   - `SECRET_KEY`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_STORAGE_BUCKET`
   - `FIREBASE_CREDENTIALS_JSON`
   - `FLASK_ENV=production`
   - `FLASK_DEBUG=false`
   - `AUTO_OPEN_BROWSER=false`

## Upgrade futuro sem grande refatoracao

Esta preparacao ja deixa a base pronta para evoluir com baixo impacto:

- troca simples de plano gratuito para pago no mesmo provedor
- aumento de recursos sem mudar controllers ou templates
- substituicao do segredo local por variaveis gerenciadas no provedor
- migracao futura para worker, cache ou banco complementar sem alterar regras do sistema

## Seguranca

- Nao commite arquivos `.env`
- Nao commite chaves privadas nem JSON de service account
- Se existir alguma credencial que ja foi compartilhada fora deste fluxo, gere uma nova no Firebase

## Arquivos de deploy incluidos

- `requirements.txt`
- `render.yaml`
- `.gitignore`
- `README.md`
