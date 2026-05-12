package network

import (
	"bytes"
	"fmt"
	"os/exec"
)

type Runner interface {
	Execute(name string, args ...string) ([]byte, error)
}

type SudoRunner struct{}

func (r *SudoRunner) Execute(name string, args ...string) ([]byte, error) {
	cmdArgs := append([]string{name}, args...)
	cmd := exec.Command("sudo", cmdArgs...)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return nil, fmt.Errorf("command failed: %w, stderr: %s", err, stderr.String())
	}

	return stdout.Bytes(), nil
}
