package models

import (
	"crypto/rand"
	"encoding/hex"
	"time"
)

const SessionLength int = 5 * 60 * 6

var DBSessions = map[string]Session{}

type Session struct {
	Un           string
	LastActivity time.Time
}

func GenerateSessionID() string {
	bytes := make([]byte, 64) // 16 bytes = 128 bits
	_, err := rand.Read(bytes)
	if err != nil {
		panic(err)
	}
	return hex.EncodeToString(bytes)
}
