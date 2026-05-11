CREATE EXTENSION IF NOT EXISTS postgis;
-- =============================================================================
-- 0. XÓA BẢNG CŨ (thứ tự tránh lỗi FK)
-- =============================================================================
DROP TABLE IF EXISTS maintenance        CASCADE;
DROP TABLE IF EXISTS incident           CASCADE;
DROP TABLE IF EXISTS incident_type      CASCADE;
DROP TABLE IF EXISTS asset              CASCADE;
DROP TABLE IF EXISTS equipment          CASCADE;
DROP TABLE IF EXISTS tree               CASCADE;
DROP TABLE IF EXISTS room               CASCADE;
DROP TABLE IF EXISTS floor              CASCADE;
DROP TABLE IF EXISTS building           CASCADE;
DROP TABLE IF EXISTS app_user           CASCADE;
DROP TABLE IF EXISTS role               CASCADE;
DROP TABLE IF EXISTS university_branch  CASCADE;

-- =============================================================================
-- 1. university_branch
--    Cột: id, name, description, geom
-- =============================================================================
CREATE TABLE university_branch (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    geom        geometry(Polygon, 4326)
);

-- =============================================================================
-- 2. role
--    Cột: id, name
-- =============================================================================
CREATE TABLE role (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- =============================================================================
-- 3. app_user
--    Cột: id, email, username, password, role_id (FK), university_branch_id (FK)
-- =============================================================================
CREATE TABLE app_user (
    id                   SERIAL PRIMARY KEY,
    email                VARCHAR(254) NOT NULL UNIQUE,
    username             VARCHAR(150) NOT NULL UNIQUE,
    password             VARCHAR(128) NOT NULL,
    role_id              INTEGER NOT NULL REFERENCES role(id) ON DELETE RESTRICT,
    university_branch_id INTEGER      REFERENCES university_branch(id) ON DELETE SET NULL
);

-- =============================================================================
-- 4. building
--    Cột: id, name, description, geom, university_branch_id (FK)
-- =============================================================================
CREATE TABLE building (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(200) NOT NULL,
    description          TEXT,
    university_branch_id INTEGER NOT NULL REFERENCES university_branch(id) ON DELETE CASCADE,
    geom                 geometry(Polygon, 4326)
);

-- =============================================================================
-- 5. floor
--    Cột: id, name, level, description, building_id (FK)
-- =============================================================================
CREATE TABLE floor (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    level       INTEGER      NOT NULL DEFAULT 0,
    description TEXT,
    building_id INTEGER NOT NULL REFERENCES building(id) ON DELETE CASCADE
);

-- =============================================================================
-- 6. room
--    Cột: id, name, room_type, capacity,
--         blueprint_url, blueprint_width, blueprint_height,
--         geom, floor_id (FK)
-- =============================================================================
CREATE TABLE room (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    room_type        VARCHAR(50)  NOT NULL,  -- 'office','classroom','lab','hall','library'
    capacity         INTEGER,
    blueprint_url    TEXT,                   -- URL ảnh mặt bằng phòng
    blueprint_width  NUMERIC(10,2),          -- Chiều rộng thực tế (m)
    blueprint_height NUMERIC(10,2),          -- Chiều cao thực tế (m)
    geom             geometry(Polygon, 4326),
    floor_id         INTEGER NOT NULL REFERENCES floor(id) ON DELETE CASCADE
);

-- =============================================================================
-- 7. equipment
--    Cột: id, code, name, equipment_type, status,
--         install_date, last_maintenance,
--         local_x, local_y,  <-- tọa độ trên blueprint
--         geom,              <-- tọa độ địa lý thực
--         room_id (FK)
-- =============================================================================
CREATE TABLE equipment (
    id               SERIAL PRIMARY KEY,
    code             VARCHAR(100) NOT NULL UNIQUE,
    name             VARCHAR(200) NOT NULL,
    equipment_type   VARCHAR(100),
    status           VARCHAR(50)  NOT NULL DEFAULT 'good', -- 'good','maintenance','broken'
    install_date     DATE,
    last_maintenance DATE,
    local_x          NUMERIC(10,4),
    local_y          NUMERIC(10,4),
    geom             geometry(Point, 4326),
    room_id          INTEGER REFERENCES room(id) ON DELETE SET NULL
);

-- =============================================================================
-- 8. tree
--    Cột: id, code, species, height, health_status,
--         planted_date, last_trimmed,
--         local_x, local_y,
--         geom,
--         university_branch_id (FK)
-- =============================================================================
CREATE TABLE tree (
    id                   SERIAL PRIMARY KEY,
    code                 VARCHAR(100) NOT NULL UNIQUE,
    species              VARCHAR(200),
    height               NUMERIC(6,2),
    health_status        VARCHAR(50)  NOT NULL DEFAULT 'good', -- 'good','diseased','dangerous'
    planted_date         DATE,
    last_trimmed         DATE,
    local_x              NUMERIC(10,4),
    local_y              NUMERIC(10,4),
    geom                 geometry(Point, 4326),
    university_branch_id INTEGER NOT NULL REFERENCES university_branch(id) ON DELETE CASCADE
);

-- =============================================================================
-- 9. asset
--    Bảng trung gian thống nhất Equipment & Tree.
--    Ràng buộc độc quyền: equipment_id XOR tree_id
-- =============================================================================
CREATE TABLE asset (
    id           SERIAL PRIMARY KEY,
    asset_type   VARCHAR(20) NOT NULL CHECK (asset_type IN ('equipment','tree')),
    equipment_id INTEGER UNIQUE REFERENCES equipment(id) ON DELETE CASCADE,
    tree_id      INTEGER UNIQUE REFERENCES tree(id)      ON DELETE CASCADE,

    CONSTRAINT chk_asset_exclusive CHECK (
        (asset_type = 'equipment' AND equipment_id IS NOT NULL AND tree_id IS NULL)
        OR
        (asset_type = 'tree'      AND tree_id IS NOT NULL      AND equipment_id IS NULL)
    )
);

-- =============================================================================
-- 10. incident_type
--     Cột: id, code, name, description, default_severity, applies_to
-- =============================================================================
CREATE TABLE incident_type (
    id               SERIAL PRIMARY KEY,
    code             VARCHAR(100) NOT NULL UNIQUE,
    name             VARCHAR(200) NOT NULL,
    description      TEXT,
    default_severity INTEGER NOT NULL DEFAULT 1 CHECK (default_severity BETWEEN 1 AND 5),
    applies_to       TEXT[]   -- Ví dụ: '{equipment}', '{tree}', '{facility,security}'
);

-- =============================================================================
-- 11. incident
--     Cột: id, title, description, reported_at, status, priority, geom,
--          incident_type_id (FK), asset_id (FK),
--          building_id (FK), room_id (FK)
-- =============================================================================
CREATE TABLE incident (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(300) NOT NULL,
    description      TEXT,
    reported_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    status           VARCHAR(50) NOT NULL DEFAULT 'open',   -- 'open','processing','resolved','closed'
    priority         VARCHAR(20) NOT NULL DEFAULT 'medium', -- 'low','medium','high','critical'
    geom             geometry(Point, 4326),
    incident_type_id INTEGER NOT NULL REFERENCES incident_type(id) ON DELETE RESTRICT,
    asset_id         INTEGER      REFERENCES asset(id)          ON DELETE SET NULL,
    building_id      INTEGER      REFERENCES building(id)       ON DELETE SET NULL,
    room_id          INTEGER      REFERENCES room(id)           ON DELETE SET NULL
);

-- =============================================================================
-- 12. maintenance
--     Cột: id, maintenance_type, maintenance_date, cost, note,
--          local_x, local_y,  <-- vị trí ghi nhận trên blueprint
--          asset_id (FK), staff_id (FK → app_user)
-- =============================================================================
CREATE TABLE maintenance (
    id               SERIAL PRIMARY KEY,
    maintenance_type VARCHAR(50)    NOT NULL, -- 'inspection','repair','replacement','trim','cleaning'
    maintenance_date DATE           NOT NULL DEFAULT CURRENT_DATE,
    cost             NUMERIC(15,2)  DEFAULT 0,
    note             TEXT,
    local_x          NUMERIC(10,4),
    local_y          NUMERIC(10,4),
    asset_id         INTEGER NOT NULL REFERENCES asset(id)     ON DELETE CASCADE,
    staff_id         INTEGER NOT NULL REFERENCES app_user(id)  ON DELETE RESTRICT
);

-- =============================================================================
-- INDEX hỗ trợ truy vấn không gian
-- =============================================================================
CREATE INDEX idx_university_branch_geom ON university_branch USING GIST (geom);
CREATE INDEX idx_building_geom          ON building           USING GIST (geom);
CREATE INDEX idx_room_geom              ON room               USING GIST (geom);
CREATE INDEX idx_equipment_geom         ON equipment          USING GIST (geom);
CREATE INDEX idx_tree_geom              ON tree               USING GIST (geom);
CREATE INDEX idx_incident_geom          ON incident           USING GIST (geom);

-- =============================================================================
-- DỮ LIỆU MẪU
-- =============================================================================

-- 1. ROLE
INSERT INTO role (id, name) VALUES
(1, 'admin'),
(2, 'giảng viên'),
(3, 'nhân viên CSVC');

-- 2. UNIVERSITY_BRANCH
INSERT INTO university_branch (id, name, description, geom) VALUES
(1, 'Cơ sở Lê Văn Sỹ',
   '236B Lê Văn Sỹ, Phường 1, Tân Bình, TP.HCM',
   ST_GeomFromText('POLYGON((106.663 10.795, 106.665 10.795, 106.665 10.793, 106.663 10.793, 106.663 10.795))', 4326)),
(2, 'Cơ sở Nhà Bè',
   'Đường Huỳnh Tấn Phát, Huyện Nhà Bè, TP.HCM',
   ST_GeomFromText('POLYGON((106.750 10.688, 106.755 10.688, 106.755 10.685, 106.750 10.685, 106.750 10.688))', 4326));

-- 3. APP_USER (password mặc định: 123456 — hash Django pbkdf2_sha256)
INSERT INTO app_user (id, email, username, password, role_id, university_branch_id) VALUES
(1, 'admin@hcmunre.edu.vn',        'admin_tong', 'pbkdf2_sha256$600000$abc123$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 1, NULL),
(2, 'gv.nguyenvana@hcmunre.edu.vn','nguyenvana', 'pbkdf2_sha256$600000$abc123$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 2, 1),
(3, 'gv.tranbath@hcmunre.edu.vn',  'tranbath',   'pbkdf2_sha256$600000$abc123$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 2, 2),
(4, 'csvc.lethic@hcmunre.edu.vn',  'lethic',     'pbkdf2_sha256$600000$abc123$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 3, 1),
(5, 'csvc.phamvand@hcmunre.edu.vn','phamvand',   'pbkdf2_sha256$600000$abc123$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=', 3, 2);

-- 4. BUILDING
INSERT INTO building (id, name, description, university_branch_id, geom) VALUES
(1, 'Tòa nhà A - LVS',             'Khu hành chính và văn phòng khoa', 1,
   ST_GeomFromText('POLYGON((106.6635 10.7945, 106.6640 10.7945, 106.6640 10.7940, 106.6635 10.7940, 106.6635 10.7945))', 4326)),
(2, 'Tòa nhà B - LVS',             'Khu giảng đường lý thuyết',        1,
   ST_GeomFromText('POLYGON((106.6642 10.7945, 106.6647 10.7945, 106.6647 10.7940, 106.6642 10.7940, 106.6642 10.7945))', 4326)),
(3, 'Tòa nhà Trung Tâm - Nhà Bè',  'Khu học tập đa chức năng',         2,
   ST_GeomFromText('POLYGON((106.751 10.687, 106.752 10.687, 106.752 10.686, 106.751 10.686, 106.751 10.687))', 4326)),
(4, 'Tòa nhà Thực hành - Nhà Bè',  'Hệ thống phòng Lab và thực hành',  2,
   ST_GeomFromText('POLYGON((106.753 10.687, 106.754 10.687, 106.754 10.686, 106.753 10.686, 106.753 10.687))', 4326));

-- 5. FLOOR
INSERT INTO floor (id, name, level, description, building_id) VALUES
(1, 'Tầng Trệt A',  0, 'Sảnh lễ tân và phòng đào tạo',  1),
(2, 'Tầng 1 A',     1, 'Văn phòng các khoa',             1),
(3, 'Tầng 1 B',     1, 'Giảng đường',                    2),
(4, 'Tầng 2 B',     2, 'Giảng đường lớn',                2),
(5, 'Tầng Trệt TT', 0, 'Sảnh sinh viên Nhà Bè',          3),
(6, 'Tầng 1 TT',    1, 'Khu học lý thuyết',               3),
(7, 'Tầng 1 TH',    1, 'Phòng Lab Hóa - Sinh',            4),
(8, 'Tầng 2 TH',    2, 'Phòng Lab GIS & IT',              4);

-- 6. ROOM
INSERT INTO room (id, name, room_type, capacity, blueprint_url, blueprint_width, blueprint_height, geom, floor_id) VALUES
(1, 'Phòng A001',        'office',    10,  NULL, 12.0,  8.0,  ST_GeomFromText('POLYGON((106.6636 10.7944, 106.6637 10.7944, 106.6637 10.7943, 106.6636 10.7943, 106.6636 10.7944))', 4326), 1),
(2, 'Phòng Khoa CNTT',   'office',    20,  NULL, 15.0,  10.0, NULL, 2),
(3, 'Phòng B101',        'classroom', 60,  NULL, 20.0,  15.0, NULL, 3),
(4, 'Phòng B102',        'classroom', 60,  NULL, 20.0,  15.0, NULL, 3),
(5, 'Hội trường B201',   'hall',      200, NULL, 40.0,  25.0, NULL, 4),
(6, 'Thư viện cơ sở 2',  'library',   150, NULL, 30.0,  20.0, NULL, 5),
(7, 'Phòng Lab C101',    'lab',       40,  NULL, 18.0,  12.0, NULL, 7),
(8, 'Phòng Lab GIS C202','lab',       35,  NULL, 18.0,  12.0, NULL, 8);

-- 7. EQUIPMENT
INSERT INTO equipment (id, code, name, equipment_type, status, install_date, last_maintenance, local_x, local_y, geom, room_id) VALUES
(1, 'MAYCHIEU_B101',   'Máy chiếu Panasonic',   'Máy chiếu',    'good',        '2023-01-15', '2025-06-01', 5.0,  2.5,  ST_GeomFromText('POINT(106.6643 10.7944)', 4326), 3),
(2, 'ML_B101_1',       'Máy lạnh Daikin 2HP',   'Máy lạnh',     'good',        '2023-01-15', '2025-12-01', 1.0,  3.0,  ST_GeomFromText('POINT(106.6644 10.7944)', 4326), 3),
(3, 'ML_B101_2',       'Máy lạnh Daikin 2HP',   'Máy lạnh',     'maintenance', '2023-01-15', '2025-12-01', 19.0, 3.0,  NULL,                                              3),
(4, 'MAYCHIEU_B102',   'Máy chiếu Sony',        'Máy chiếu',    'broken',      '2022-09-01', NULL,         5.0,  2.5,  NULL,                                              4),
(5, 'PC_LAB_C202_01',  'Máy tính Dell Optiplex','Máy tính bàn', 'good',        '2024-02-10', '2026-03-15', 2.0,  2.0,  ST_GeomFromText('POINT(106.7535 10.6865)', 4326),  8),
(6, 'PC_LAB_C202_02',  'Máy tính Dell Optiplex','Máy tính bàn', 'good',        '2024-02-10', '2026-03-15', 4.0,  2.0,  NULL,                                              8),
(7, 'MIC_B201',        'Micro không dây',        'Âm thanh',     'good',        '2023-05-20', NULL,         NULL, NULL, NULL,                                              5);

-- 8. TREE
INSERT INTO tree (id, code, species, height, health_status, planted_date, last_trimmed, local_x, local_y, geom, university_branch_id) VALUES
(1, 'CAY_LVS_001', 'Cây Bàng Đài Loan', 5.5,  'good',      '2015-06-01', '2025-11-20', NULL, NULL, ST_GeomFromText('POINT(106.6632 10.7948)', 4326), 1),
(2, 'CAY_LVS_002', 'Cây Phượng Vĩ',     8.2,  'diseased',  '2010-09-05', NULL,         NULL, NULL, ST_GeomFromText('POINT(106.6648 10.7941)', 4326), 1),
(3, 'CAY_NB_001',  'Cây Lộc Vừng',      4.0,  'good',      '2020-11-20', NULL,         NULL, NULL, ST_GeomFromText('POINT(106.7505 10.6875)', 4326), 2),
(4, 'CAY_NB_002',  'Cây Xà Cừ',         12.0, 'dangerous', '2005-01-15', NULL,         NULL, NULL, ST_GeomFromText('POINT(106.7555 10.6855)', 4326), 2);

-- 9. ASSET (equipment trước, tree sau)
INSERT INTO asset (id, asset_type, equipment_id, tree_id) VALUES
(1,  'equipment', 1, NULL),
(2,  'equipment', 2, NULL),
(3,  'equipment', 3, NULL),
(4,  'equipment', 4, NULL),
(5,  'equipment', 5, NULL),
(6,  'equipment', 6, NULL),
(7,  'equipment', 7, NULL),
(8,  'tree', NULL, 1),
(9,  'tree', NULL, 2),
(10, 'tree', NULL, 3),
(11, 'tree', NULL, 4);

-- 10. INCIDENT_TYPE
INSERT INTO incident_type (id, code, name, description, default_severity, applies_to) VALUES
(1, 'HONG_THIET_BI', 'Hỏng thiết bị điện tử',      'Lỗi không lên nguồn, hư hỏng linh kiện',   3, '{equipment}'),
(2, 'CAY_NGA_DO',    'Cây có nguy cơ ngã đổ',       'Cành mục, rễ trốc cần xử lý gấp',          5, '{tree}'),
(3, 'HU_DIEU_HOA',   'Hỏng máy lạnh / Điều hòa',   'Chảy nước, không mát',                      3, '{equipment,facility}'),
(4, 'AN_NINH',       'Mất cắp / Phá hoại',           'Cửa bị phá, mất tài sản',                   4, '{facility,security}');

-- 11. INCIDENT
INSERT INTO incident (id, title, description, reported_at, status, priority, geom, incident_type_id, asset_id, building_id, room_id) VALUES
(1, 'Máy chiếu B102 không lên hình',
   'Giảng viên cắm cáp nhưng máy báo No Signal',
   '2026-04-10 08:30:00', 'open',       'high',   NULL,
   1, 4, 2, 4),
(2, 'Máy lạnh chảy nước xuống bàn',
   'Máy lạnh B101 rỉ nước ướt hết bàn sinh viên',
   '2026-04-12 14:00:00', 'processing', 'medium', NULL,
   3, 3, 2, 3),
(3, 'Cây phượng vĩ mục cành lớn',
   'Nhánh cây lớn có dấu hiệu gãy đứt ngang',
   '2026-04-14 09:00:00', 'open',       'high',
   ST_GeomFromText('POINT(106.6648 10.7941)', 4326),
   2, 9, NULL, NULL);

-- 12. MAINTENANCE
INSERT INTO maintenance (id, maintenance_type, maintenance_date, cost, note, local_x, local_y, asset_id, staff_id) VALUES
(1, 'inspection', '2025-12-01', 150000.00, 'Vệ sinh lưới lọc máy lạnh định kỳ',    1.0,  3.0,  2,  4),
(2, 'repair',     '2026-03-15', 500000.00, 'Thay RAM mới cho PC Lab',               2.0,  2.0,  5,  5),
(3, 'trim',       '2025-11-20', 1200000.00,'Cắt tỉa nhánh cây Bàng phòng mùa mưa', NULL, NULL, 8,  4);

-- =============================================================================
-- ĐỒNG BỘ SEQUENCE (tránh lỗi ID khi INSERT mới qua Django Admin)
-- =============================================================================
SELECT setval('role_id_seq',              (SELECT MAX(id) FROM role));
SELECT setval('university_branch_id_seq', (SELECT MAX(id) FROM university_branch));
SELECT setval('app_user_id_seq',          (SELECT MAX(id) FROM app_user));
SELECT setval('building_id_seq',          (SELECT MAX(id) FROM building));
SELECT setval('floor_id_seq',             (SELECT MAX(id) FROM floor));
SELECT setval('room_id_seq',              (SELECT MAX(id) FROM room));
SELECT setval('equipment_id_seq',         (SELECT MAX(id) FROM equipment));
SELECT setval('tree_id_seq',              (SELECT MAX(id) FROM tree));
SELECT setval('asset_id_seq',             (SELECT MAX(id) FROM asset));
SELECT setval('incident_type_id_seq',     (SELECT MAX(id) FROM incident_type));
SELECT setval('incident_id_seq',          (SELECT MAX(id) FROM incident));
SELECT setval('maintenance_id_seq',       (SELECT MAX(id) FROM maintenance));