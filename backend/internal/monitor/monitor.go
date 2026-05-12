package monitor

import (
	"bufio"
	"os"
	"strings"
	"time"
)

type Device struct {
	IP        string
	MAC       string
	Hostname  string
	Connected bool
	LastSeen  time.Time
	BytesUp   int64
	BytesDown int64
}

func GetConnectedDevices() ([]Device, error) {
	file, err := os.Open("/proc/net/arp")
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var devices []Device
	scanner := bufio.NewScanner(file)
	scanner.Scan() // skip header

	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 4 {
			continue
		}

		ip := fields[0]
		mac := fields[3]
		
		if mac == "00:00:00:00:00:00" {
			continue
		}

		devices = append(devices, Device{
			IP:        ip,
			MAC:       mac,
			Connected: true,
			LastSeen:  time.Now(),
		})
	}

	return devices, scanner.Err()
}
