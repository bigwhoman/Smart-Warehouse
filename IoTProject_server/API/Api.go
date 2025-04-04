package API

import (
	"IoTProject_server/models"
	"IoTProject_server/util"
	"encoding/json"
	"fmt"
	mqtt "github.com/eclipse/paho.mqtt.golang"
	"golang.org/x/crypto/bcrypt"
	"log"
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
	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
		return
	}

	var user_input models.SendTemprature
	err := json.NewDecoder(r.Body).Decode(&user_input)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	fmt.Println(user_input.BoxCode)
	fmt.Println(user_input.Temperature)
	time_now := time.Now().Format("2006-01-02 15:04:05")
	temp := models.Temprature{}
	temp.Boxcode = user_input.BoxCode
	temp.Temperature = user_input.Temperature
	temp.Time = time_now
	err = util.InsertTempretureIntodb(util.DataBase, temp)
	if err != nil {
		fmt.Println(err)
	}
	w.WriteHeader(http.StatusOK)
	fmt.Println("Login successful")
}

func IsRented(w http.ResponseWriter, r *http.Request) {
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
		var response models.IsRented
		response.Response = true
		json.NewEncoder(w).Encode(response)
		//http.Error(w, "Box already rented!", http.StatusOK)
		return
	} else {
		var response models.IsRented
		response.Response = false
		json.NewEncoder(w).Encode(response)
		//http.Error(w, "Box already rented!", http.StatusOK)
		return
	}

}

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
		var response models.MessageBody
		response.Response = "Rented"
		json.NewEncoder(w).Encode(response)
		http.Error(w, "Box already rented!", http.StatusUnauthorized)
		return
	}

	QrCode, headerContent, err := util.GenerateQRhexCode()
	fmt.Println("QR code is:")
	fmt.Println(QrCode)
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

func SendingQR(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusMethodNotAllowed)
		return
	}
	var sendBackQR models.SendBackQR
	err := json.NewDecoder(r.Body).Decode(&sendBackQR)

	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
	}

	request, ok := models.RentRequests[sendBackQR.Code]
	if ok {
		currentTime := time.Now()
		if currentTime.Sub(request.Time) < time.Second*60 {
			cookie, err := r.Cookie("session")
			if err != nil {
				fmt.Println(err.Error())
				http.Error(w, "Internal error", http.StatusInternalServerError)
				return
			}

			currentUser := models.DBSessions[cookie.Value].Un
			err = util.RentBox(util.DataBase, currentUser, request.BoxCode)
			if err != nil {
				fmt.Println(err.Error())
				http.Error(w, "Internal error", http.StatusInternalServerError)
				return
			}
			fmt.Println(currentUser + " rented box " + request.BoxCode + " Successfuly!")
			w.WriteHeader(http.StatusOK)
			// MQTT broker (replace with your Pi's IP)
			broker := "tcp://10.118.231.196:1883"
			topic := "notifyRent"
			message := currentUser + " rented " + request.BoxCode
			opts := mqtt.NewClientOptions()
			opts.AddBroker(broker)
			opts.SetClientID("go-client-" + fmt.Sprint(time.Now().Unix()))
			opts.SetConnectTimeout(5 * time.Second)

			client := mqtt.NewClient(opts)

			// Connect to broker
			if token := client.Connect(); token.Wait() && token.Error() != nil {
				log.Fatal("❌ Connection error:", token.Error())
			}
			fmt.Println("✅ Connected to MQTT broker")

			// Publish the message
			token := client.Publish(topic, 0, false, message)
			token.Wait()
			fmt.Println("📤 Message published:", message)

			client.Disconnect(250)
		} else {
			delete(models.RentRequests, sendBackQR.Code)
			http.Error(w, "Invalid code", http.StatusBadRequest)
		}
	} else {
		http.Error(w, "Invalid code", http.StatusBadRequest)
	}

}
