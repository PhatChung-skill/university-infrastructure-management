CREATE TABLE building (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    geom GEOMETRY(POLYGON, 4326)
);


--Bảng phòng học/lab/thư viện
	
	CREATE TABLE room (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    room_type TEXT CHECK (room_type IN ('classroom', 'lab', 'library', 'office', 'hall')),
    capacity INT,
    building_id INT REFERENCES building(id),
    geom GEOMETRY(POINT, 4326)
);


--Bảng cây cối

	CREATE TABLE tree (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    species TEXT,                	-- loại cây
    height NUMERIC,              -- chiều cao (m)
    health_status TEXT CHECK (
        health_status IN ('good', 'diseased', 'dangerous')
    ),
    planted_date DATE,
    last_trimmed DATE,
    note TEXT,
    geom GEOMETRY(POINT, 4326)
);


--Bảng equipment
	
	CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    name TEXT,
    equipment_type TEXT,
    status TEXT CHECK (status IN ('good', 'broken', 'maintenance')),
    install_date DATE,
    last_maintenance DATE,
    room_id INT REFERENCES room(id),
    geom GEOMETRY(POINT, 4326)
);


--Bảng sự cố

CREATE TABLE incident (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    reported_at TIMESTAMP DEFAULT now(),
    status TEXT CHECK (status IN ('open', 'processing', 'closed')),
    asset_id INT REFERENCES asset(id),
    priority TEXT CHECK (priority IN ('low','medium','high')),
    incident_type_id INT REFERENCES incident_type(id),
    geom GEOMETRY(POINT, 4326)
);
	
--Bảng loại sự cố

CREATE TABLE incident_type (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    default_severity INT CHECK (default_severity BETWEEN 1 AND 5)
);



--Bảng tài sản 

CREATE TABLE asset (
    id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(id),
   asset_type TEXT CHECK (asset_type IN ('equipment', 'tree')),
    tree_id INT REFERENCES tree(id),
    CHECK (
        (equipment_id IS NOT NULL AND tree_id IS NULL)
     OR (equipment_id IS NULL AND tree_id IS NOT NULL)
    )
);





--Bảng bảo trì/sửa chữa (lịch sử)

CREATE TABLE maintenance (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES asset(id),
    staff_id INT REFERENCES app_user(id),
    maintenance_type TEXT CHECK (maintenance_type IN ('repair','inspection','trim','replace'))
    maintenance_date DATE,
    cost NUMERIC,
    note TEXT
);



--Bảng vai trò

	CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

--Bảng người dùng
CREATE TABLE app_user (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role_id INT REFERENCES role(id)
);



--Đánh truy vấn để thực hiện truy vấn trên bản đồ.

CREATE INDEX idx_building_geom ON building USING GIST (geom);
CREATE INDEX idx_room_geom ON room USING GIST (geom);
CREATE INDEX idx_tree_geom ON tree USING GIST (geom);
CREATE INDEX idx_equipment_geom ON equipment USING GIST (geom);
CREATE INDEX idx_incident_geom ON incident USING GIST (geom);



-- 2. TẠO APP_USER (Nhân viên & Giảng viên)
INSERT INTO home_appuser (username, password, role_id)
SELECT 
    'user_hcmunre_' || i, 
    '123',
    CASE 
        WHEN i <= 5 THEN floor(random() * 2 + 1) -- Role 1,2: Quản lý
        ELSE 3 -- Role 3: Giảng viên
    END
FROM generate_series(1, 20) AS i;

-- 3. TẠO BUILDING (Các tòa nhà tại HCMUNRE - Lê Văn Sỹ)
-- Tọa độ trung tâm: 10.7984, 106.6655
INSERT INTO home_building (name, description, geom) VALUES 
('Nhà A - Hiệu bộ', 'Phòng Ban Giám hiệu, Hành chính', ST_GeomFromText('POLYGON((106.6652 10.7988, 106.6658 10.7988, 106.6658 10.7992, 106.6652 10.7992, 106.6652 10.7988))', 4326)),
('Nhà B - Giảng đường', 'Khu giảng đường chính sinh viên', ST_GeomFromText('POLYGON((106.6648 10.7982, 106.6655 10.7982, 106.6655 10.7986, 106.6648 10.7986, 106.6648 10.7982))', 4326)),
('Nhà C - Thí nghiệm', 'Phòng Lab Hóa - Môi trường', ST_GeomFromText('POLYGON((106.6656 10.7980, 106.6660 10.7980, 106.6660 10.7985, 106.6656 10.7985, 106.6656 10.7980))', 4326)),
('Thư viện', 'Trung tâm thông tin thư viện', ST_GeomFromText('POLYGON((106.6660 10.7988, 106.6664 10.7988, 106.6664 10.7991, 106.6660 10.7991, 106.6660 10.7988))', 4326)),
('Hội trường', 'Nơi tổ chức sự kiện', ST_GeomFromText('POLYGON((106.6645 10.7988, 106.6650 10.7988, 106.6650 10.7990, 106.6645 10.7990, 106.6645 10.7988))', 4326));

-- 4. TẠO 20 ROOM (Phòng học)
-- Random tọa độ nằm đè lên các tòa nhà trên
INSERT INTO home_room (name, room_type, capacity, building_id, geom)
SELECT 
    'Phòng ' || (CASE WHEN i < 10 THEN 'B' ELSE 'C' END) || (100 + i),
    (ARRAY['classroom', 'lab', 'library', 'office', 'hall'])[floor(random() * 5 + 1)],
    floor(random() * 80 + 30),
    floor(random() * 5 + 1), -- Gán vào 5 tòa nhà trên
    ST_SetSRID(ST_MakePoint(106.6648 + (random() * 0.0015), 10.7980 + (random() * 0.0010)), 4326)
