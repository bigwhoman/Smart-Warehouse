package models

import (
	"database/sql"
	"time"
)

type Box struct {
	Id      int            `json:"id"`
	BoxCode string         `json:"boxcode"`
	Owner   string         `json:"owner"`
	Renter  sql.NullString `json:"renter"`
}

type RentRequestBox struct {
	BoxCode string `json:"code"`
	Time    time.Time
}

var RentRequests = map[string]RentRequestBox{}
