package util

import (
	"database/sql"
	"fmt"
	_ "github.com/go-sql-driver/mysql"
)

var db_user = "root"
var db_password = "Km_12Seb_12drt_43_ets_gg12"

var DataBase *sql.DB

func Initializedatabase() {
	dsn := fmt.Sprintf("%s:%s@tcp(127.0.0.1:3306)/iot_project", db_user, db_password)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		fmt.Println("sql.Open error:", err.Error())
	}

	// ACTUAL CONNECTION TEST
	if err := db.Ping(); err != nil {
		fmt.Println("db.Ping error:", err.Error())
	}

	fmt.Println("Database connected successfully.")
	DataBase = db
}
