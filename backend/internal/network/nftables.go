package network

import (
	"encoding/json"
	"fmt"
	"strings"
)

type NFTablesManager struct {
	runner Runner
}

func NewNFTablesManager(runner Runner) *NFTablesManager {
	return &NFTablesManager{runner: runner}
}

func (m *NFTablesManager) SetupNAT(wanInterface, lanInterface string) error {
	commands := [][]string{
		{"add", "table", "ip", "spotman"},
		{"add", "chain", "ip", "spotman", "postrouting", "{ type nat hook postrouting priority 100 ; policy accept ; }"},
		{"add", "rule", "ip", "spotman", "postrouting", "oifname", wanInterface, "masquerade"},
		{"add", "chain", "ip", "spotman", "forward", "{ type filter hook forward priority 0 ; policy accept ; }"},
		{"add", "rule", "ip", "spotman", "forward", "iifname", lanInterface, "oifname", wanInterface, "accept"},
		{"add", "rule", "ip", "spotman", "forward", "iifname", wanInterface, "oifname", lanInterface, "ct state established,related accept"},
	}

	for _, args := range commands {
		_, err := m.runner.Execute("nft", args...)
		if err != nil {
			return fmt.Errorf("nft command failed: %v", err)
		}
	}

	// Enable IP forwarding in kernel
	_, err := m.runner.Execute("sysctl", "-w", "net.ipv4.ip_forward=1")
	return err
}

func (m *NFTablesManager) AddDeviceCounter(ip string) error {
	// Add rules to count packets for this IP with comments as labels
	_, err := m.runner.Execute("nft", "add", "rule", "ip", "spotman", "forward", "ip", "saddr", ip, "counter", "comment", fmt.Sprintf("up_%s", ip))
	if err != nil {
		return err
	}
	_, err = m.runner.Execute("nft", "add", "rule", "ip", "spotman", "forward", "ip", "daddr", ip, "counter", "comment", fmt.Sprintf("down_%s", ip))
	return err
}

func (m *NFTablesManager) RedirectTraffic(domainIP, targetIP string) error {
	// Redirect traffic for a specific IP to a local target (e.g., captive portal)
	_, err := m.runner.Execute("nft", "add", "rule", "ip", "spotman", "prerouting", "ip", "daddr", domainIP, "dnat", "to", targetIP)
	return err
}

func (m *NFTablesManager) BanMAC(mac string) error {
	_, err := m.runner.Execute("nft", "add", "rule", "ip", "spotman", "forward", "ether", "saddr", mac, "drop")
	return err
}

func (m *NFTablesManager) IsolateMAC(mac string) error {
	// Cut off internet (WAN) but allow LAN?
	// For full quarantine, drop all from this MAC
	_, err := m.runner.Execute("nft", "add", "rule", "ip", "spotman", "forward", "ether", "saddr", mac, "drop")
	return err
}

func (m *NFTablesManager) Flush() error {
	_, err := m.runner.Execute("nft", "flush", "table", "ip", "spotman")
	return err
}

type NFTOutput struct {
	Nftables []interface{} `json:"nftables"`
}

func (m *NFTablesManager) GetCounters() (map[string]int64, error) {
	out, err := m.runner.Execute("nft", "-j", "list", "table", "ip", "spotman")
	if err != nil {
		return nil, err
	}

	var data NFTOutput
	if err := json.Unmarshal(out, &data); err != nil {
		return nil, err
	}

	counters := make(map[string]int64)
	for _, item := range data.Nftables {
		obj, ok := item.(map[string]interface{})
		if !ok {
			continue
		}

		rule, ok := obj["rule"].(map[string]interface{})
		if !ok {
			continue
		}

		comment, _ := rule["comment"].(string)
		if !strings.Contains(comment, "_") {
			continue
		}

		exprs, ok := rule["expr"].([]interface{})
		if !ok {
			continue
		}

		for _, e := range exprs {
			eObj, ok := e.(map[string]interface{})
			if !ok {
				continue
			}

			if c, ok := eObj["counter"].(map[string]interface{}); ok {
				if b, ok := c["bytes"].(float64); ok {
					counters[comment] = int64(b)
				}
			}
		}
	}

	return counters, nil
}
