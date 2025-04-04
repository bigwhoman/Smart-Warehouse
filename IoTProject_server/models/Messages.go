package models

type MessageBody struct {
	Response string `json:"response"`
}

type IsRented struct {
	Response bool `json:"response"`
}

type SendTemprature struct {
	BoxCode     string  `json:"code"`
	Temperature float32 `json:"temperature"`
}
