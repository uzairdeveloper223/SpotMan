package network

import (
	"fmt"
	"os"
	"path/filepath"
)

type HotspotConfig struct {
	Interface  string
	SSID       string
	Password   string
	Channel    int
	Band       string // "2.4" or "5"
}

func GenerateHostapdConfig(cfg HotspotConfig, path string) error {
	hwMode := "g"
	if cfg.Band == "5" {
		hwMode = "a"
	}

	content := fmt.Sprintf(`interface=%s
driver=nl80211
ssid=%s
hw_mode=%s
channel=%d
wpa=2
wpa_passphrase=%s
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP CCMP
rsn_pairwise=CCMP
auth_algs=1
macaddr_acl=0
`, cfg.Interface, cfg.SSID, hwMode, cfg.Channel, cfg.Password)

	return os.WriteFile(path, []byte(content), 0600)
}

type DHCPConfig struct {
	Interface  string
	Gateway    string
	RangeStart string
	RangeEnd   string
	DNS        []string
	Blocked    []string // Domains to sinkhole
}

func GenerateDnsmasqConfig(cfg DHCPConfig, path string) error {
	content := fmt.Sprintf(`interface=%s
bind-interfaces
dhcp-range=%s,%s,12h
dhcp-option=option:router,%s
`, cfg.Interface, cfg.RangeStart, cfg.RangeEnd, cfg.Gateway)

	for _, dns := range cfg.DNS {
		content += fmt.Sprintf("dhcp-option=option:dns-server,%s\n", dns)
	}

	// Force DNS - make dnsmasq the only DNS server for clients
	content += "port=53\n"
	content += "domain-needed\n"
	content += "bogus-priv\n"

	// Sinkhole blocked domains
	for _, domain := range cfg.Blocked {
		content += fmt.Sprintf("address=/%s/127.0.0.1\n", domain)
	}

	return os.WriteFile(path, []byte(content), 0600)
}
