-- init_db.sql
CREATE DATABASE IF NOT EXISTS manutencao_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'manutencao_user'@'%' 
IDENTIFIED WITH mysql_native_password BY 'manutencao_pass';

GRANT ALL PRIVILEGES ON manutencao_db.* TO 'manutencao_user'@'%';
FLUSH PRIVILEGES;

USE manutencao_db;

-- Tabela de Localizações
CREATE TABLE IF NOT EXISTS localizacoes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL
);

-- Tabela de Mecânicos
CREATE TABLE IF NOT EXISTS mecanicos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(20)
);

-- Tabela de Equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS ordens_servico (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero_os VARCHAR(20) NOT NULL UNIQUE,
    solicitante VARCHAR(100) NOT NULL,
    localizacao_id INT NOT NULL,
    tipo_manutencao VARCHAR(50) NOT NULL,
    tipo_parada VARCHAR(50) NOT NULL,
    equipamento_id INT NOT NULL,
    motivo TEXT NOT NULL,
    mecanico_id INT,
    data_inicio DATETIME NOT NULL,
    data_inicio_execucao DATETIME,
    data_termino DATETIME,
    status VARCHAR(20) DEFAULT 'Aberta',
    sap VARCHAR(50),
    tempo_manutencao FLOAT,
    descricao_servico TEXT,         -- Coluna adicionada
    materiais_utilizados TEXT,      -- Coluna adicionada
    fotos_paths JSON,               -- Coluna adicionada (assumindo tipo JSON)
    graxa_oleo BOOLEAN,             -- Coluna adicionada
    limpeza BOOLEAN,                -- Coluna adicionada
    pecas_soltas BOOLEAN,           -- Coluna adicionada
    equipamento_liberado BOOLEAN,   -- Coluna adicionada
    nome_mecanico VARCHAR(100),     -- Coluna adicionada
    nome_conferente VARCHAR(100),   -- Coluna adicionada
    assinatura_mecanico TEXT NULL,
    assinatura_conferente TEXT NULL,
    data_assinatura_mecanico DATETIME NULL,
    data_assinatura_conferente DATETIME NULL,
    FOREIGN KEY (localizacao_id) REFERENCES localizacoes(id),
    FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id),
    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
);

-- Inserir usuário admin padrão
-- Senha: admin123 (hash gerado com werkzeug.security.generate_password_hash)
INSERT INTO users (username, email, password_hash, role) VALUES 
('admin', 'admin@admin.com', 'scrypt:32768:8:1$Sto5g6Q1OiXS3fEi$b2c9798a905a744f37578bcb20f49d3d4398660229c29a6aa589643e426b049dfb5942f1d784307125607bc913648ef428a8c558cbaa5db26f5a3456e6a27960', 'admin')
ON DUPLICATE KEY UPDATE 
username = VALUES(username),
email = VALUES(email),
role = VALUES(role);
