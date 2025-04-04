package models

type Temprature struct {
	Time        string  `json:"time"`
	Temperature float32 `json:"temperature"`
	Boxcode     string  `json:"boxcode"`
}
