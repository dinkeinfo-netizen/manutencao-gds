# Sistema de Manutenção GDS - RQ MAN – 073 01

Uma aplicação web completa baseada em Flask para gestão de ordens de serviço (OS), equipamentos e equipe técnica. Este sistema otimiza o fluxo de trabalho de manutenção, desde a solicitação até a conclusão, incluindo assinaturas digitais e notificações automatizadas.

## 🚀 Funcionalidades

- **Gestão de Ordens de Serviço**: Criação, acompanhamento e finalização de OS.
- **Automação de Fluxo**: Transições automáticas de status (Aberta -> Em Andamento -> Concluída).
- **Assinaturas Digitais**: Coleta de assinaturas do mecânico e do conferente para validação.
- **Importação/Exportação em Massa**: Importação de equipamentos e localizações via Excel; exportação de histórico de manutenção e KPIs.
- **Dashboard de Indicadores**: KPIs em tempo real por mecânico, indisponibilidade de equipamentos e tipos de manutenção.
- **Níveis de Acesso**: Permissões especializadas para Admin, Mecânicos e Usuários Padrão.
- **Notificações por E-mail**: Alertas automáticos para abertura e finalização de atividades de manutenção.

## 🛠 Tecnologias Utilizadas

- **Backend**: Python / Flask
- **Banco de Dados**: MySQL 8.0
- **Frontend**: HTML5, Vanilla CSS, Bootstrap 5, Chart.js
- **Conteinerização**: Docker & Docker Compose
- **Processamento de Dados**: Pandas / Openpyxl (Integração com Excel)

## 📦 Configuração e Instalação

### Pré-requisitos
- Docker e Docker Compose instalados.

### Passos
1. **Clonar o repositório**:
   ```bash
   git clone https://github.com/dinkeinfo-netizen/manutencao-gds.git
   cd manutencao-gds
   ```

2. **Configuração de Ambiente**:
   Crie um arquivo `.env` na raiz do diretório (use o `.env.example` como referência, se disponível) com as seguintes variáveis:
   - `SECRET_KEY`: Uma chave aleatória segura para sessões do Flask.
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Para integração de e-mail.

3. **Subir os containers**:
   ```bash
   docker-compose up -d --build
   ```

4. **Acessar a Aplicação**:
   O sistema estará disponível em `http://localhost:5001`.

## 🗄 Estrutura do Banco de Dados

O sistema utiliza SQLAlchemy como ORM. Os principais modelos incluem:
- **Mecanico**: Gestão da equipe técnica.
- **Equipamento**: Inventário de máquinas e ativos.
- **Localizacao**: Gestão de locais físicos.
- **OrdemServico**: Registro centralizado de manutenções, incluindo materiais, fotos e assinaturas.
- **User**: Autenticação e autorização de usuários.

## 📄 Documentação

Desenvolvido e mantido por **DINKE**. Referência: **RQ MAN – 073 01**.
