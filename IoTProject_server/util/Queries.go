package util

import (
	"IoTProject_server/models"
	"database/sql"
	"golang.org/x/crypto/bcrypt"
)

func GetUserFromdbByUsername(db *sql.DB, username string) (models.User, bool, error) {
	var user models.User
	query := "SELECT * FROM users WHERE username=" + "\"" + username + "\""
	results, err := db.Query(query)
	if err != nil {
		return user, false, err
	}
	count := 0
	for results.Next() {
		count++
		err = results.Scan(&user.UserId, &user.UserName, &user.Password, &user.Type)
		if err != nil {
			return user, false, err
		}
	}
	if count == 0 {
		return user, false, nil
	} else {
		return user, true, nil
	}

}

func InsertNewUserIntodb(db *sql.DB, user models.User) error {
	encryptedPassword, _ := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.MinCost)
	query := "INSERT INTO users VALUES (" + "NULL" + "," + "\"" + string(user.UserName) + "\"" + "," + "\"" + string(encryptedPassword) + "\"" + "," + "\"" + string(user.Type) + "\"" + ")"
	insert, err := db.Query(query)
	if err != nil {
		return err
	}
	defer insert.Close()
	return nil
}
