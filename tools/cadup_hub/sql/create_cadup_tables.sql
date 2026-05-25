-- CADUP Hub v2 future tables.
-- This script is not executed automatically.

CREATE TABLE IF NOT EXISTS cadup_lotes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    empresa VARCHAR(120) NULL,
    tipo CHAR(1) NULL,
    ddd VARCHAR(2) NULL,
    quantidade_solicitada INT UNSIGNED NOT NULL,
    quantidade_gerada INT UNSIGNED NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'pendente',
    filtros_json JSON NULL,
    created_by VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    PRIMARY KEY (id),
    KEY idx_cadup_lotes_status (status),
    KEY idx_cadup_lotes_empresa_tipo (empresa, tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cadup_numeros_gerados (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    lote_id BIGINT UNSIGNED NULL,
    numero VARCHAR(16) NOT NULL,
    ddd VARCHAR(2) NOT NULL,
    prefixo VARCHAR(5) NOT NULL,
    mcdu VARCHAR(4) NOT NULL,
    operadora VARCHAR(120) NULL,
    tipo CHAR(1) NULL,
    cidade VARCHAR(120) NULL,
    uf CHAR(2) NULL,
    origem VARCHAR(40) NOT NULL DEFAULT 'manual',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_cadup_numeros_gerados_numero (numero),
    KEY idx_cadup_numeros_gerados_lote (lote_id),
    KEY idx_cadup_numeros_gerados_prefixo (ddd, prefixo),
    CONSTRAINT fk_cadup_numeros_lote
        FOREIGN KEY (lote_id) REFERENCES cadup_lotes (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cadup_blocklist (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    numero VARCHAR(16) NULL,
    ddd VARCHAR(2) NULL,
    prefixo VARCHAR(5) NULL,
    mcdu VARCHAR(4) NULL,
    motivo VARCHAR(255) NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_by VARCHAR(120) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_cadup_blocklist_numero (numero),
    KEY idx_cadup_blocklist_prefixo (ddd, prefixo),
    KEY idx_cadup_blocklist_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cadup_audit_log (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    action VARCHAR(80) NOT NULL,
    entity VARCHAR(80) NOT NULL,
    entity_id VARCHAR(80) NULL,
    actor VARCHAR(120) NULL,
    metadata_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_cadup_audit_action (action),
    KEY idx_cadup_audit_entity (entity, entity_id),
    KEY idx_cadup_audit_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