FROM generate_series(1, 20) AS i;

-- 5. TẠO 20 TREE (Cây xanh trong sân trường)
INSERT INTO home_tree (code, species, height, health_status, planted_date, geom)
SELECT 
    'TREE-' || lpad(i::text, 3, '0'),
    (ARRAY['Bàng', 'Sao Đen', 'Phượng', 'Lộc Vừng', 'Me Tây'])[floor(random() * 5 + 1)],
    (random() * 10 + 2)::numeric(5,2),
    (ARRAY['good', 'good', 'diseased', 'dangerous'])[floor(random() * 4 + 1)],
    CURRENT_DATE - (floor(random() * 2000) || ' days')::interval,
    ST_SetSRID(ST_MakePoint(106.6645 + (random() * 0.0020), 10.7980 + (random() * 0.0015)), 4326)
FROM generate_series(1, 20) AS i;

-- 6. TẠO 20 EQUIPMENT (Thiết bị)
INSERT INTO home_equipment (code, name, equipment_type, status, install_date, room_id, geom)
SELECT 
    'EQ-' || lpad(i::text, 3, '0'),
    (ARRAY['Máy chiếu', 'PC', 'Điều hòa', 'Loa', 'Wifi'])[floor(random() * 5 + 1)] || ' #' || i,
    (ARRAY['Máy chiếu', 'Máy tính', 'Điều hòa', 'Âm thanh', 'Mạng'])[floor(random() * 5 + 1)],
    (ARRAY['good', 'good', 'broken', 'maintenance'])[floor(random() * 4 + 1)],
    CURRENT_DATE - (floor(random() * 1000) || ' days')::interval,
    floor(random() * 20 + 1), -- Gán vào Room ID 1-20
    ST_SetSRID(ST_MakePoint(106.6648 + (random() * 0.0015), 10.7980 + (random() * 0.0010)), 4326)
FROM generate_series(1, 20) AS i;

-- 7. TẠO ASSET (Tài sản - Logic 40 dòng để bao phủ 20 Cây + 20 Thiết bị)
-- 20 dòng đầu cho Equipment
INSERT INTO home_asset (asset_type, equipment_id, tree_id)
SELECT 'equipment', i, NULL FROM generate_series(1, 20) AS i;
-- 20 dòng sau cho Tree
INSERT INTO home_asset (asset_type, equipment_id, tree_id)
SELECT 'tree', NULL, i FROM generate_series(1, 20) AS i;

-- 8. TẠO 20 INCIDENT (Sự cố)
-- Random tọa độ sự cố trùng vào khu vực trường
INSERT INTO home_incident (title, description, status, priority, incident_type_id, asset_id, reported_at, geom)
SELECT 
    'Sự cố số ' || i,
    'Mô tả chi tiết...',
    (ARRAY['open', 'processing', 'closed'])[floor(random() * 3 + 1)],
    (ARRAY['low', 'medium', 'high'])[floor(random() * 3 + 1)],
    floor(random() * 4 + 1), -- IncidentType ID 1-4 (Giả định bảng này đã có dữ liệu)
    floor(random() * 40 + 1), -- Asset ID 1-40
    NOW() - (floor(random() * 30) || ' days')::interval,
    ST_SetSRID(ST_MakePoint(106.6645 + (random() * 0.0020), 10.7980 + (random() * 0.0015)), 4326)
FROM generate_series(1, 20) AS i;

-- 9. TẠO MAINTENANCE (Bảo trì)
INSERT INTO home_maintenance (asset_id, staff_id, maintenance_type, maintenance_date, cost, note)
SELECT 
    floor(random() * 40 + 1),
    floor(random() * 5 + 1), -- Staff ID 1-5
    (ARRAY['repair', 'inspection', 'trim', 'replace'])[floor(random() * 4 + 1)],
    CURRENT_DATE - (floor(random() * 365) || ' days')::interval,
    (random() * 5000000 + 100000)::numeric(10,2),
    'Đã xử lý'
FROM generate_series(1, 20) AS i;

-- RESET ID SEQUENCE (Để tránh lỗi Duplicate ID khi thêm mới)
SELECT setval(pg_get_serial_sequence('home_appuser', 'id'), (SELECT MAX(id) FROM home_appuser));
SELECT setval(pg_get_serial_sequence('home_building', 'id'), (SELECT MAX(id) FROM home_building));
SELECT setval(pg_get_serial_sequence('home_room', 'id'), (SELECT MAX(id) FROM home_room));
SELECT setval(pg_get_serial_sequence('home_tree', 'id'), (SELECT MAX(id) FROM home_tree));
SELECT setval(pg_get_serial_sequence('home_equipment', 'id'), (SELECT MAX(id) FROM home_equipment));
SELECT setval(pg_get_serial_sequence('home_asset', 'id'), (SELECT MAX(id) FROM home_asset));
SELECT setval(pg_get_serial_sequence('home_incident', 'id'), (SELECT MAX(id) FROM home_incident));
SELECT setval(pg_get_serial_sequence('home_maintenance', 'id'), (SELECT MAX(id) FROM home_maintenance));

COMMIT;

select * from home_appuser

