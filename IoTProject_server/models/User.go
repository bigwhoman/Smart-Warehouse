package models

type User struct {
	UserId   int    `json:"id"`
	UserName string `json:"username"`
	Password string `json:"password"`
	Type     string `json:"type"`
}
