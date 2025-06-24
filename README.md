# python-lambda-hub-websocket-auth

![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=amazon-aws&style=for-the-badge)
![WebSocket](https://img.shields.io/badge/API%20Gateway-WebSocket-blue?style=for-the-badge)
![DynamoDB](https://img.shields.io/badge/DynamoDB-NoSQL-blueviolet?logo=amazon-aws&style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge)

Este projeto implementa uma arquitetura de comunicação em tempo real utilizando WebSocket via API Gateway, AWS Lambda e DynamoDB. O serviço permite que sessões conectadas via navegador troquem mensagens em tempo real através de um HUB centralizado.

---

## 📚 Sumário

- [Arquitetura da Solução](#arquitetura-da-solução)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Deploy](#deploy)
- [Rotas WebSocket](#rotas-websocket)
- [Testes Locais](#testes-locais)
- [Especificação Funcional](#especificação-funcional)
- [Autenticação e Segurança](#autenticação-e-segurança)
- [Estrutura da Tabela DynamoDB](#estrutura-da-tabela-dynamodb)
- [Tratamento de Erros e Logs](#tratamento-de-erros-e-logs)
- [Fluxo Arquitetural](#fluxo-arquitetural)
- [Monitoramento](#monitoramento)

---

## 📐 Arquitetura da Solução

Abaixo está o fluxo completo do serviço WebSocket com API Gateway e AWS Lambda:

![Arquitetura da Solução](docs/img/solucao_lambda_hub_aws_python_atualizada.drawio.png)

---

## 🛠️ Tecnologias Utilizadas

- **AWS Lambda (Python 3.12)**
- **Amazon API Gateway (WebSocket)**
- **Amazon DynamoDB**
- **AWS SAM (Serverless Application Model)**
- **AWS Secrets Manager**

---

## 📁 Estrutura do Projeto

```text
    python-lambda-hub-websocket-auth/
    │
    ├── connect/        # Lambda: onConnect
    │   └── on_connect_lambda.py
    │
    ├── disconnect/     # Lambda: onDisconnect
    │   └── on_disconnect_lambda.py
    │
    ├── send-message/   # Lambda: messageSender
    │   └── on_send_message_lambda.py
    │
    ├── template.yaml   # AWS SAM CloudFormation template
    └── events/         # Testes locais (JSON)
```

## Deploy
### Pré-requisitos
    - AWS SAM CLI

### Passos de Deploy

```text
aws configure
sam build
sam deploy --guided
```

Durante o deploy, você informará:
    * Nome da stack
    * Região AWS
    * Nome da tabela DynamoDB (TABLE_NAME)
    * Nome do segredo no Secrets Manager (SIGNING_SECRET_NAME)
    * Endpoint WebSocket (opcional)


| Rota WebSocket | Função Lambda      | Ação                             |
| -------------- | ------------------ | -------------------------------- |
| `$connect`     | ConnectFunction    | Salva conexão na tabela DynamoDB |
| `$disconnect`  | DisconnectFunction | Remove conexão da tabela         |
| `sendMessage`  | MessageFunction    | Envia mensagens para as conexões |

## 📦 Testes Locais
Utilizar os eventos de teste disponíveis em events/ com o comando:
```bash
sam local invoke ConnectFunction --event events/connect.json
```

## # Especificação Funcional - Serviço python-lambda-hub-websocket-auth

## Visão Geral

O serviço permite a troca de mensagens em tempo real entre usuários conectados a um HUB WebSocket, utilizando AWS Lambda e DynamoDB para persistência e comunicação via API Gateway.

## Funcionalidades

### 1. Conexão WebSocket (`$connect`)

- **Trigger**: Evento de conexão WebSocket.
- **Ação**: A Lambda `ConnectFunction` armazena `connection_id` e `session_id` no DynamoDB.
- **Objetivo**: Registrar usuários para comunicação futura.

### 2. Desconexão WebSocket (`$disconnect`)

- **Trigger**: Encerramento de conexão.
- **Ação**: `DisconnectFunction` remove o `connection_id` da tabela DynamoDB.
- **Objetivo**: Limpar conexões inativas.

### 3. Envio de Mensagem (`sendMessage`)

- **Trigger**: Mensagem do cliente contendo lista de sessões.
- **Ação**:
  - `MessageFunction` busca todos os `connection_id` relacionados aos `session_id` fornecidos.
  - Usa o `apigatewaymanagementapi` para enviar mensagens em tempo real.
- **Objetivo**: Disseminar atualizações entre clientes conectados.

## Estrutura da Tabela DynamoDB

| Atributo      | Tipo |
|---------------|------|
| session_id    | S    |
| connection_id | S    |

## Exceções e Logs

- Todos os handlers capturam erros com `try/except`.
- Logs de eventos e falhas são enviados para o CloudWatch com nível `INFO` e `ERROR`.

## Fluxo Arquitetural

1. Usuário abre navegador com WebSocket.
2. Ao conectar, a `ConnectFunction` registra a sessão.
3. Ao enviar dados para uma sessão, `MessageFunction` envia para todos os `connection_id` daquela `session_id`.
4. Ao desconectar, `DisconnectFunction` remove a conexão.

## Segurança

- A autenticação não está ativada no WebSocket (por padrão).
- Pode-se adicionar autenticação via JWT no futuro.

## Monitoramento

- CloudWatch Logs para cada função.
- Métricas de conexão e envio disponíveis via API Gateway e Lambda Metrics.

---





