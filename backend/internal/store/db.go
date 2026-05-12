package store

import (
	"database/sql"
	_ "github.com/mattn/go-sqlite3"
	"time"
)

type Store struct {
	db *sql.DB
}

type DeviceLog struct {
	ID        int
	MAC       string
	IP        string
	Action    string
	Timestamp time.Time
}

func NewStore(dbPath string) (*Store, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	schema := `
	CREATE TABLE IF NOT EXISTS devices (
		mac TEXT PRIMARY KEY,
		hostname TEXT,
		last_ip TEXT,
		is_banned BOOLEAN DEFAULT 0,
		is_isolated BOOLEAN DEFAULT 0,
		download_limit_kbps INTEGER DEFAULT 0,
		first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS usage_logs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		mac TEXT,
		bytes_up INTEGER,
		bytes_down INTEGER,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY(mac) REFERENCES devices(mac)
	);

	CREATE TABLE IF NOT EXISTS system_logs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		mac TEXT,
		action TEXT,
		details TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`

	if _, err := db.Exec(schema); err != nil {
		return nil, err
	}

	return &Store{db: db}, nil
}

func (s *Store) LogSystemAction(mac, action, details string) error {
	_, err := s.db.Exec("INSERT INTO system_logs (mac, action, details) VALUES (?, ?, ?)", mac, action, details)
	return err
}

func (s *Store) UpdateDevice(mac, hostname, ip string) error {
	_, err := s.db.Exec(`
		INSERT INTO devices (mac, hostname, last_ip, last_seen) 
		VALUES (?, ?, ?, CURRENT_TIMESTAMP)
		ON CONFLICT(mac) DO UPDATE SET 
			hostname=excluded.hostname, 
			last_ip=excluded.last_ip, 
			last_seen=CURRENT_TIMESTAMP`, mac, hostname, ip)
	return err
}

func (s *Store) SetDeviceBan(mac string, banned bool) error {
	_, err := s.db.Exec("UPDATE devices SET is_banned=? WHERE mac=?", banned, mac)
	return err
}

func (s *Store) SetDeviceIsolation(mac string, isolated bool) error {
	_, err := s.db.Exec("UPDATE devices SET is_isolated=? WHERE mac=?", isolated, mac)
	return err
}

func (s *Store) GetUsageLogs() ([]map[string]interface{}, error) {
	rows, err := s.db.Query(`
		SELECT mac, bytes_up, bytes_down, timestamp 
		FROM usage_logs 
		ORDER BY timestamp DESC LIMIT 1000`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var logs []map[string]interface{}
	for rows.Next() {
		var mac string
		var up, down int64
		var ts string
		rows.Scan(&mac, &up, &down, &ts)
		logs = append(logs, map[string]interface{}{
			"mac":       mac,
			"bytes_up":   up,
			"bytes_down": down,
			"timestamp":  ts,
		})
	}
	return logs, nil
}
