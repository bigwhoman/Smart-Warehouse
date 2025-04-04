package util

import (
	"IoTProject_server/models"
	"database/sql"
	"errors"
	"fmt"
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

func GetBoxFromdbByBoxcode(db *sql.DB, boxcode string) (models.Box, bool, error) {
	var box models.Box
	query := "SELECT * FROM boxes WHERE boxcode=" + "\"" + boxcode + "\""
	results, err := db.Query(query)
	if err != nil {
		return box, false, err
	}
	count := 0
	for results.Next() {
		count++
		err = results.Scan(&box.Id, &box.BoxCode, &box.Owner, &box.Renter)
		if err != nil {
			return box, false, err
		}
	}
	if count == 0 {
		return box, false, nil
	} else {
		return box, true, nil
	}
}

func IsBoxRented(db *sql.DB, boxcode string) (bool, error) {
	var box models.Box
	query := "SELECT * FROM boxes WHERE boxcode=" + "\"" + boxcode + "\""
	results, err := db.Query(query)
	if err != nil {
		return false, err
	}
	count := 0
	for results.Next() {
		count++
		err = results.Scan(&box.Id, &box.BoxCode, &box.Owner, &box.Renter)
		if err != nil {
			return false, err
		}
	}
	if count == 0 {
		return false, errors.New("Box is not available")
	} else {
		if !box.Renter.Valid {
			return false, nil
		} else {
			return true, nil
		}
	}
}

func InsertTempretureIntodb(db *sql.DB, temp models.Temprature) error {
	query := "INSERT INTO tempratures VALUES (" + "NULL" + "," + "\"" + temp.Time + "\"" + "," + "\"" + fmt.Sprintf("%f", 123.456) + "\"" + "," + "\"" + string(temp.Boxcode) + "\"" + ")"
	insert, err := db.Query(query)
	if err != nil {
		return err
	}
	defer insert.Close()
	return nil
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

func RentBox(db *sql.DB, renter string, boxcode string) error {
	query := "UPDATE boxes SET renter = " + "\"" + renter + "\"" + " WHERE boxcode=" + "\"" + boxcode + "\""
	_, err := db.Query(query)
	if err != nil {

		return err
	}
	return nil
}
