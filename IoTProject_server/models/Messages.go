package models

type MessageBody struct {
	Response string `json:"response"`
}

type IsRented struct {
	Response bool `json:"response"`
}
