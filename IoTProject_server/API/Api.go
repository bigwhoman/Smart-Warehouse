package API

import (
	"IoTProject_server/models"
	"IoTProject_server/util"
	"encoding/json"
	"fmt"
	"golang.org/x/crypto/bcrypt"
	"net/http"
	"time"
)

func alreadyLoggedIn(w http.ResponseWriter, req *http.Request) bool {
	cookie, err := req.Cookie("session")
	if err != nil {
		return false
	}
	session, ok := models.DBSessions[cookie.Value]
	if ok {
		session.LastActivity = time.Now()
		models.DBSessions[cookie.Value] = session
	}

	agent, ok, err := util.GetUserFromdbByUsername(util.DataBase, session.Un)
	if err != nil {
		fmt.Println(err)
		return false
	}
	// refresh session
	cookie.MaxAge = models.SessionLength
	http.SetCookie(w, cookie)
	return ok && ("" != agent.UserName)
}

func Signup(w http.ResponseWriter, r *http.Request) {
	if alreadyLoggedIn(w, r) {
		w.WriteHeader(http.StatusSeeOther)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
		return
	}

	var user_input models.User
	err := json.NewDecoder(r.Body).Decode(&user_input)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// username taken?
	user, ok, err := util.GetUserFromdbByUsername(util.DataBase, user_input.UserName)
	if ok && (user.UserName != "") {
		http.Error(w, "Username already taken", http.StatusForbidden)
		return
	}

	err = util.InsertNewUserIntodb(util.DataBase, user_input)
	if err != nil {
		fmt.Println(err.Error())
		http.Error(w, "Internal error", http.StatusInternalServerError)
		return
	}
	// create session
	sID := models.GenerateSessionID()
	cookie := &http.Cookie{
		Name:  "session",
		Value: sID,
	}
	cookie.MaxAge = models.SessionLength
	http.SetCookie(w, cookie)
	models.DBSessions[cookie.Value] = models.Session{user_input.UserName, time.Now()}
	w.WriteHeader(http.StatusOK)
	fmt.Println("Signup successful")
}

func Login(w http.ResponseWriter, r *http.Request) {

	if alreadyLoggedIn(w, r) {
		fmt.Println("Login: Already logged in")
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
		return
	}

	var user_input models.User
	err := json.NewDecoder(r.Body).Decode(&user_input)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	user, ok, err := util.GetUserFromdbByUsername(util.DataBase, user_input.UserName)
	if !ok && user.UserName == "" {
		http.Error(w, "Username and/or password do not match", http.StatusForbidden)
		return
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(user_input.Password))
	if err != nil {
		http.Error(w, "Username and/or password do not match", http.StatusForbidden)
		return
	}

	sID := models.GenerateSessionID()
	cookie := &http.Cookie{
		Name:  "session",
		Value: sID,
	}
	cookie.MaxAge = models.SessionLength
	http.SetCookie(w, cookie)
	models.DBSessions[cookie.Value] = models.Session{user_input.UserName, time.Now()}
	w.WriteHeader(http.StatusOK)
	fmt.Println("Login successful")
}

func SendTemperature(w http.ResponseWriter, r *http.Request) {

}

//func GetQRImage(w http.ResponseWriter, r *http.Request) {
//	if r.Method != http.MethodGet {
//		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
//		return
//	}
//	code, headerContent, err := util.GenerateQRhexCode()
//	fmt.Println(code)
//	if err != nil {
//		fmt.Println("Error generating QR image")
//		http.Error(w, "Internal error", http.StatusInternalServerError)
//		return
//	}
//	w.Header().Set("Content-Type", "application/octet-stream")
//	w.Header().Set("Content-Disposition", `attachment; filename="qr.h"`)
//	w.Write([]byte(headerContent))
//}

func RentBoxRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
		return
	}
	var boxRequest models.RentRequestBox

	err := json.NewDecoder(r.Body).Decode(&boxRequest)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	rentStatus, err := util.IsBoxRented(util.DataBase, boxRequest.BoxCode)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if rentStatus {
		http.Error(w, "Box already rented!", http.StatusUnauthorized)
		return
	}

	QrCode, headerContent, err := util.GenerateQRhexCode()

	if err != nil {
		fmt.Println("Error generating QR image")
		http.Error(w, "Internal error", http.StatusInternalServerError)
		return
	}

	models.RentRequests[QrCode] = models.RentRequestBox{BoxCode: boxRequest.BoxCode, Time: time.Now()}
	
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", `attachment; filename="qr.h"`)
	w.Write([]byte(headerContent))
}
