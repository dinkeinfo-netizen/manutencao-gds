-- init_db.sql (PostgreSQL version)

-- Table: localizacoes
CREATE TABLE IF NOT EXISTS localizacoes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL
);

-- Table: mecanicos
CREATE TABLE IF NOT EXISTS mecanicos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(20)
);

-- Table: checklist_templates
CREATE TABLE IF NOT EXISTS checklist_templates (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(255),
    ativo BOOLEAN DEFAULT TRUE
);

-- Table: checklist_itens
CREATE TABLE IF NOT EXISTS checklist_itens (
    id SERIAL PRIMARY KEY,
    template_id INT NOT NULL,
    pergunta VARCHAR(255) NOT NULL,
    ordem INT DEFAULT 0,
    FOREIGN KEY (template_id) REFERENCES checklist_templates(id) ON DELETE CASCADE
);

-- Table: equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    localizacao_id INT,
    checklist_template_id INT,
    FOREIGN KEY (localizacao_id) REFERENCES localizacoes(id),
    FOREIGN KEY (checklist_template_id) REFERENCES checklist_templates(id)
);

-- Table: users (needed before ordens_servico maybe, but definitely for admin)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL
);

-- Table: ordens_servico
CREATE TABLE IF NOT EXISTS ordens_servico (
    id SERIAL PRIMARY KEY,
    numero_os VARCHAR(20) NOT NULL UNIQUE,
    solicitante VARCHAR(100) NOT NULL,
    localizacao_id INT NOT NULL,
    tipo_manutencao VARCHAR(50) NOT NULL,
    tipo_parada VARCHAR(50) NOT NULL,
    equipamento_id INT NOT NULL,
    motivo TEXT NOT NULL,
    mecanico_id INT,
    data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_inicio_execucao TIMESTAMP,
    data_termino TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Aberta',
    sap VARCHAR(50),
    tempo_manutencao FLOAT,
    descricao_servico TEXT,
    materiais_utilizados TEXT,
    fotos_paths JSONB,
    graxa_oleo BOOLEAN,
    limpeza BOOLEAN,
    pecas_soltas BOOLEAN,
    equipamento_liberado BOOLEAN,
    nome_mecanico VARCHAR(100),
    nome_conferente VARCHAR(100),
    assinatura_mecanico TEXT,
    assinatura_conferente TEXT,
    data_assinatura_mecanico TIMESTAMP,
    data_assinatura_conferente TIMESTAMP,
    FOREIGN KEY (localizacao_id) REFERENCES localizacoes(id),
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id),
    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
);

-- Table: checklist_respostas
CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    ordem_servico_id INT NOT NULL,
    checklist_item_id INT NOT NULL,
    valor BOOLEAN,
    observacao VARCHAR(255),
    FOREIGN KEY (ordem_servico_id) REFERENCES ordens_servico(id),
    FOREIGN KEY (checklist_item_id) REFERENCES checklist_itens(id)
);

-- Table: calendario_operacional
CREATE TABLE IF NOT EXISTS calendario_operacional (
    data DATE PRIMARY KEY,
    eh_dia_util BOOLEAN DEFAULT TRUE,
    descricao VARCHAR(255)
);

-- Table: parametros_maquina_mensal
CREATE TABLE IF NOT EXISTS parametros_maquina_mensal (
    id SERIAL PRIMARY KEY,
    maquina_id INT NOT NULL,
    mes INT NOT NULL,
    ano INT NOT NULL,
    horas_turno_dia FLOAT DEFAULT 8.0,
    esta_ativa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (maquina_id) REFERENCES equipamentos(id)
);

-- Insert default admin user
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@admin.com', 'scrypt:32768:8:1$Sto5g6Q1OiXS3fEi$b2c9798a905a744f37578bcb20f49d3d4398660229c29a6aa589643e426b049dfb5942f1d784307125607bc913648ef428a8c558cbaa5db26f5a3456e6a27960', 'admin')
ON CONFLICT (username) DO UPDATE SET 
    email = EXCLUDED.email,
    role = EXCLUDED.role;
