package network

import (
	"fmt"
	"os/exec"
	"sync"
)

type HotspotManager struct {
	runner       Runner
	hostapdCmd   *exec.Cmd
	dnsmasqCmd   *exec.Cmd
	mu           sync.Mutex
	configPath   string
	dnsmasqPath  string
}

func NewHotspotManager(runner Runner) *HotspotManager {
	return &HotspotManager{
		runner:      runner,
		configPath:  "/tmp/hostapd.conf",
		dnsmasqPath: "/tmp/dnsmasq.conf",
	}
}

func (m *HotspotManager) Start(hCfg HotspotConfig, dCfg DHCPConfig) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.hostapdCmd != nil || m.dnsmasqCmd != nil {
		return fmt.Errorf("hotspot already running")
	}

	if err := GenerateHostapdConfig(hCfg, m.configPath); err != nil {
		return err
	}
	if err := GenerateDnsmasqConfig(dCfg, m.dnsmasqPath); err != nil {
		return err
	}

	// Unblock wifi
	if _, err := m.runner.Execute("rfkill", "unblock", "wifi"); err != nil {
		return err
	}

	// Set IP for LAN interface
	if _, err := m.runner.Execute("ip", "addr", "add", dCfg.Gateway+"/24", "dev", hCfg.Interface); err != nil {
		// Ignore if already set
	}
	if _, err := m.runner.Execute("ip", "link", "set", hCfg.Interface, "up"); err != nil {
		return err
	}

	// Start dnsmasq
	m.dnsmasqCmd = exec.Command("sudo", "dnsmasq", "-C", m.dnsmasqPath, "-d")
	if err := m.dnsmasqCmd.Start(); err != nil {
		return fmt.Errorf("failed to start dnsmasq: %v", err)
	}

	// Start hostapd
	m.hostapdCmd = exec.Command("sudo", "hostapd", m.configPath)
	if err := m.hostapdCmd.Start(); err != nil {
		m.dnsmasqCmd.Process.Kill()
		m.dnsmasqCmd = nil
		return fmt.Errorf("failed to start hostapd: %v", err)
	}

	return nil
}

func (m *HotspotManager) Stop() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.hostapdCmd != nil {
		m.runner.Execute("pkill", "hostapd")
		m.hostapdCmd = nil
	}
	if m.dnsmasqCmd != nil {
		m.runner.Execute("pkill", "dnsmasq")
		m.dnsmasqCmd = nil
	}

	return nil
}
