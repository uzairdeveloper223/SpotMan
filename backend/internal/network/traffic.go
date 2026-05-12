package network

import (
	"fmt"
)

type TrafficManager struct {
	runner Runner
}

func NewTrafficManager(runner Runner) *TrafficManager {
	return &TrafficManager{runner: runner}
}

func (m *TrafficManager) SetupRoot(iface string) error {
	_, err := m.runner.Execute("tc", "qdisc", "add", "dev", iface, "root", "handle", "1:", "htb", "default", "10")
	return err
}

func (m *TrafficManager) LimitClient(iface, ip string, rateKbps int) error {
	// Example: tc class add dev wlan0 parent 1: classid 1:1 htb rate 1024kbps
	// tc filter add dev wlan0 protocol ip parent 1:0 prio 1 u32 match ip dst 192.168.1.5 flowid 1:1
	
	classID := "1:100" // Should be dynamic based on IP or a map
	_, err := m.runner.Execute("tc", "class", "add", "dev", iface, "parent", "1:", "classid", classID, "htb", "rate", fmt.Sprintf("%dkbit", rateKbps))
	if err != nil {
		return err
	}

	_, err = m.runner.Execute("tc", "filter", "add", "dev", iface, "protocol", "ip", "parent", "1:0", "prio", "1", "u32", "match", "ip", "dst", ip, "flowid", classID)
	return err
}

func (m *TrafficManager) Clear(iface string) error {
	_, err := m.runner.Execute("tc", "qdisc", "del", "dev", iface, "root")
	return err
}
