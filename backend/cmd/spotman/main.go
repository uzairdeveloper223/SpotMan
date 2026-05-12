package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/uzairdeveloper223/spotman/internal/monitor"
	"github.com/uzairdeveloper223/spotman/internal/network"
	"github.com/uzairdeveloper223/spotman/internal/store"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

type Server struct {
	runner  *network.SudoRunner
	nft     *network.NFTablesManager
	hotspot *network.HotspotManager
	traffic *network.TrafficManager
	store   *store.Store
	clients map[*websocket.Conn]bool
	mu      sync.Mutex
}

func main() {
	runner := &network.SudoRunner{}
	nft := network.NewNFTablesManager(runner)
	hotspot := network.NewHotspotManager(runner)
	traffic := network.NewTrafficManager(runner)
	db, err := store.NewStore("spotman.db")
	if err != nil {
		log.Fatal(err)
	}

	srv := &Server{
		runner:  runner,
		nft:     nft,
		hotspot: hotspot,
		traffic: traffic,
		store:   db,
		clients: make(map[*websocket.Conn]bool),
	}

	http.HandleFunc("/ws", srv.handleWS)
	http.HandleFunc("/api/interfaces", srv.handleInterfaces)
	http.HandleFunc("/api/devices", srv.handleDevices)
	http.HandleFunc("/api/hotspot/start", srv.handleStartHotspot)
	http.HandleFunc("/api/hotspot/stop", srv.handleStopHotspot)
	http.HandleFunc("/api/client/ban", srv.handleBanClient)
	http.HandleFunc("/api/client/throttle", srv.handleThrottleClient)
	http.HandleFunc("/api/logs/export", srv.handleExportLogs)
	http.HandleFunc("/", srv.handleRoot)

	// Start monitoring loop
	go srv.monitoringLoop()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("SpotMan backend starting on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func (s *Server) monitoringLoop() {
	for {
		devices, err := monitor.GetConnectedDevices()
		if err == nil {
			counters, _ := s.nft.GetCounters()

			for i := range devices {
				d := &devices[i]
				s.store.UpdateDevice(d.MAC, d.Hostname, d.IP)

				upKey := "up_" + d.IP
				downKey := "down_" + d.IP

				if val, ok := counters[upKey]; ok {
					d.BytesUp = val
				}
				if val, ok := counters[downKey]; ok {
					d.BytesDown = val
				}
			}

			s.broadcast(devices)
		}
		time.Sleep(2 * time.Second)
	}
}

func (s *Server) handleWS(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	s.mu.Lock()
	s.clients[conn] = true
	s.mu.Unlock()
}

func (s *Server) broadcast(data interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	msg, _ := json.Marshal(data)
	for client := range s.clients {
		if err := client.WriteMessage(websocket.TextMessage, msg); err != nil {
			client.Close()
			delete(s.clients, client)
		}
	}
}

func (s *Server) handleDevices(w http.ResponseWriter, r *http.Request) {
	devices, err := monitor.GetConnectedDevices()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(devices)
}

func (s *Server) handleInterfaces(w http.ResponseWriter, r *http.Request) {
	interfaces, err := os.ReadDir("/sys/class/net")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var result []string
	for _, iface := range interfaces {
		name := iface.Name()
		if name != "lo" {
			result = append(result, name)
		}
	}
	json.NewEncoder(w).Encode(result)
}

func (s *Server) handleStartHotspot(w http.ResponseWriter, r *http.Request) {
	var req struct {
		SSID      string   `json:"ssid"`
		Password  string   `json:"password"`
		Channel   int      `json:"channel"`
		Band      string   `json:"band"`
		Interface string   `json:"interface"`
		WAN       string   `json:"wan"`
		Blocked   []string `json:"blocked"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	hCfg := network.HotspotConfig{
		Interface: req.Interface,
		SSID:      req.SSID,
		Password:  req.Password,
		Channel:   req.Channel,
		Band:      req.Band,
	}

	dCfg := network.DHCPConfig{
		Interface:  req.Interface,
		Gateway:    "192.168.12.1",
		RangeStart: "192.168.12.10",
		RangeEnd:   "192.168.12.100",
		DNS:        []string{"8.8.8.8", "1.1.1.1"},
		Blocked:    req.Blocked,
	}

	if err := s.nft.SetupNAT(req.WAN, req.Interface); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if err := s.hotspot.Start(hCfg, dCfg); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	s.store.LogSystemAction("", "HOTSPOT_START", req.SSID)
	w.WriteHeader(http.StatusOK)
}

func (s *Server) handleStopHotspot(w http.ResponseWriter, r *http.Request) {
	if err := s.hotspot.Stop(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	s.nft.Flush()
	s.store.LogSystemAction("", "HOTSPOT_STOP", "")
	w.WriteHeader(http.StatusOK)
}

func (s *Server) handleBanClient(w http.ResponseWriter, r *http.Request) {
	var req struct {
		MAC string `json:"mac"`
	}
	json.NewDecoder(r.Body).Decode(&req)
	s.nft.BanMAC(req.MAC)
	s.store.SetDeviceBan(req.MAC, true)
	s.store.LogSystemAction(req.MAC, "CLIENT_BAN", "")
}

func (s *Server) handleThrottleClient(w http.ResponseWriter, r *http.Request) {
	var req struct {
		IP   string `json:"ip"`
		Rate int    `json:"rate"` // kbps
		Iface string `json:"iface"`
	}
	json.NewDecoder(r.Body).Decode(&req)
	s.traffic.LimitClient(req.Iface, req.IP, req.Rate)
	s.store.LogSystemAction(req.IP, "CLIENT_THROTTLE", fmt.Sprintf("%d", req.Rate))
}

func (s *Server) handleExportLogs(w http.ResponseWriter, r *http.Request) {
	format := r.URL.Query().Get("format")
	logs, err := s.store.GetUsageLogs()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if format == "csv" {
		w.Header().Set("Content-Type", "text/csv")
		w.Header().Set("Content-Disposition", "attachment;filename=usage_logs.csv")
		fmt.Fprintln(w, "MAC,Bytes Up,Bytes Down,Timestamp")
		for _, l := range logs {
			fmt.Fprintf(w, "%s,%v,%v,%s\n", l["mac"], l["bytes_up"], l["bytes_down"], l["timestamp"])
		}
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logs)
}

func (s *Server) handleRoot(w http.ResponseWriter, r *http.Request) {
	// If the host header doesn't match our local IP or localhost,
	// it might be a sinkholed domain.
	// Show a custom "Blocked" page.
	
	html := `<!DOCTYPE html>
<html>
<head>
    <title>Site Blocked - SpotMan</title>
    <style>
        body { background: #111827; color: white; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1f2937; padding: 2rem; rounded: 1rem; border: 1px solid #374151; text-align: center; }
        h1 { color: #ef4444; }
        p { color: #9ca3af; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Access Denied</h1>
        <p>This domain has been blocked by the network administrator via SpotMan.</p>
        <div style="margin-top: 2rem; font-size: 0.8rem; color: #4b5563;">Powered by SpotMan</div>
    </div>
</body>
</html>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}
